"""系统备份/恢复路由 - V5-d
提供数据库 zip 打包备份、zip 恢复、备份列表功能
"""
import os
import io
import zipfile
import shutil
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from database import DB_PATH, DATA_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/system', tags=['系统备份'])

# 备份存储目录
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)


@router.get('/backup')
def system_backup():
    """将整个 SQLite 数据库打包为 zip 下载
    zip 内包含：数据库文件 + 备份时间戳 README.txt
    """
    if not DB_PATH or not os.path.exists(DB_PATH):
        raise HTTPException(500, '数据库文件不存在，无法备份')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_filename = os.path.basename(DB_PATH)
    zip_filename = f'backup_{timestamp}.zip'

    # 在内存中构建 zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 写入数据库文件
        zf.write(DB_PATH, db_filename)
        # 写入 README.txt（含备份时间戳）
        readme_content = (
            f"辅导员工作平台 - 数据库备份\n"
            f"备份时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"数据库文件：{db_filename}\n"
            f"备份文件：{zip_filename}\n"
        )
        zf.writestr('README.txt', readme_content)

    buf.seek(0)

    # 同时在 backups/ 目录保存一份
    backup_path = os.path.join(BACKUP_DIR, zip_filename)
    with open(backup_path, 'wb') as f:
        f.write(buf.getvalue())
    logger.info(f"[备份] 已保存到: {backup_path}")

    return StreamingResponse(
        buf,
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename={zip_filename}'}
    )


@router.post('/restore')
async def system_restore(file: UploadFile = File(...)):
    """上传 zip 文件恢复数据库
    - 解压 zip 提取 .db 文件
    - 替换前先自动备份当前数据库（存为 data/backup_before_restore.db）
    - 返回成功/失败
    """
    if not DB_PATH:
        raise HTTPException(500, '数据库路径未识别')

    # 校验文件类型
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(400, '仅支持 .zip 文件（需包含 .db 数据库文件）')

    content = await file.read()
    if len(content) < 100:
        raise HTTPException(400, '文件过小，疑似损坏')

    try:
        buf = io.BytesIO(content)
        with zipfile.ZipFile(buf, 'r') as zf:
            # 在 zip 中查找 .db 文件
            db_files = [n for n in zf.namelist() if n.endswith('.db') or n.endswith('.sqlite')]
            if not db_files:
                raise HTTPException(400, 'zip 中未找到 .db / .sqlite 数据库文件')

            db_file_name = db_files[0]
            db_data = zf.read(db_file_name)

        if len(db_data) < 100:
            raise HTTPException(400, '数据库文件过小，疑似损坏')

        # 替换前先自动备份当前数据库
        if os.path.exists(DB_PATH):
            backup_path = os.path.join(DATA_DIR, 'backup_before_restore.db')
            shutil.copy2(DB_PATH, backup_path)
            logger.info(f"[恢复] 已备份当前数据库到: {backup_path}")

        # 写入新数据库文件
        with open(DB_PATH, 'wb') as f:
            f.write(db_data)

        logger.info(f"[恢复] 已从 {file.filename} 恢复数据库，大小: {len(db_data)} 字节")
        return {
            'ok': True,
            'restored_bytes': len(db_data),
            'source_file': file.filename,
            'db_file': db_file_name,
            'note': '数据库已恢复，需重启后端生效（当前进程内 engine 缓存已失效）'
        }

    except zipfile.BadZipFile:
        raise HTTPException(400, '无效的 zip 文件')
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('[恢复] 恢复失败')
        raise HTTPException(500, f'恢复失败: {type(e).__name__}: {str(e)}')


@router.get('/backups')
def list_backups():
    """列出 data/backups/ 目录下的所有备份文件（按时间倒序）
    返回 [{name, size, created_at}]
    """
    if not os.path.isdir(BACKUP_DIR):
        return []

    backups = []
    for fname in os.listdir(BACKUP_DIR):
        fpath = os.path.join(BACKUP_DIR, fname)
        if os.path.isfile(fpath):
            stat = os.stat(fpath)
            backups.append({
                'name': fname,
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            })

    # 按创建时间倒序排列
    backups.sort(key=lambda x: x['created_at'], reverse=True)
    return backups

@router.get('/backups/download')
def download_backup(file: str):
    """下载指定的备份文件"""
    if not file or '..' in file or '/' in file:
        raise HTTPException(400, '无效的文件名')
    fpath = os.path.join(BACKUP_DIR, file)
    if not os.path.isfile(fpath):
        raise HTTPException(404, f'备份文件不存在: {file}')
    return StreamingResponse(
        open(fpath, 'rb'),
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename={file}'}
    )
