"""检索器 - SQLite FTS5 + 中文 2-gram 分词预处理"""
import logging
import re
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def _bigram_tokenize(s: str) -> str:
    """
    中文 2-gram 分词预处理
    对中文连续字符做相邻字组合，英文按空格分词
    结果用空格拼接，供 FTS5 索引/查询使用
    """
    if not s:
        return ''
    tokens = []
    i = 0
    while i < len(s):
        ch = s[i]
        if '\u4e00' <= ch <= '\u9fff':
            # 中文字符：与下一个中文字符组成 bigram
            if i + 1 < len(s) and '\u4e00' <= s[i+1] <= '\u9fff':
                tokens.append(ch + s[i+1])
            # 也保留单字用于单字查询
            tokens.append(ch)
        elif ch.isalnum():
            # 英文/数字：累积连续的 alnum 作为一个 token
            j = i
            while j < len(s) and s[j].isalnum():
                j += 1
            tokens.append(s[i:j].lower())
            i = j
            continue
        # 其他字符（空格、标点）跳过
        i += 1
    return ' '.join(tokens)


def _build_fts_query(s: str) -> str:
    """
    构造 FTS5 MATCH 查询字符串
    用 OR 连接各 token，宽松匹配
    """
    tokens = _bigram_tokenize(s).split()
    if not tokens:
        return ''
    # 用 OR 连接，宽松匹配
    # 对中文 bigram token 用引号包裹（避免 FTS5 解析错误）
    safe_tokens = []
    for t in tokens:
        if t:
            safe_tokens.append(f'"{t}"')
    return ' OR '.join(safe_tokens)


def ensure_fts_index(db: Session):
    """确保 FTS5 虚拟表存在（幂等）"""
    db.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_chunks_fts USING fts5(
            content,
            content='knowledge_chunks',
            content_rowid='id'
        )
    """))
    db.commit()
    logger.info("FTS5 虚拟表已确认存在")


def rebuild_fts_index(db: Session):
    """重建 FTS5 索引（清空后全量插入）"""
    # 先清空旧索引
    db.execute(text("DELETE FROM knowledge_chunks_fts"))
    # 重新插入所有 chunk
    chunks = db.execute(text("SELECT id, content FROM knowledge_chunks")).fetchall()
    for chunk_id, content in chunks:
        bigram = _bigram_tokenize(content or '')
        db.execute(text("INSERT INTO knowledge_chunks_fts(rowid, content) VALUES(:id, :c)"),
                   {'id': chunk_id, 'c': bigram})
    db.commit()
    logger.info(f"FTS5 索引重建完成，共 {len(chunks)} 条")


def insert_chunk_fts(db: Session, chunk_id: int, content: str):
    """插入单条 chunk 到 FTS5 索引"""
    bigram = _bigram_tokenize(content)
    db.execute(text("INSERT INTO knowledge_chunks_fts(rowid, content) VALUES(:id, :c)"),
               {'id': chunk_id, 'c': bigram})
    db.commit()


def delete_chunk_fts(db: Session, chunk_id: int):
    """从 FTS5 索引删除单条"""
    try:
        db.execute(text("DELETE FROM knowledge_chunks_fts WHERE rowid = :id"), {'id': chunk_id})
        db.commit()
    except Exception as e:
        logger.warning(f"FTS5 删除 chunk {chunk_id} 失败: {e}")


def search(query: str, db: Session, top_k: int = 5) -> list[dict]:
    """
    FTS5 检索相关 chunk
    :param query: 用户查询
    :param db: 数据库会话
    :param top_k: 返回前 K 条
    :return: [{id, doc_id, chunk_index, content, source_file, rank}]
    """
    fts_query = _build_fts_query(query)
    if not fts_query.strip():
        return []

    try:
        results = db.execute(text("""
            SELECT fts.rowid as id, kc.doc_id, kc.chunk_index, kc.content, kc.source_file, fts.rank
            FROM knowledge_chunks_fts fts
            JOIN knowledge_chunks kc ON fts.rowid = kc.id
            WHERE knowledge_chunks_fts MATCH :q
            ORDER BY fts.rank
            LIMIT :k
        """), {'q': fts_query, 'k': top_k}).fetchall()

        return [{
            'id': r.id,
            'doc_id': r.doc_id,
            'chunk_index': r.chunk_index,
            'content': r.content,
            'source_file': r.source_file,
            'rank': r.rank,
        } for r in results]
    except Exception as e:
        logger.warning(f"FTS5 搜索失败: {e}, query={fts_query}")
        return []
