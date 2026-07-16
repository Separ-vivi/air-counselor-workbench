"""驾驶舱数据路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
from models import Student, Tag, GradeRecord, WarningRecord, student_tags, ClassModel, Major

router = APIRouter(prefix='/api/dashboard', tags=['驾驶舱'])


@router.get('')
def get_dashboard(
    class_name: Optional[str] = Query(None),
    major: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取驾驶舱数据"""
    # 基础查询 - 使用 join
    base_query = db.query(Student).outerjoin(ClassModel, Student.class_id == ClassModel.id).outerjoin(Major, ClassModel.major_id == Major.id)
    if class_name:
        base_query = base_query.filter(ClassModel.class_name == class_name)
    if major:
        base_query = base_query.filter(Major.major_name == major)

    total_students = base_query.count()

    # 班级数
    if class_name:
        total_classes = 1
    else:
        total_classes = db.query(func.count(func.distinct(ClassModel.id))).join(
            Student, Student.class_id == ClassModel.id
        ).filter(ClassModel.class_name != '').scalar() or 0

    # 专业数
    if major:
        total_majors = 1
    else:
        total_majors = db.query(func.count(func.distinct(Major.id))).join(
            ClassModel, ClassModel.major_id == Major.id
        ).join(Student, Student.class_id == ClassModel.id).filter(Major.major_name != '').scalar() or 0

    # 预警统计
    student_ids = [s.id for s in base_query.all()]
    warning_query = db.query(WarningRecord)
    if student_ids:
        warning_query = warning_query.filter(WarningRecord.student_id.in_(student_ids))

    red_count = warning_query.filter(WarningRecord.warning_type == 'red').count()
    yellow_count = warning_query.filter(WarningRecord.warning_type == 'yellow').count()

    # 班级分布
    class_dist_query = db.query(
        ClassModel.class_name, func.count(Student.id)
    ).outerjoin(Student, Student.class_id == ClassModel.id).filter(
        ClassModel.class_name != ''
    )
    if major:
        class_dist_query = class_dist_query.filter(Major.major_name == major)
    class_distribution = [
        {'name': name, 'value': count}
        for name, count in class_dist_query.group_by(ClassModel.id).all()
    ]

    # 专业分布
    major_dist_query = db.query(
        Major.major_name, func.count(Student.id)
    ).outerjoin(ClassModel, ClassModel.major_id == Major.id).outerjoin(
        Student, Student.class_id == ClassModel.id
    ).filter(Major.major_name != '')
    if class_name:
        major_dist_query = major_dist_query.filter(ClassModel.class_name == class_name)
    major_distribution = [
        {'name': name, 'value': count}
        for name, count in major_dist_query.group_by(Major.id).all()
        if count > 0
    ]

    # 标签分布 TOP 10
    tag_dist = db.query(
        Tag.name, Tag.color, func.count(student_tags.c.student_id)
    ).join(student_tags, Tag.id == student_tags.c.tag_id)
    if student_ids:
        tag_dist = tag_dist.filter(student_tags.c.student_id.in_(student_ids))
    tag_distribution = [
        {'name': name, 'color': color, 'value': count}
        for name, color, count in tag_dist.group_by(Tag.id).order_by(
            func.count(student_tags.c.student_id).desc()
        ).limit(10).all()
    ]

    # 近期新增/更新学生
    recent_query = base_query.order_by(Student.updated_at.desc()).limit(5)
    recent_students = [
        {
            'id': s.id, 'name': s.name, 'student_no': s.student_no,
            'class_name': s.class_name,
            'updated_at': s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in recent_query.all()
    ]

    return {
        'total_students': total_students,
        'total_classes': total_classes,
        'total_majors': total_majors,
        'red_count': red_count,
        'yellow_count': yellow_count,
        'normal_count': total_students - red_count - yellow_count,
        'class_distribution': class_distribution,
        'major_distribution': major_distribution,
        'tag_distribution': tag_distribution,
        'recent_students': recent_students,
    }
