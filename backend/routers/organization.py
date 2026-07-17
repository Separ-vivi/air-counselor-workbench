"""组织架构 API - 年级/专业/班级"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import Grade, Major, ClassModel, Student

router = APIRouter(prefix='/api/org', tags=['organization'])


class GradeCreate(BaseModel):
    grade_name: str
    start_year: int


class MajorCreate(BaseModel):
    major_name: str
    grade_id: int


class ClassCreate(BaseModel):
    class_name: str
    major_id: int
    class_teacher: Optional[str] = ''
    monitor: Optional[str] = ''
    league_secretary: Optional[str] = ''


# ===== 年级 =====

@router.get('/grades')
def list_grades(db: Session = Depends(get_db)):
    grades = db.query(Grade).order_by(Grade.start_year.desc()).all()
    result = []
    for g in grades:
        result.append({
            'id': g.id,
            'grade_name': g.grade_name,
            'start_year': g.start_year,
            'major_count': len(g.majors) if g.majors else 0,
        })
    return result


@router.post('/grades')
def create_grade(data: GradeCreate, db: Session = Depends(get_db)):
    grade = Grade(**data.dict())
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return {'id': grade.id, 'grade_name': grade.grade_name, 'start_year': grade.start_year}


@router.put('/grades/{grade_id}')
def update_grade(grade_id: int, data: GradeCreate, db: Session = Depends(get_db)):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="年级不存在")
    grade.grade_name = data.grade_name
    grade.start_year = data.start_year
    db.commit()
    return {'id': grade.id, 'grade_name': grade.grade_name, 'start_year': grade.start_year}


@router.delete('/grades/{grade_id}')
def delete_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="年级不存在")
    db.delete(grade)
    db.commit()
    return {'message': '删除成功'}


# ===== 专业 =====

@router.get('/majors')
def list_majors(grade_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Major)
    if grade_id:
        query = query.filter(Major.grade_id == grade_id)
    majors = query.all()
    result = []
    for m in majors:
        result.append({
            'id': m.id,
            'major_name': m.major_name,
            'grade_id': m.grade_id,
            'grade_name': m.grade.grade_name if m.grade else '',
            'class_count': len(m.classes) if m.classes else 0,
        })
    return result


@router.post('/majors')
def create_major(data: MajorCreate, db: Session = Depends(get_db)):
    major = Major(**data.dict())
    db.add(major)
    db.commit()
    db.refresh(major)
    return {'id': major.id, 'major_name': major.major_name, 'grade_id': major.grade_id}


@router.put('/majors/{major_id}')
def update_major(major_id: int, data: MajorCreate, db: Session = Depends(get_db)):
    major = db.query(Major).filter(Major.id == major_id).first()
    if not major:
        raise HTTPException(status_code=404, detail="专业不存在")
    major.major_name = data.major_name
    major.grade_id = data.grade_id
    db.commit()
    return {'id': major.id, 'major_name': major.major_name, 'grade_id': major.grade_id}


@router.delete('/majors/{major_id}')
def delete_major(major_id: int, db: Session = Depends(get_db)):
    major = db.query(Major).filter(Major.id == major_id).first()
    if not major:
        raise HTTPException(status_code=404, detail="专业不存在")
    db.delete(major)
    db.commit()
    return {'message': '删除成功'}


# ===== 班级 =====

@router.get('/classes')
def list_classes(major_id: Optional[int] = None, grade_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(ClassModel)
    if major_id:
        query = query.filter(ClassModel.major_id == major_id)
    classes = query.all()

    result = []
    for c in classes:
        # 如果指定了 grade_id 过滤
        if grade_id and c.major and c.major.grade_id != grade_id:
            continue
        student_count = db.query(Student).filter(Student.class_id == c.id).count()
        result.append({
            'id': c.id,
            'class_name': c.class_name,
            'major_id': c.major_id,
            'major_name': c.major.major_name if c.major else '',
            'grade_name': c.major.grade.grade_name if c.major and c.major.grade else '',
            'class_teacher': c.class_teacher,
            'monitor': c.monitor,
            'league_secretary': c.league_secretary,
            'student_count': student_count,
        })
    return result


@router.get('/classes/export')
def export_classes_all(
    search: str = Query(''),
    grade_id: Optional[int] = None,
    major_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """按当前筛选/搜索导出全部班级 Excel (v3j-B-b02)"""
    from openpyxl import Workbook
    from io import BytesIO
    from fastapi.responses import StreamingResponse

    query = db.query(ClassModel)
    if major_id:
        query = query.filter(ClassModel.major_id == major_id)
    classes = query.all()

    rows = []
    for c in classes:
        if grade_id and c.major and c.major.grade_id != grade_id:
            continue
        if search:
            kw = search.strip()
            fields = [c.class_name or '', c.class_teacher or '', c.monitor or '', c.league_secretary or '',
                      (c.major.major_name if c.major else ''), (c.major.grade.grade_name if c.major and c.major.grade else '')]
            if not any(kw in (v or '') for v in fields):
                continue
        student_count = db.query(Student).filter(Student.class_id == c.id).count()
        rows.append({
            'class_name': c.class_name,
            'grade_name': c.major.grade.grade_name if c.major and c.major.grade else '',
            'major_name': c.major.major_name if c.major else '',
            'class_teacher': c.class_teacher or '',
            'monitor': c.monitor or '',
            'league_secretary': c.league_secretary or '',
            'student_count': student_count,
        })

    wb = Workbook()
    ws = wb.active
    ws.title = '班级列表'
    ws.append(['班级名称', '年级', '专业', '班主任', '班长', '团支书', '人数'])
    for r in rows:
        ws.append([r['class_name'], r['grade_name'], r['major_name'], r['class_teacher'], r['monitor'], r['league_secretary'], r['student_count']])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=classes_all.xlsx'}
    )


@router.post('/classes/export')
def export_classes_by_ids(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """按 ID 列表批量导出班级 Excel (v3j-B-b02)"""
    from openpyxl import Workbook
    from io import BytesIO
    from fastapi.responses import StreamingResponse

    ids = payload.get('ids') or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(400, '请传入非空的 ids 列表')

    classes = db.query(ClassModel).filter(ClassModel.id.in_(ids)).all()
    wb = Workbook()
    ws = wb.active
    ws.title = '班级列表'
    ws.append(['班级名称', '年级', '专业', '班主任', '班长', '团支书', '人数'])
    for c in classes:
        grade_name = c.major.grade.grade_name if c.major and c.major.grade else ''
        major_name = c.major.major_name if c.major else ''
        student_count = db.query(Student).filter(Student.class_id == c.id).count()
        ws.append([c.class_name, grade_name, major_name, c.class_teacher or '', c.monitor or '', c.league_secretary or '', student_count])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=classes_selected.xlsx'}
    )


@router.post('/classes')
def create_class(data: ClassCreate, db: Session = Depends(get_db)):
    existing = db.query(ClassModel).filter(ClassModel.class_name == data.class_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="班级名称已存在")
    cls = ClassModel(**data.dict())
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return {'id': cls.id, 'class_name': cls.class_name, 'major_id': cls.major_id}


@router.get('/classes/{class_id}')
def get_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    students = db.query(Student).filter(Student.class_id == class_id).all()
    return {
        'id': cls.id,
        'class_name': cls.class_name,
        'major_id': cls.major_id,
        'major_name': cls.major.major_name if cls.major else '',
        'grade_name': cls.major.grade.grade_name if cls.major and cls.major.grade else '',
        'class_teacher': cls.class_teacher,
        'monitor': cls.monitor,
        'league_secretary': cls.league_secretary,
        'students': [{'id': s.id, 'student_no': s.student_no, 'name': s.name, 'gender': s.gender, 'phone': s.phone}
                     for s in students],
    }


@router.put('/classes/{class_id}')
def update_class(class_id: int, data: ClassCreate, db: Session = Depends(get_db)):
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    for key, value in data.dict().items():
        setattr(cls, key, value)
    db.commit()
    return {'id': cls.id, 'class_name': cls.class_name}


@router.delete('/classes/{class_id}')
def delete_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    db.delete(cls)
    db.commit()
    return {'message': '删除成功'}


# ===== 组织架构树 =====

@router.get('/tree')
def get_org_tree(db: Session = Depends(get_db)):
    """获取完整组织架构树"""
    grades = db.query(Grade).order_by(Grade.start_year.desc()).all()
    result = []
    for g in grades:
        grade_data = {
            'id': g.id,
            'grade_name': g.grade_name,
            'start_year': g.start_year,
            'majors': []
        }
        for m in g.majors:
            major_data = {
                'id': m.id,
                'major_name': m.major_name,
                'classes': []
            }
            for c in m.classes:
                student_count = db.query(Student).filter(Student.class_id == c.id).count()
                major_data['classes'].append({
                    'id': c.id,
                    'class_name': c.class_name,
                    'student_count': student_count,
                    'class_teacher': c.class_teacher,
                })
            grade_data['majors'].append(major_data)
        result.append(grade_data)
    return result
