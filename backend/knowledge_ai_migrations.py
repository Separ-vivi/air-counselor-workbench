"""知识库 AI 能力 - 数据库迁移（幂等）
建 knowledge_chunks / knowledge_chats / system_settings 三张表 + FTS5 虚拟表
"""
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


def run_knowledge_ai_migrations(engine):
    """执行知识库 AI 相关的数据库迁移（幂等）"""
    with engine.begin() as conn:
        # 1. knowledge_chunks 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                chunk_index INTEGER DEFAULT 0,
                content TEXT DEFAULT '',
                source_file VARCHAR(500) DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (doc_id) REFERENCES knowledge_docs(id) ON DELETE CASCADE
            )
        """))
        # 索引
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_doc_id ON knowledge_chunks(doc_id)"))
        except Exception:
            pass

        # 2. knowledge_chats 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT DEFAULT '',
                sources_json TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """))

        # 3. system_settings 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(100) NOT NULL UNIQUE,
                value TEXT DEFAULT '',
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """))

        # 4. FTS5 虚拟表
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_chunks_fts USING fts5(
                content,
                content='knowledge_chunks',
                content_rowid='id'
            )
        """))

    logger.info("知识库 AI 迁移完成（knowledge_chunks / knowledge_chats / system_settings / FTS5）")
