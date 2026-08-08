"""文档工具箱路由 - 分类文档管理 + AI辅助（基于完整文档，不切片）

分类：policy(政策文件) / form(常用表格) / student_collect(学生端收集) / other(其他文档)
存储：保留原始PDF/Word/Excel文件，不做碎片化切片
索引：提取文档全文作为单一索引单元
AI：基于完整文档回答问题，引用具体章节/页码
"""
import os
import json
import logging
import tempfile
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import DocumentFile
from services.llm_adapter import LLMAdapter
from services.file_parser import parse as parse_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api')

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'docbox')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 分类定义
CATEGORIES = {
    'policy': '政策文件',
    'form': '常用表格',
    'student_collect': '学生端收集',
    'other': '其他文档',
}

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt', '.csv'}


def _format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _get_page_count(file_path: str, ext: str) -> int:
    """获取PDF页数"""
    if ext == '.pdf':
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0
    return 0


def _extract_text(file_path: str) -> str:
    """提取文件全文（复用已有的file_parser）"""
    try:
        return parse_file(file_path)
    except Exception as e:
        logger.warning(f"提取文本失败: {e}")
        return ''


# ===== 文档列表（按分类） =====

@router.get('/docbox/list')
def list_documents(
    category: str = Query('', description='按分类筛选'),
    search: str = Query('', description='搜索关键词'),
    db: Session = Depends(get_db)
):
    """返回文档列表，可按分类筛选和搜索"""
    query = db.query(DocumentFile)
    
    if category and category in CATEGORIES:
        query = query.filter(DocumentFile.category == category)
    
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            (DocumentFile.title.like(search_pattern)) |
            (DocumentFile.description.like(search_pattern))
        )
    
    items = query.order_by(DocumentFile.created_at.desc()).all()
    
    # 按分类分组
    grouped = {}
    for cat_key, cat_name in CATEGORIES.items():
        cat_items = [i for i in items if i.category == cat_key]
        grouped[cat_key] = {
            'name': cat_name,
            'count': len(cat_items),
            'items': [{
                'id': d.id,
                'title': d.title,
                'category': d.category,
                'description': d.description or '',
                'doc_type': d.doc_type,
                'file_size': d.file_size,
                'file_size_str': _format_file_size(d.file_size),
                'page_count': d.page_count,
                'link_url': d.link_url or '',
                'created_at': str(d.created_at)[:16] if d.created_at else '',
                'updated_at': str(d.updated_at)[:16] if d.updated_at else '',
            } for d in cat_items]
        }
    
    return {
        'categories': grouped,
        'total': len(items),
    }


# ===== 上传文档 =====

