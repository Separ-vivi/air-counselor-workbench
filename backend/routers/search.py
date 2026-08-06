"""全局搜索路由 - V5-d
支持跨学生、班级、FAQ、模板的模糊搜索
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Student, ClassModel, FAQ, DocumentTemplate

router = APIRouter(prefix='/api/search', tags=['全局搜索'])


@router.get('')
def global_search(
    q: str = Query('', description='搜索关键词'),
    scope: str = Query('all', description='搜索范围: all/students/classes/faqs/templates'),
    db: Session = Depends(get_db),
):
    """全局搜索端点
    - students: 在 name / student_no / phone / email 中模糊搜索
    - classes: 在 class_name 中模糊搜索
    - faqs: 在 question / answer 中模糊搜索
    - templates: 在 name / content 中模糊搜索
    每个类别最多返回 10 条
    """
    keyword = q.strip()
    if not keyword:
        return {'students': [], 'classes': [], 'faqs': [], 'templates': []}

    pattern = f'%{keyword}%'
    result = {}

    # 学生搜索
    if scope in ('all', 'students'):
        students = (
            db.query(Student)
            .outerjoin(ClassModel, Student.class_id == ClassModel.id)
            .filter(
                Student.name.ilike(pattern)
                | Student.student_no.ilike(pattern)
                | Student.phone.ilike(pattern)
                | Student.email.ilike(pattern)
            )
            .limit(10)
            .all()
        )
        result['students'] = [
            {
                'id': s.id,
                'name': s.name,
                'student_no': s.student_no,
                'class_name': s.class_obj.class_name if s.class_obj else '',
            }
            for s in students
        ]

    # 班级搜索
    if scope in ('all', 'classes'):
        classes = (
            db.query(ClassModel)
            .filter(ClassModel.class_name.ilike(pattern))
            .limit(10)
            .all()
        )
        result['classes'] = [
            {'id': c.id, 'class_name': c.class_name}
            for c in classes
        ]

    # FAQ 搜索
    if scope in ('all', 'faqs'):
        faqs = (
            db.query(FAQ)
            .filter(FAQ.question.ilike(pattern) | FAQ.answer.ilike(pattern))
            .limit(10)
            .all()
        )
        result['faqs'] = [
            {'id': f.id, 'question': f.question, 'answer': f.answer}
            for f in faqs
        ]

    # 模板搜索
    if scope in ('all', 'templates'):
        templates = (
            db.query(DocumentTemplate)
            .filter(DocumentTemplate.name.ilike(pattern) | DocumentTemplate.content.ilike(pattern))
            .limit(10)
            .all()
        )
        result['templates'] = [
            {'id': t.id, 'name': t.name, 'template_type': t.template_type}
            for t in templates
        ]

    return result
