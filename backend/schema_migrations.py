"""
Schema 自愈机制
-----------------
sqlite `create_all` 只在表不存在时建表，schema 迁移不会自动进行。
本模块在启动时对每个 model 表：
  1. 读取实际列（PRAGMA table_info）
  2. 对比 model 定义
  3. 缺失的列用 ALTER TABLE ADD COLUMN 补齐（backward-compatible）
另提供 hard_reset()：drop_all + create_all + seed，供系统设置调用。

作者：多多 · V3-A 补丁
"""
import logging
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# SQLAlchemy 类型 → SQLite 类型
_TYPE_MAP = {
    'INTEGER': 'INTEGER',
    'BIGINT':  'INTEGER',
    'SMALLINT':'INTEGER',
    'BOOLEAN': 'INTEGER',
    'VARCHAR': 'TEXT',
    'TEXT':    'TEXT',
    'STRING':  'TEXT',
    'CHAR':    'TEXT',
    'DATETIME':'TEXT',
    'DATE':    'TEXT',
    'FLOAT':   'REAL',
    'NUMERIC': 'REAL',
    'REAL':    'REAL',
}

def _sqlite_type(col):
    t = str(col.type).upper()
    # 剥离 VARCHAR(100) → VARCHAR
    base = t.split('(')[0].strip()
    return _TYPE_MAP.get(base, 'TEXT')

def _default_literal(col):
    """把 model 里的 default 转成 SQL DEFAULT 字面量。"""
    d = col.default
    if d is None:
        return None
    if hasattr(d, 'arg'):
        v = d.arg
        if callable(v):
            return None  # datetime.now 等不能 SQL 表达
        if isinstance(v, bool):
            return '1' if v else '0'
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, str):
            # 转义单引号
            esc = v.replace("'", "''")
            return f"'{esc}'"
    return None

def ensure_schema_up_to_date(engine, base):
    """
    对每张表：
      - 表不存在 → create_all 会自建，跳过
      - 表存在但缺列 → ALTER TABLE ADD COLUMN
      - 表存在且列齐 → 跳过
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    added = 0
    with engine.begin() as conn:
        for table_name, table in base.metadata.tables.items():
            if table_name not in existing_tables:
                continue  # create_all 会建
            actual_cols = {c['name'] for c in inspector.get_columns(table_name)}
            for col in table.columns:
                if col.name in actual_cols:
                    continue
                col_type = _sqlite_type(col)
                default = _default_literal(col)
                sql = f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {col_type}'
                if default is not None:
                    sql += f' DEFAULT {default}'
                try:
                    conn.execute(text(sql))
                    added += 1
                    logger.info(f'[schema] + {table_name}.{col.name} ({col_type})')
                except OperationalError as e:
                    logger.warning(f'[schema] add column failed {table_name}.{col.name}: {e}')
    if added:
        logger.info(f'[schema] 完成迁移，新增 {added} 个字段')
    else:
        logger.info('[schema] 所有表字段已对齐，无需迁移')
    return added


def hard_reset(engine, base):
    """Drop 全部业务表 → 重建 → 由调用方决定是否 seed。"""
    logger.warning('[schema] hard_reset: drop_all + create_all')
    base.metadata.drop_all(bind=engine)
    base.metadata.create_all(bind=engine)
    return True


def get_schema_health(engine, base):
    """返回每个表的健康状态。"""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    report = []
    total_missing = 0
    for table_name, table in base.metadata.tables.items():
        if table_name not in existing_tables:
            report.append({'table': table_name, 'status': 'missing_table', 'missing_cols': []})
            continue
        actual_cols = {c['name'] for c in inspector.get_columns(table_name)}
        expected_cols = {c.name for c in table.columns}
        missing = list(expected_cols - actual_cols)
        total_missing += len(missing)
        report.append({
            'table': table_name,
            'status': 'ok' if not missing else 'missing_cols',
            'missing_cols': missing,
            'actual_col_count': len(actual_cols),
            'expected_col_count': len(expected_cols),
        })
    return {
        'total_tables': len(report),
        'total_missing_cols': total_missing,
        'healthy': total_missing == 0,
        'tables': report,
    }