@router.post('/docbox/upload')
async def upload_document(
    file: UploadFile = File(...),
    category: str = 'other',
    description: str = '',
    db: Session = Depends(get_db)
):
    """上传文档到文档工具箱 - 保留完整文件，提取全文作为索引"""
    if not file.filename:
        raise HTTPException(400, '文件名不能为空')
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f'不支持的文件类型: {ext}，支持 {", ".join(ALLOWED_EXTENSIONS)}')
    
    if category not in CATEGORIES:
        category = 'other'
    
    # 保存文件
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    safe_name = f"{timestamp}_{file.filename}"
    # 按分类建子目录
    cat_dir = os.path.join(UPLOAD_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)
    file_path = os.path.join(cat_dir, safe_name)
    # V6.18: 使用相对路径存储，确保跨机器可移植
    rel_file_path = os.path.relpath(file_path, os.path.dirname(os.path.dirname(__file__)))
    
    content_bytes = await file.read()
    file_size = len(content_bytes)
    
    with open(file_path, 'wb') as f:
        f.write(content_bytes)
    
    try:
        # 提取全文（不做切片，保留完整文本）
        full_text = _extract_text(file_path)
        
        # 获取PDF页数
        page_count = _get_page_count(file_path, ext)
        
        # 创建文档记录
        doc = DocumentFile(
            title=file.filename,
            category=category,
            description=description,
            doc_type=ext.lstrip('.'),
            file_path=rel_file_path,
            file_size=file_size,
            page_count=page_count,
            full_text=full_text,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # 更新FTS索引
        _rebuild_docbox_fts(db)
        
        return {
            'id': doc.id,
            'title': doc.title,
            'category': doc.category,
            'doc_type': doc.doc_type,
            'file_size': file_size,
            'page_count': page_count,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"上传处理失败: {e}")
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise HTTPException(500, f'文件处理失败: {str(e)}')


# ===== 添加链接类文档（学生端收集） =====

@router.post('/docbox/link')
def add_link_document(data: dict, db: Session = Depends(get_db)):
    """添加链接类文档（如学生端收集的表单链接）"""
    title = data.get('title', '').strip()
    link_url = data.get('link_url', '').strip()
    category = data.get('category', 'student_collect')
    description = data.get('description', '')
    
    if not title:
        raise HTTPException(400, '标题不能为空')
    if not link_url:
        raise HTTPException(400, '链接不能为空')
    if category not in CATEGORIES:
        category = 'student_collect'
    
    doc = DocumentFile(
        title=title,
        category=category,
        description=description,
        doc_type='link',
        link_url=link_url,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    return {'id': doc.id, 'title': doc.title}


# ===== 获取文档详情 =====

@router.get('/docbox/{doc_id}')
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """获取文档详情（含全文）"""
    doc = db.query(DocumentFile).get(doc_id)
    if not doc:
        raise HTTPException(404, '文档不存在')
    
    return {
        'id': doc.id,
        'title': doc.title,
        'category': doc.category,
        'category_name': CATEGORIES.get(doc.category, '其他'),
        'description': doc.description or '',
        'doc_type': doc.doc_type,
        'file_path': doc.file_path,
        'file_size': doc.file_size,
        'file_size_str': _format_file_size(doc.file_size),
        'page_count': doc.page_count,
        'link_url': doc.link_url or '',
        'full_text': doc.full_text or '',
        'created_at': str(doc.created_at) if doc.created_at else '',
        'updated_at': str(doc.updated_at) if doc.updated_at else '',
    }


# ===== 文档预览/下载 =====

@router.get('/docbox/{doc_id}/preview')
def preview_document(doc_id: int, db: Session = Depends(get_db)):
    """下载/预览文档原始文件"""
    doc = db.query(DocumentFile).get(doc_id)
    if not doc:
        raise HTTPException(404, '文档不存在')
    
    if doc.doc_type == 'link':
        raise HTTPException(400, '链接类文档无文件可预览')
    
    # V6.18: 支持相对路径解析
    file_path = doc.file_path
    if file_path and not os.path.isabs(file_path):
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_path)
    if not file_path or not os.path.isfile(file_path):
        raise HTTPException(404, '文件不存在或已被删除')
    
    # 根据文件类型设置MIME
    mime_map = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.txt': 'text/plain; charset=utf-8',
        '.csv': 'text/csv; charset=utf-8',
    }
    ext = os.path.splitext(doc.file_path)[1].lower()
    media_type = mime_map.get(ext, 'application/octet-stream')
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=doc.title,
    )


# ===== 更新文档分类/描述 =====

@router.put('/docbox/{doc_id}')
def update_document(doc_id: int, data: dict, db: Session = Depends(get_db)):
    """更新文档信息（分类、描述等）"""
    doc = db.query(DocumentFile).get(doc_id)
    if not doc:
        raise HTTPException(404, '文档不存在')
    
    if 'category' in data and data['category'] in CATEGORIES:
        doc.category = data['category']
    if 'title' in data:
        doc.title = data['title']
    if 'description' in data:
        doc.description = data['description']
    if 'link_url' in data:
        doc.link_url = data['link_url']
    
    doc.updated_at = datetime.now()
    db.commit()
    
    return {'ok': True}


# ===== 删除文档 =====

