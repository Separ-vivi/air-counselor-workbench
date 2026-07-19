"""知识库 AI 能力路由 - 上传/解析/检索/LLM 问答
新文件，不污染原 knowledge_modules.py 的 FAQ/文书部分

注意路由顺序：带具体路径的路由必须在 {kid} 通配路由之前注册。
由于 knowledge_modules.py 已有 GET /api/knowledge 和 GET /api/knowledge/{kid}，
本模块的知识库列表增强通过 GET /api/knowledge/enhanced 提供，避免路由冲突。
"""
import os
import json
import logging
import tempfile
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import KnowledgeDoc, KnowledgeChunk, KnowledgeChat
from services.llm_adapter import LLMAdapter, save_llm_settings, get_llm_settings_masked
from services.file_parser import parse as parse_file
from services.chunker import chunk_text
from services.retriever import ensure_fts_index, insert_chunk_fts, delete_chunk_fts, search as fts_search, rebuild_fts_index

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api')

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploads')


# ===== 文件上传 → 解析 → 分块 → 入库 =====

@router.post('/knowledge/upload')
async def upload_knowledge_doc(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传文件 → 解析 → chunking → 入库 → 建 FTS5 索引"""
    if not file.filename:
        raise HTTPException(400, '文件名不能为空')

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.docx', '.pdf', '.txt'):
        raise HTTPException(400, f'不支持的文件类型: {ext}，仅支持 .docx/.pdf/.txt')

    # 保存文件到 uploads 目录
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    safe_name = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    content_bytes = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content_bytes)

    try:
        # 解析文件
        parsed_text = parse_file(file_path)
        if not parsed_text.strip():
            os.remove(file_path)
            raise HTTPException(400, '文件内容为空或解析失败')

        # 分块
        chunks = chunk_text(parsed_text, size=500, overlap=50)
        if not chunks:
            os.remove(file_path)
            raise HTTPException(400, '文档分块失败，内容可能过短')

        # 创建文档记录
        doc = KnowledgeDoc(
            title=file.filename,
            content=parsed_text[:2000],  # 只存前2000字作为摘要
            doc_type=ext.lstrip('.'),
            file_path=file_path,
            chunk_count=len(chunks),
            created_at=datetime.now(),
        )
        db.add(doc)
        db.flush()  # 拿到 doc.id

        # 入库 chunks
        for idx, chunk_content in enumerate(chunks):
            chunk = KnowledgeChunk(
                doc_id=doc.id,
                chunk_index=idx,
                content=chunk_content,
                source_file=file.filename,
                created_at=datetime.now(),
            )
            db.add(chunk)
            db.flush()  # 拿到 chunk.id
            # 写入 FTS5 索引
            insert_chunk_fts(db, chunk.id, chunk_content)

        db.commit()

        return {
            'id': doc.id,
            'title': doc.title,
            'chunk_count': len(chunks),
            'doc_type': doc.doc_type,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"上传处理失败: {e}")
        # 清理文件
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise HTTPException(500, f'文件处理失败: {str(e)}')


# ===== 知识库列表（增强版，避免与原 GET /api/knowledge 冲突） =====

@router.get('/knowledge/enhanced')
def list_knowledge_enhanced(db: Session = Depends(get_db)):
    """返回知识库文档列表（含 chunk_count/来源文件/创建时间）— 增强版"""
    items = db.query(KnowledgeDoc).order_by(KnowledgeDoc.created_at.desc()).all()
    result = []
    for d in items:
        # 统计实际 chunk 数
        actual_chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.doc_id == d.id).count()
        result.append({
            'id': d.id,
            'title': d.title,
            'doc_type': d.doc_type,
            'content_preview': d.content[:200] + '...' if len(d.content or '') > 200 else (d.content or ''),
            'chunk_count': actual_chunks or d.chunk_count,
            'file_path': d.file_path,
            'created_at': str(d.created_at) if d.created_at else '',
        })
    return result


# ===== 文档 chunk 列表 =====

@router.get('/knowledge/{doc_id}/chunks')
def get_doc_chunks(doc_id: int, db: Session = Depends(get_db)):
    """返回指定文档的 chunk 列表"""
    doc = db.query(KnowledgeDoc).get(doc_id)
    if not doc:
        raise HTTPException(404, '文档不存在')

    chunks = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.doc_id == doc_id
    ).order_by(KnowledgeChunk.chunk_index).all()

    return [{
        'id': c.id,
        'doc_id': c.doc_id,
        'chunk_index': c.chunk_index,
        'content': c.content,
        'source_file': c.source_file,
        'created_at': str(c.created_at) if c.created_at else '',
    } for c in chunks]


# ===== 知识库问答 =====

@router.post('/knowledge/chat')
def knowledge_chat(data: dict, db: Session = Depends(get_db)):
    """检索 chunk → 调 LLM → 返回 answer + sources"""
    question = data.get('question', '').strip()
    if not question:
        raise HTTPException(400, '问题不能为空')

    # 确保 FTS5 索引存在
    ensure_fts_index(db)

    # 检索相关 chunk
    results = fts_search(question, db, top_k=5)

    # 如果 FTS5 没结果，尝试 LIKE 兜底（短文档场景）
    if not results:
        like_pattern = f'%{question[:10]}%'
        fallback = db.execute(text(
            "SELECT id, doc_id, chunk_index, content, source_file FROM knowledge_chunks "
            "WHERE content LIKE :q LIMIT 5"
        ), {'q': like_pattern}).fetchall()
        results = [{
            'id': r.id,
            'doc_id': r.doc_id,
            'chunk_index': r.chunk_index,
            'content': r.content,
            'source_file': r.source_file,
            'rank': 0,
        } for r in fallback]

    if not results:
        # 没有检索到相关内容
        chat_record = KnowledgeChat(
            question=question,
            answer='知识库中暂无相关文档，请先上传文档后再提问。',
            sources_json='[]',
            created_at=datetime.now(),
        )
        db.add(chat_record)
        db.commit()
        return {
            'answer': '知识库中暂无相关文档，请先上传文档后再提问。',
            'sources': [],
        }

    # 构造上下文
    context_parts = []
    sources_info = []
    for r in results:
        context_parts.append(r['content'])
        # 查文档标题
        doc = db.query(KnowledgeDoc).get(r['doc_id'])
        doc_title = doc.title if doc else '未知文档'
        sources_info.append({
            'chunk_id': r['id'],
            'doc_title': doc_title,
            'snippet': r['content'][:150] + '...' if len(r['content']) > 150 else r['content'],
        })

    context = '\n\n'.join(context_parts)

    # 调用 LLM
    llm = LLMAdapter()
    if not llm.is_configured:
        # 未配置 LLM，返回友好提示 + 检索结果
        answer = f"【LLM 未配置】请先在系统设置中配置 API Key。\n\n基于知识库检索到以下相关内容：\n\n" + '\n---\n'.join(context_parts[:3])
        chat_record = KnowledgeChat(
            question=question,
            answer=answer,
            sources_json=json.dumps(sources_info, ensure_ascii=False),
            created_at=datetime.now(),
        )
        db.add(chat_record)
        db.commit()
        return {'answer': answer, 'sources': sources_info}

    system_prompt = (
        "你是高校辅导员工作平台的智能助手。请根据以下知识库内容回答用户的问题。"
        "如果知识库内容不足以回答问题，请如实说明。回答要简洁、准确、有条理。\n\n"
        f"知识库内容：\n{context}"
    )

    try:
        answer = llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ])
    except RuntimeError as e:
        # LLM 调用失败，返回友好错误 + 检索结果
        answer = f"【AI 回答失败】{str(e)}\n\n基于知识库检索到以下相关内容：\n\n" + '\n---\n'.join(context_parts[:3])

    # 保存聊天记录
    chat_record = KnowledgeChat(
        question=question,
        answer=answer,
        sources_json=json.dumps(sources_info, ensure_ascii=False),
        created_at=datetime.now(),
    )
    db.add(chat_record)
    db.commit()

    return {'answer': answer, 'sources': sources_info}


# ===== 聊天历史 =====

@router.get('/knowledge/chat/history')
def chat_history(db: Session = Depends(get_db)):
    """返回最近 20 条聊天记录"""
    records = db.query(KnowledgeChat).order_by(
        KnowledgeChat.created_at.desc()
    ).limit(20).all()

    return [{
        'id': r.id,
        'question': r.question,
        'answer': r.answer,
        'sources': json.loads(r.sources_json) if r.sources_json else [],
        'created_at': str(r.created_at) if r.created_at else '',
    } for r in records]


# ===== 删除文档（含关联 chunks + 聊天 + FTS5 清理） =====

@router.delete('/knowledge/{doc_id}/full')
def delete_knowledge_full(doc_id: int, db: Session = Depends(get_db)):
    """删除文档 + 关联 chunks + FTS5 索引清理"""
    doc = db.query(KnowledgeDoc).get(doc_id)
    if not doc:
        raise HTTPException(404, '文档不存在')

    # 删除 FTS5 索引
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.doc_id == doc_id).all()
    for chunk in chunks:
        delete_chunk_fts(db, chunk.id)

    # 删除 chunks（CASCADE 应该会处理，但显式删更安全）
    db.query(KnowledgeChunk).filter(KnowledgeChunk.doc_id == doc_id).delete()

    # 删除文档记录
    db.delete(doc)
    db.commit()

    # 尝试删除文件
    if doc.file_path and os.path.isfile(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"删除文件失败: {e}")

    return {'ok': True, 'message': f'文档 {doc_id} 及关联数据已删除'}


# ===== 系统 LLM 设置 =====

@router.get('/system/llm-settings')
def get_llm_settings():
    """返回当前 LLM 配置（api_key 脱敏）"""
    return get_llm_settings_masked()


@router.post('/system/llm-settings')
def update_llm_settings(data: dict):
    """更新 LLM 配置"""
    api_key = data.get('api_key', '')
    base_url = data.get('base_url', '')
    model = data.get('model', '')
    model_name = data.get('model_name', '')

    if not any([api_key, base_url, model, model_name]):
        raise HTTPException(400, '至少提供一个配置项')

    llm = save_llm_settings(
        api_key=api_key,
        base_url=base_url,
        model=model,
        model_name=model_name,
    )
    return {'ok': True, 'message': 'LLM 配置已更新'}
