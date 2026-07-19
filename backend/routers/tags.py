"""标签管理路由 - V5-d 扩展
包含标签 CRUD 和学生-标签关联操作
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from database import get_db
from models import Tag, Student, student_tags
from schemas import TagCreate, TagUpdate, TagOut

# ===== 标签管理路由（原有功能） =====

router = APIRouter(prefix='/api/tags', tags=['标签管理'])


@router.get('', response_model=list)
def list_tags(db: Session = Depends(get_db)):
    """获取所有标签（含学生数统计）"""
    tags = db.query(Tag).order_by(Tag.group_name, Tag.name).all()
    result = []
    for t in tags:
        count = db.query(func.count(student_tags.c.student_id)).filter(
            student_tags.c.tag_id == t.id
        ).scalar()
        result.append({
            'id': t.id,
            'name': t.name,
            'group_name': t.group_name,
            'color': t.color,
            'student_count': count,
        })
    return result


@router.get('/groups')
def list_tag_groups(db: Session = Depends(get_db)):
    """获取标签分组列表"""
    groups = db.query(Tag.group_name).distinct().all()
    result = []
    for g in groups:
        tags = db.query(Tag).filter(Tag.group_name == g[0]).all()
        result.append({
            'group_name': g[0],
            'tags': [
                {
                    'id': t.id, 'name': t.name, 'color': t.color,
                    'student_count': db.query(func.count(student_tags.c.student_id)).filter(
                        student_tags.c.tag_id == t.id
                    ).scalar()
                }
                for t in tags
            ]
        })
    return result


@router.post('', response_model=dict)
def create_tag(data: TagCreate, db: Session = Depends(get_db)):
    """新增标签"""
    existing = db.query(Tag).filter(
        Tag.name == data.name, Tag.group_name == data.group_name
    ).first()
    if existing:
        raise HTTPException(400, f'标签 "{data.name}" 在分组 "{data.group_name}" 中已存在')

    tag = Tag(**data.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return {'id': tag.id, 'message': '创建成功'}


@router.put('/{tag_id}', response_model=dict)
def update_tag(tag_id: int, data: TagUpdate, db: Session = Depends(get_db)):
    """更新标签"""
    tag = db.query(Tag).get(tag_id)
    if not tag:
        raise HTTPException(404, '标签不存在')

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tag, key, value)
    db.commit()
    return {'message': '更新成功'}


@router.delete('/{tag_id}', response_model=dict)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """删除标签"""
    tag = db.query(Tag).get(tag_id)
    if not tag:
        raise HTTPException(404, '标签不存在')
    db.delete(tag)
    db.commit()
    return {'message': '删除成功'}


@router.post('/{tag_id}/students/{student_id}', response_model=dict)
def add_tag_to_student(tag_id: int, student_id: int, db: Session = Depends(get_db)):
    """给学生添加标签"""
    student = db.query(Student).get(student_id)
    tag = db.query(Tag).get(tag_id)
    if not student or not tag:
        raise HTTPException(404, '学生或标签不存在')

    if tag in student.tags:
        return {'message': '标签已存在'}

    student.tags.append(tag)
    db.commit()
    return {'message': '添加成功'}


@router.delete('/{tag_id}/students/{student_id}', response_model=dict)
def remove_tag_from_student(tag_id: int, student_id: int, db: Session = Depends(get_db)):
    """从学生移除标签"""
    student = db.query(Student).get(student_id)
    tag = db.query(Tag).get(tag_id)
    if not student or not tag:
        raise HTTPException(404, '学生或标签不存在')

    if tag in student.tags:
        student.tags.remove(tag)
        db.commit()
    return {'message': '移除成功'}


# ===== V5-d: 学生维度的标签操作端点 =====

class StudentTagAdd(BaseModel):
    """给学生添加标签的请求体"""
    tag_id: int

# 学生标签路由（独立 router，前缀为 /api）
student_tag_router = APIRouter(prefix='/api', tags=['学生标签'])


@student_tag_router.get('/students/{student_id}/tags')
def get_student_tags(student_id: int, db: Session = Depends(get_db)):
    """获取学生的所有标签"""
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(404, '学生不存在')

    tags = student.tags.all() if hasattr(student.tags, 'all') else list(student.tags)
    return [
        {
            'id': t.id,
            'name': t.name,
            'group_name': t.group_name,
            'color': t.color,
        }
        for t in tags
    ]


@student_tag_router.post('/students/{student_id}/tags')
def add_student_tag(student_id: int, data: StudentTagAdd, db: Session = Depends(get_db)):
    """给学生添加标签（请求体: {tag_id}）"""
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(404, '学生不存在')

    tag = db.query(Tag).get(data.tag_id)
    if not tag:
        raise HTTPException(404, '标签不存在')

    # 检查是否已存在
    existing_tags = student.tags.all() if hasattr(student.tags, 'all') else list(student.tags)
    if tag in existing_tags:
        return {'message': '标签已存在'}

    student.tags.append(tag)
    db.commit()
    return {'message': '添加成功'}


@student_tag_router.delete('/students/{student_id}/tags/{tag_id}')
def remove_student_tag(student_id: int, tag_id: int, db: Session = Depends(get_db)):
    """移除学生标签"""
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(404, '学生不存在')

    tag = db.query(Tag).get(tag_id)
    if not tag:
        raise HTTPException(404, '标签不存在')

    existing_tags = student.tags.all() if hasattr(student.tags, 'all') else list(student.tags)
    if tag in existing_tags:
        student.tags.remove(tag)
        db.commit()
    return {'message': '移除成功'}