@router.delete('/docbox/{doc_id}')
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """V6.17: 删除文档及关联文件（增强容错）"""
    doc = db.query(DocumentFile).get(doc_id)
    if not doc:
        # V6.17: 即使记录不存在也返回成功（幂等删除）
        return {'ok': True, 'message': '文档不存在或已被删除'}
    
    title = doc.title
    
    # 删除文件（多个可能的路径）
    if doc.file_path:
        try:
            fp = doc.file_path
            if not os.path.isabs(fp):
                fp = os.path.join(os.path.dirname(os.path.dirname(__file__)), fp)
            if os.path.isfile(fp):
                os.remove(fp)
                logger.info(f"已删除文件: {doc.file_path}")
        except Exception as e:
            logger.warning(f"删除文件失败: {e}")
    
    # 删除数据库记录
    try:
        db.delete(doc)
        db.commit()
    except Exception as e:
        logger.error(f"删除数据库记录失败: {e}")
        db.rollback()
        # 重试一次
        try:
            doc = db.query(DocumentFile).get(doc_id)
            if doc:
                db.delete(doc)
                db.commit()
        except Exception as e2:
            logger.error(f"重试删除仍失败: {e2}")
            db.rollback()
            raise HTTPException(500, f'删除失败: {str(e2)}')
    
    # 重建FTS索引（忽略失败）
    try:
        _rebuild_docbox_fts(db)
    except Exception as e:
        logger.warning(f"FTS索引重建失败: {e}")
    
    return {'ok': True, 'message': f'「{title}」已删除'}


# ===== V6.17: 清理脏数据 =====

@router.post('/docbox/cleanup')
def cleanup_orphaned_docs(db: Session = Depends(get_db)):
    """V6.17: 清理上传失败但遗留的脏数据（文件不存在或full_text为空的记录）"""
    docs = db.query(DocumentFile).all()
    cleaned = 0
    
    for doc in docs:
        should_delete = False
        
        # 检查1: 非链接类但文件不存在
        if doc.doc_type != 'link' and doc.file_path and not os.path.isfile(doc.file_path):
            should_delete = True
        
        # 检查2: 文件大小为0且没有全文
        if doc.file_size == 0 and not doc.full_text and doc.doc_type != 'link':
            should_delete = True
        
        if should_delete:
            logger.info(f"清理脏数据: id={doc.id}, title={doc.title}")
            db.delete(doc)
            cleaned += 1
    
    if cleaned > 0:
        db.commit()
        try:
            _rebuild_docbox_fts(db)
        except Exception:
            pass
    
    return {'cleaned': cleaned}


# ===== FTS5 索引管理 =====

