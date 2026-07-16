"""学生干部 + 班主任 + 就业升学 路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import StudentCadreRecord, ClassTeacher, EmploymentRecord, Student

router = APIRouter(prefix='/api')


def _get_student_class_name(db: Session, student_id: int) -> str:
    """通过student_id获取班级名称"""
    stu = db.query(Student).filter(Student.id == student_id).first()
    if stu and stu.class_obj:
        return stu.class_obj.class_name
    return ''


# ===== 学生干部 =====
def _cadre_dict(c, db):
    stu = db.query(Student).filter(Student.id == c.student_id).first()
    return {
        'id': c.id, 'student_id': c.student_id,
        'class_name': _get_student_class_name(db, c.student_id),
        'student_name': stu.name if stu else '',
        'student_no': stu.student_no if stu else '',
        'phone': stu.phone if stu else '',
        'position': c.position,
        'level': getattr(c, 'level', '') or '',
        'organization': getattr(c, 'organization', '') or '',
        'term': c.term,
        'start_date': getattr(c, 'start_date', '') or '',
        'end_date': getattr(c, 'end_date', '') or '',
        'email': getattr(c, 'email', '') or '',
        'notes': c.notes,
    }


@router.get('/cadres')
def list_cadres(class_name: Optional[str] = None, level: Optional[str] = None, position: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(StudentCadreRecord)
    if level:
        q = q.filter(StudentCadreRecord.level == level)
    if position:
        q = q.filter(StudentCadreRecord.position.contains(position))
    items = q.order_by(StudentCadreRecord.position).all()
    result = []
    for c in items:
        stu_class_name = _get_student_class_name(db, c.student_id)
        if class_name and stu_class_name != class_name:
            continue
        result.append(_cadre_dict(c, db))
    return result


@router.get('/cadres/directory')
def cadre_directory(db: Session = Depends(get_db)):
    """班委通讯录"""
    from models import ClassModel
    classes = db.query(ClassModel).all()
    result = []
    for cls in classes:
        # 查找该班级的学生干部
        students_in_class = db.query(Student).filter(Student.class_id == cls.id).all()
        student_ids = [s.id for s in students_in_class]
        cadres = db.query(StudentCadreRecord).filter(StudentCadreRecord.student_id.in_(student_ids)).all() if student_ids else []
        teacher = db.query(ClassTeacher).filter(ClassTeacher.class_id == cls.id).first()
        class_data = {'class_name': cls.class_name, 'cadres': [], 'teacher': None}
        for c in cadres:
            stu = db.query(Student).filter(Student.id == c.student_id).first()
            class_data['cadres'].append({
                'position': c.position, 'student_name': stu.name if stu else '',
                'phone': stu.phone if stu else '',
            })
        if teacher:
            class_data['teacher'] = {
                'name': teacher.name, 'phone': teacher.phone, 'office': teacher.office,
            }
        if class_data['cadres'] or class_data['teacher']:
            result.append(class_data)
    return result



@router.get('/cadres/{cadre_id}')
def get_cadre(cadre_id: int, db: Session = Depends(get_db)):
    c = db.query(StudentCadreRecord).filter(StudentCadreRecord.id == cadre_id).first()
    if not c:
        raise HTTPException(404, '记录不存在')
    return _cadre_dict(c, db)


@router.post('/cadres')
def create_cadre(data: dict, db: Session = Depends(get_db)):
    c = StudentCadreRecord(**data)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {'id': c.id}


@router.put('/cadres/{cid}')
def update_cadre(cid: int, data: dict, db: Session = Depends(get_db)):
    c = db.query(StudentCadreRecord).filter(StudentCadreRecord.id == cid).first()
    if not c:
        raise HTTPException(404, '记录不存在')
    for k, v in data.items():
        if hasattr(c, k):
            setattr(c, k, v)
    db.commit()
    return {'ok': True}


@router.delete('/cadres/{cid}')
def delete_cadre(cid: int, db: Session = Depends(get_db)):
    c = db.query(StudentCadreRecord).filter(StudentCadreRecord.id == cid).first()
    if c:
        db.delete(c)
        db.commit()
    return {'ok': True}


# ===== 班主任 =====
@router.get('/class-teachers')
def list_class_teachers(db: Session = Depends(get_db)):
    from models import ClassModel
    items = db.query(ClassTeacher).all()
    result = []
    for t in items:
        cls_name = ''
        if t.class_id:
            cls = db.query(ClassModel).filter(ClassModel.id == t.class_id).first()
            cls_name = cls.class_name if cls else ''
        result.append({
            'id': t.id, 'class_id': t.class_id,
            'class_name': cls_name or getattr(t, 'class_name', ''),
            'name': t.name,
            'staff_no': t.staff_no, 'teacher_no': t.staff_no,  # alias
            'department': t.department,
            'phone': t.phone, 'office': t.office,
            'research_direction': t.research_direction,
            'title': getattr(t, 'title', '') or '',
            'email': getattr(t, 'email', '') or '',
            'notes': t.notes,
        })
    return result


def _teacher_normalize_input(data: dict) -> dict:
    d = dict(data)
    if 'teacher_no' in d and 'staff_no' not in d:
        d['staff_no'] = d.pop('teacher_no')
    allowed = {'class_id','name','staff_no','department','phone','office','research_direction','title','email','notes'}
    return {k: v for k, v in d.items() if k in allowed}


@router.post('/class-teachers')
def create_class_teacher(data: dict, db: Session = Depends(get_db)):
    t = ClassTeacher(**_teacher_normalize_input(data))
    db.add(t)
    db.commit()
    db.refresh(t)
    return {'id': t.id}


@router.put('/class-teachers/{tid}')
def update_class_teacher(tid: int, data: dict, db: Session = Depends(get_db)):
    t = db.query(ClassTeacher).filter(ClassTeacher.id == tid).first()
    if not t:
        raise HTTPException(404, '记录不存在')
    for k, v in _teacher_normalize_input(data).items():
        if hasattr(t, k):
            setattr(t, k, v)
    db.commit()
    return {'ok': True}


@router.delete('/class-teachers/{tid}')
def delete_class_teacher(tid: int, db: Session = Depends(get_db)):
    t = db.query(ClassTeacher).filter(ClassTeacher.id == tid).first()
    if t:
        db.delete(t)
        db.commit()
    return {'ok': True}


# ===== 就业升学 =====
@router.get('/employment')
def list_employment(db: Session = Depends(get_db)):
    items = db.query(EmploymentRecord).order_by(EmploymentRecord.id.desc()).all()
    result = []
    for e in items:
        stu = db.query(Student).filter(Student.id == e.student_id).first()
        result.append({
            'id': e.id, 'student_id': e.student_id,
            'student_name': stu.name if stu else '',
            'class_name': _get_student_class_name(db, e.student_id),
            'intention_type': e.intention_type, 'target_industry': e.target_industry,
            'target_position': e.target_position, 'internship_company': e.internship_company,
            'status': e.status, 'offer_date': e.offer_date,
            'salary_range': e.salary_range, 'notes': e.notes,
        })
    return result


@router.post('/employment')
def create_employment(data: dict, db: Session = Depends(get_db)):
    e = EmploymentRecord(**data)
    db.add(e)
    db.commit()
    db.refresh(e)
    return {'id': e.id}


@router.put('/employment/{eid}')
def update_employment(eid: int, data: dict, db: Session = Depends(get_db)):
    e = db.query(EmploymentRecord).filter(EmploymentRecord.id == eid).first()
    if not e:
        raise HTTPException(404, '记录不存在')
    for k, v in data.items():
        if hasattr(e, k):
            setattr(e, k, v)
    db.commit()
    return {'ok': True}


@router.delete('/employment/{eid}')
def delete_employment(eid: int, db: Session = Depends(get_db)):
    e = db.query(EmploymentRecord).filter(EmploymentRecord.id == eid).first()
    if e:
        db.delete(e)
        db.commit()
    return {'ok': True}
