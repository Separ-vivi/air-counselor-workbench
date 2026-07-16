"""系统设置 · 数据管理路由"""
import os
import io
import shutil
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, engine, Base, SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/system', tags=['系统管理'])

# 数据库文件路径（sqlite 单文件）
DB_PATH = None
try:
    url = str(engine.url)
    # sqlite:///air_workbench.db  或  sqlite:////abs/path
    if url.startswith('sqlite:///'):
        rel = url.replace('sqlite:///', '', 1)
        # 相对路径按 backend/ 解析
        if not os.path.isabs(rel):
            DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), rel)
        else:
            DB_PATH = rel
except Exception:
    pass


@router.get('/health')
def system_health(db: Session = Depends(get_db)):
    """数据库健康检查：schema 是否对齐 + 各表行数"""
    from schema_migrations import get_schema_health
    from sqlalchemy import text as sql_text
    report = get_schema_health(engine, Base)
    # 补每表行数
    for t in report['tables']:
        try:
            r = db.execute(sql_text(f'SELECT COUNT(*) FROM "{t["table"]}"')).scalar()
            t['row_count'] = int(r or 0)
        except Exception:
            t['row_count'] = -1
    # 关键表快照
    from models import Student, ClassModel, Major, GradeRecord
    report['summary'] = {
        'student_count': db.query(Student).count(),
        'class_count': db.query(ClassModel).count(),
        'major_count': db.query(Major).count(),
        'grade_count': db.query(GradeRecord).count(),
    }
    return report


@router.post('/reinit')
def system_reinit(seed_size: str = 'large'):
    """
    危险操作：drop 全部表 + 重建 + 灌 seed。
    seed_size: small=原示例种子, large=生成 300+ 学生全域数据
    """
    from schema_migrations import hard_reset
    logger.warning(f"[system] 执行 reinit, seed_size={seed_size}")
    hard_reset(engine, Base)
    if seed_size == 'large':
        from seed_large import seed_large_dataset
        stats = seed_large_dataset()
    else:
        from seed_data import seed_if_empty
        seed_if_empty()
        stats = {'mode': 'small', 'note': '原示例种子已灌入'}
    return {'ok': True, 'reinit': True, 'seed_size': seed_size, 'stats': stats}


@router.post('/seed-large')
def seed_large_endpoint():
    """在已有数据库上追加大 seed（不 drop）"""
    from seed_large import seed_large_dataset
    stats = seed_large_dataset()
    return {'ok': True, 'stats': stats}


@router.get('/backup')
def system_backup():
    """下载完整 sqlite 数据库文件"""
    if not DB_PATH or not os.path.exists(DB_PATH):
        raise HTTPException(500, 'DB 文件不存在，无法备份')
    filename = f"air_workbench_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    return FileResponse(DB_PATH, filename=filename, media_type='application/octet-stream')


@router.post('/restore')
async def system_restore(file: UploadFile = File(...)):
    """上传 sqlite 文件覆盖现有数据库"""
    if not DB_PATH:
        raise HTTPException(500, 'DB 路径未识别')
    if not file.filename.endswith('.db') and not file.filename.endswith('.sqlite'):
        raise HTTPException(400, '仅支持 .db / .sqlite 文件')
    content = await file.read()
    if len(content) < 100:
        raise HTTPException(400, '文件过小，疑似损坏')
    # 备份当前
    if os.path.exists(DB_PATH):
        backup_path = DB_PATH + f'.bak_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        shutil.copy2(DB_PATH, backup_path)
        logger.info(f"[system] 覆盖前已备份到: {backup_path}")
    # 写入新文件
    with open(DB_PATH, 'wb') as f:
        f.write(content)
    return {'ok': True, 'restored_bytes': len(content), 'note': '需重启后端生效（当前进程内 engine 缓存已失效）'}


@router.delete('/clear-business')
def clear_business_data():
    """清空业务数据（保留 组织架构/系统配置/知识库）"""
    from models import (
        Student, GradeRecord, WarningRecord, PartyProgress, PsychologyRecord,
        FamilyContact, StudentCadreRecord, ClassTeacher, EmploymentRecord,
        Activity, ActivitySignup, PartyStudy, ClassMeeting, WeeklySummary,
        GeneratedDocument, Tag,
        StudentHardship, StudentGrant, StudentScholarship, StudentLoan,
        StudentWorkStudy, StudentHonor, StudentDormVisit, StudentLeave,
        StudentDiscipline, StudentDormChat, StudentAttendanceException,
        StudentStatusChange, Project, ProjectStudent,
    )
    from sqlalchemy import text as sql_text
    deleted = {}
    errors = []
    # 关联表先删（无 model 类）
    db = SessionLocal()
    try:
        db.execute(sql_text('DELETE FROM student_tags'))
        db.commit()
    except Exception as e:
        errors.append(f'student_tags: {e}')
        db.rollback()
    db.close()

    # 按依赖顺序删（子表→Student→组织表）
    clear_order = [
        GeneratedDocument, ActivitySignup, ProjectStudent, Project,
        StudentHardship, StudentGrant, StudentScholarship, StudentLoan,
        StudentWorkStudy, StudentHonor, StudentDormVisit, StudentLeave,
        StudentDiscipline, StudentDormChat, StudentAttendanceException,
        StudentStatusChange,
        PartyProgress, PsychologyRecord, FamilyContact,
        StudentCadreRecord, EmploymentRecord, WarningRecord, GradeRecord,
        Activity, PartyStudy, ClassMeeting, WeeklySummary,
        ClassTeacher, Student, Tag,
    ]
    for m in clear_order:
        db = SessionLocal()
        try:
            n = db.query(m).delete(synchronize_session=False)
            db.commit()
            deleted[m.__name__] = n
        except Exception as e:
            errors.append(f'{m.__name__}: {e}')
            db.rollback()
        finally:
            db.close()

    return {
        'ok': True,
        'deleted': deleted,
        'errors': errors,
        'note': '业务数据已清空（保留 年级/专业/班级/设置/知识库/FAQ/模板）'
    }