def _ensure_docbox_fts(db: Session):
    """确保文档工具箱FTS5虚拟表存在（V6.16-hotfix: 修复外部内容表列名不匹配）"""
    # 检查现有表是否使用了错误的外部内容表配置（V6.15的bug）
    try:
        # 尝试DELETE来检测表是否损坏
        db.execute(text("DELETE FROM docbox_fts WHERE rowid = -1"))
    except Exception:
        # 表损坏或不存在，先删除旧的有问题的表再重建
        try:
            db.execute(text("DROP TABLE IF EXISTS docbox_fts"))
        except Exception:
            pass
    
    db.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS docbox_fts USING fts5(
            title,
            content,
            description
        )
    """))
    db.commit()


def _rebuild_docbox_fts(db: Session):
    """重建文档工具箱FTS5索引"""
    _ensure_docbox_fts(db)
    db.execute(text("DELETE FROM docbox_fts"))
    
    docs = db.query(DocumentFile).all()
    for d in docs:
        # 使用2-gram分词
        from services.retriever import _bigram_tokenize
        title_bigram = _bigram_tokenize(d.title or '')
        content_bigram = _bigram_tokenize(d.full_text or '')
        desc_bigram = _bigram_tokenize(d.description or '')
        
        db.execute(text("""
            INSERT INTO docbox_fts(rowid, title, content, description)
            VALUES(:id, :title, :content, :desc)
        """), {
            'id': d.id,
            'title': title_bigram,
            'content': content_bigram,
            'desc': desc_bigram,
        })
    db.commit()
    logger.info(f"文档工具箱FTS5索引重建完成，共 {len(docs)} 条")


# ===== AI 问答（基于完整文档） =====

@router.post('/docbox/chat')
def docbox_chat(data: dict, db: Session = Depends(get_db)):
    """基于完整文档的AI问答 - 引用具体章节/页码"""
    question = data.get('question', '').strip()
    if not question:
        raise HTTPException(400, '问题不能为空')
    
    _ensure_docbox_fts(db)
    
    # FTS5搜索
    from services.retriever import _bigram_tokenize, _build_fts_query
    fts_query = _build_fts_query(question)
    
    matched_docs = []
    if fts_query.strip():
        try:
            results = db.execute(text("""
                SELECT fts.rowid as id, fts.rank
                FROM docbox_fts fts
                WHERE docbox_fts MATCH :q
                ORDER BY fts.rank
                LIMIT 5
            """), {'q': fts_query}).fetchall()
            
            for r in results:
                doc = db.query(DocumentFile).get(r.id)
                if doc:
                    matched_docs.append(doc)
        except Exception as e:
            logger.warning(f"FTS5搜索失败: {e}")
    
    # 如果FTS5没结果，尝试LIKE兜底
    if not matched_docs:
        like_pattern = f'%{question[:20]}%'
        fallback = db.query(DocumentFile).filter(
            (DocumentFile.title.like(like_pattern)) |
            (DocumentFile.full_text.like(like_pattern))
        ).limit(5).all()
        matched_docs = list(fallback)
    
    if not matched_docs:
        return {
            'answer': '文档工具箱中暂无相关文档，请先上传文档后再提问。',
            'sources': [],
        }
    
    # 构造上下文（基于完整文档）
    context_parts = []
    sources_info = []
    
    for doc in matched_docs[:3]:  # 最多3篇完整文档
        doc_text = doc.full_text or ''
        if not doc_text and doc.doc_type == 'link':
            doc_text = f"[链接文档] {doc.title}\n链接：{doc.link_url}\n描述：{doc.description}"
        
        # 限制单篇文档上下文长度，但保留足够内容
        if len(doc_text) > 8000:
            doc_text = doc_text[:8000] + '\n...(文档内容过长，已截断)'
        
        context_parts.append(f"【文档：{doc.title}（分类：{CATEGORIES.get(doc.category, '其他')}）】\n{doc_text}")
        sources_info.append({
            'doc_id': doc.id,
            'doc_title': doc.title,
            'category': doc.category,
            'category_name': CATEGORIES.get(doc.category, '其他'),
            'doc_type': doc.doc_type,
            'page_count': doc.page_count,
            'file_size': doc.file_size,
        })
    
    context = '\n\n---\n\n'.join(context_parts)
    
    # 调用LLM
    llm = LLMAdapter()
    if not llm.is_configured:
        answer = f"【AI未配置】请先在系统设置中配置API Key。\n\n基于文档检索到以下相关文档：\n\n"
        answer += '\n'.join([f"- {s['doc_title']}（{s['category_name']}）" for s in sources_info])
        return {'answer': answer, 'sources': sources_info}
    
    system_prompt = (
        "你是高校辅导员工作平台的智能文档助手。请根据以下完整文档内容回答用户的问题。\n"
        "要求：\n"
        "1. 回答要基于文档内容，如果文档内容不足以回答，请如实说明\n"
        "2. 引用时要标注具体来源（哪份文档、哪个部分或章节）\n"
        "3. 如果是PDF文档，尽量引用具体页码\n"
        "4. 回答要简洁、准确、有条理\n"
        "5. 多篇文档相关时，对比说明\n\n"
        f"文档内容：\n{context}"
    )
    
    try:
        answer = llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ])
    except RuntimeError as e:
        answer = f"【AI回答失败】{str(e)}\n\n检索到相关文档：\n" + '\n'.join([f"- {s['doc_title']}" for s in sources_info])
    
    return {'answer': answer, 'sources': sources_info}


# ===== 批量迁移旧知识库文档到文档工具箱 =====

@router.post('/docbox/migrate')
def migrate_from_knowledge(db: Session = Depends(get_db)):
    """将旧知识库的文档迁移到文档工具箱（保留原文件）"""
    from models import KnowledgeDoc
    old_docs = db.query(KnowledgeDoc).all()
    migrated = 0
    
    for old in old_docs:
        # 检查是否已迁移
        existing = db.query(DocumentFile).filter(DocumentFile.title == old.title).first()
        if existing:
            continue
        
        # 获取文件大小
        file_size = 0
        if old.file_path and os.path.isfile(old.file_path):
            file_size = os.path.getsize(old.file_path)
        
        doc = DocumentFile(
            title=old.title,
            category='other',  # 默认归入"其他"
            description=f'从旧知识库迁移（原{old.chunk_count}个分块）',
            doc_type=old.doc_type,
            file_path=old.file_path,
            file_size=file_size,
            page_count=0,
            full_text=old.content or '',
            created_at=old.created_at or datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(doc)
        migrated += 1
    
    db.commit()
    
    if migrated > 0:
        _rebuild_docbox_fts(db)
    
    return {'migrated': migrated, 'total_old': len(old_docs)}
