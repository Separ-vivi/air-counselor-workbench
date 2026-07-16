"""
通用列表查询辅助函数
支持搜索、排序、筛选、分页
"""
from typing import Any, Dict, List, Optional, Type
from sqlalchemy import or_, and_, asc, desc
from sqlalchemy.orm import Query, Session
from sqlalchemy.orm import DeclarativeBase


def list_with_search_filter_sort(
    db: Session,
    model: Type[DeclarativeBase],
    query_params: Dict[str, Any],
    search_fields: Optional[List[str]] = None,
    filter_fields: Optional[Dict[str, str]] = None,
    default_sort: Optional[str] = None,
    default_order: str = "desc",
) -> Dict[str, Any]:
    """
    通用列表查询函数
    
    Args:
        db: 数据库会话
        model: SQLAlchemy 模型类
        query_params: 请求参数 (FastAPI 的 Query 参数)
        search_fields: 可搜索的字段列表 (用于 LIKE 模糊搜索)
        filter_fields: 可筛选的字段映射 {参数名: 数据库字段名}
        default_sort: 默认排序字段
        default_order: 默认排序方向 (asc/desc)
    
    Returns:
        {
            "items": [...],  # 数据列表
            "total": int,    # 总数
            "page": int,     # 当前页
            "size": int,     # 每页大小
        }
    """
    # 解析分页参数
    page = int(query_params.get("page", 1))
    size = int(query_params.get("size", query_params.get("page_size", 20)))
    if page < 1:
        page = 1
    if size < 1 or size > 1000:
        size = 20
    
    # 基础查询
    query = db.query(model)
    
    # 搜索处理 (LIKE '%keyword%')
    search = query_params.get("search", "").strip()
    if search and search_fields:
        search_conditions = []
        for field in search_fields:
            if hasattr(model, field):
                column = getattr(model, field)
                search_conditions.append(column.ilike(f"%{search}%"))
        if search_conditions:
            query = query.filter(or_(*search_conditions))
    
    # 筛选处理 (精确匹配)
    if filter_fields:
        filter_conditions = []
        for param_name, db_field in filter_fields.items():
            value = query_params.get(param_name)
            if value and hasattr(model, db_field):
                column = getattr(model, db_field)
                # 支持多值筛选 (逗号分隔)
                if "," in str(value):
                    values = [v.strip() for v in str(value).split(",")]
                    filter_conditions.append(column.in_(values))
                else:
                    filter_conditions.append(column == value)
        if filter_conditions:
            query = query.filter(and_(*filter_conditions))
    
    # 排序处理
    sort_by = query_params.get("sort_by", query_params.get("sort", default_sort))
    order = query_params.get("order", default_order).lower()
    
    if sort_by and hasattr(model, sort_by):
        column = getattr(model, sort_by)
        if order == "asc":
            query = query.order_by(asc(column))
        else:
            query = query.order_by(desc(column))
    elif default_sort and hasattr(model, default_sort):
        column = getattr(model, default_sort)
        if default_order == "asc":
            query = query.order_by(asc(column))
        else:
            query = query.order_by(desc(column))
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


def student_search(db: Session, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    学生远程搜索 (用于关联选择器)
    支持学号、姓名、班级模糊搜索
    """
    from models import Student
    
    if not keyword or not keyword.strip():
        return []
    
    keyword = keyword.strip()
    search_pattern = f"%{keyword}%"
    
    results = db.query(
        Student.id,
        Student.student_no,
        Student.name,
        Student.class_name
    ).filter(
        or_(
            Student.student_no.ilike(search_pattern),
            Student.name.ilike(search_pattern),
            Student.class_name.ilike(search_pattern),
        )
    ).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "student_no": r.student_no,
            "name": r.name,
            "class_name": r.class_name,
            "label": f"{r.name} ({r.student_no} · {r.class_name})",
        }
        for r in results
    ]
