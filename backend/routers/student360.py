"""学生360主档案 API - V3-A
路由: /api/student360/{student_id}/...
支持12个Tab的就地CRUD
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import (
    Student, ClassModel, Major, Grade,
    GradeRecord, WarningRecord, PartyProgress,
    PsychologyRecord, FamilyContact, StudentCadreRecord,
    Activity, ActivitySignup, EmploymentRecord,
    StudentHardship, StudentGrant, StudentScholarship,
    StudentLoan, StudentWorkStudy, StudentHonor,
    StudentDormVisit, StudentLeave, StudentDiscipline,
    StudentDormChat, StudentAttendanceException,
    StudentStatusChange, Project, ProjectStudent,
    ComprehensiveAssessment
)

router = APIRouter(prefix='/api/student360', tags=['student360'])


# ===== Pydantic Schemas =====

class StudentBase(BaseModel):
    student_no: str
    name: str
    gender: Optional[str] = ''
    class_id: Optional[int] = None
    birth_date: Optional[str] = ''
    political_status: Optional[str] = ''
    phone: Optional[str] = ''
    email: Optional[str] = ''
    parent_phone: Optional[str] = ''
    birth_source: Optional[str] = ''
    notes: Optional[str] = ''


class GradeRecordCreate(BaseModel):
    semester: str
    course_name: str
    score: Optional[float] = None
    gpa: Optional[float] = None
    credit: Optional[float] = None
    is_repair: Optional[bool] = False


class WarningCreate(BaseModel):
    warning_type: str
    description: Optional[str] = ''
    semester: Optional[str] = ''


class PartyProgressCreate(BaseModel):
    stage: str
    stage_date: Optional[str] = ''
    contact_person: Optional[str] = ''
    notes: Optional[str] = ''


class PsychologyRecordCreate(BaseModel):
    record_date: Optional[str] = ''
    location: Optional[str] = ''
    topic: Optional[str] = ''
    summary: Optional[str] = ''
    emotion_tags: Optional[str] = ''
    follow_up_plan: Optional[str] = ''
    next_follow_date: Optional[str] = ''


class FamilyContactCreate(BaseModel):
    contact_date: Optional[str] = ''
    parent_name: Optional[str] = ''
    contact_method: Optional[str] = ''
    topic: Optional[str] = ''
    conclusion: Optional[str] = ''
    attachment: Optional[str] = ''


class CadreRecordCreate(BaseModel):
    position: str
    term: Optional[str] = ''
    notes: Optional[str] = ''


class EmploymentRecordCreate(BaseModel):
    intention_type: Optional[str] = ''
    target_industry: Optional[str] = ''
    target_position: Optional[str] = ''
    internship_company: Optional[str] = ''
    status: Optional[str] = ''
    offer_date: Optional[str] = ''
    salary_range: Optional[str] = ''
    notes: Optional[str] = ''


class HardshipCreate(BaseModel):
    hardship_level: Optional[str] = ''
    academic_year: Optional[str] = ''
    evidence: Optional[str] = ''
    notes: Optional[str] = ''


class GrantCreate(BaseModel):
    grant_type: Optional[str] = ''
    amount: Optional[float] = 0
    academic_year: Optional[str] = ''
    notes: Optional[str] = ''


class ScholarshipCreate(BaseModel):
    scholarship_type: Optional[str] = ''
    amount: Optional[float] = 0
    academic_year: Optional[str] = ''
    notes: Optional[str] = ''


class LoanCreate(BaseModel):
    loan_type: Optional[str] = ''
    amount: Optional[float] = 0
    duration: Optional[str] = ''
    status: Optional[str] = ''
    notes: Optional[str] = ''


class WorkStudyCreate(BaseModel):
    position: Optional[str] = ''
    hours: Optional[float] = 0
    compensation: Optional[float] = 0
    academic_year: Optional[str] = ''
    notes: Optional[str] = ''


class HonorCreate(BaseModel):
    honor_name: Optional[str] = ''
    academic_year: Optional[str] = ''
    level: Optional[str] = ''
    notes: Optional[str] = ''


class DormVisitCreate(BaseModel):
    visit_date: Optional[str] = ''
    dorm_room: Optional[str] = ''
    visitor: Optional[str] = ''
    situation: Optional[str] = ''
    notes: Optional[str] = ''


class LeaveCreate(BaseModel):
    leave_type: Optional[str] = ''
    start_date: Optional[str] = ''
    end_date: Optional[str] = ''
    destination: Optional[str] = ''
    approval_status: Optional[str] = 'pending'
    approver: Optional[str] = ''
    notes: Optional[str] = ''


class DisciplineCreate(BaseModel):
    discipline_date: Optional[str] = ''
    discipline_type: Optional[str] = ''
    level: Optional[str] = ''
    reason: Optional[str] = ''
    attachment: Optional[str] = ''
    notes: Optional[str] = ''


class DormChatCreate(BaseModel):
    chat_date: Optional[str] = ''
    topic: Optional[str] = ''
    key_points: Optional[str] = ''
    follow_up: Optional[str] = ''


class AttendanceExceptionCreate(BaseModel):
    exception_date: Optional[str] = ''
    course_name: Optional[str] = ''
    exception_type: Optional[str] = ''
    notes: Optional[str] = ''


class StatusChangeCreate(BaseModel):
    change_type: str
    start_date: Optional[str] = ''
    end_date: Optional[str] = ''
    reason: Optional[str] = ''
    original_info: Optional[str] = ''
    target_info: Optional[str] = ''
    attachment: Optional[str] = ''
    notes: Optional[str] = ''


class ProjectStudentCreate(BaseModel):
    project_id: int
    progress: Optional[int] = 0
    material_status: Optional[str] = 'pending'
    notes: Optional[str] = ''


# ===== Helper: Get student with class info =====

def get_student_with_class(db: Session, student_id: int):
    """获取学生信息，包含班级/专业/年级"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    result = {
        'id': student.id,
        'student_no': student.student_no,
        'name': student.name,
        'gender': student.gender,
        'birth_date': student.birth_date,
        'political_status': student.political_status,
        'phone': student.phone,
        'email': student.email,
        'parent_phone': student.parent_phone,
        'birth_source': student.birth_source,
        'id_card': student.id_card,
        'campus': student.campus,
        'dorm_building': student.dorm_building,
        'dorm_room': student.dorm_room,
        'is_off_campus': student.is_off_campus,
        'off_campus_address': student.off_campus_address,
        'notes': student.notes,
        'class_id': student.class_id,
        'class_name': '',
        'major_name': '',
        'grade_name': '',
    }

    if student.class_obj:
        result['class_name'] = student.class_obj.class_name
        if student.class_obj.major:
            result['major_name'] = student.class_obj.major.major_name
            if student.class_obj.major.grade:
                result['grade_name'] = student.class_obj.major.grade.grade_name

    return result


def to_dict(obj, fields):
    """将 SQLAlchemy 对象转为字典"""
    result = {}
    for f in fields:
        val = getattr(obj, f, None)
        if isinstance(val, datetime):
            result[f] = val.isoformat()
        else:
            result[f] = val
    return result


# ===== 0. 获取学生360概要 =====

@router.get('/{student_id}/summary')
def get_student_summary(student_id: int, db: Session = Depends(get_db)):
    """获取学生360概要信息（顶部信息卡）"""
    student_data = get_student_with_class(db, student_id)
    student = db.query(Student).filter(Student.id == student_id).first()

    # 核心状态灯
    # 学业预警
    warnings = db.query(WarningRecord).filter(WarningRecord.student_id == student_id).all()
    warning_status = 'green'
    for w in warnings:
        if w.warning_type == 'red':
            warning_status = 'red'
            break
        elif w.warning_type == 'yellow' and warning_status != 'red':
            warning_status = 'yellow'

    # 党团进度
    party = db.query(PartyProgress).filter(PartyProgress.student_id == student_id)\
        .order_by(desc(PartyProgress.id)).first()
    party_stage = party.stage if party else '群众'

    # 心理关注
    psych_count = db.query(PsychologyRecord).filter(PsychologyRecord.student_id == student_id).count()
    psych_status = 'normal' if psych_count == 0 else 'attention'

    # 就业状态
    employment = db.query(EmploymentRecord).filter(EmploymentRecord.student_id == student_id).first()
    employment_status = employment.status if employment else '未登记'

    # 资助等级
    hardship = db.query(StudentHardship).filter(StudentHardship.student_id == student_id).first()
    hardship_level = hardship.hardship_level if hardship else '无'

    # 统计
    stats = {
        'grade_count': db.query(GradeRecord).filter(GradeRecord.student_id == student_id).count(),
        'warning_count': len(warnings),
        'party_stage': party_stage,
        'psych_count': psych_count,
        'family_contact_count': db.query(FamilyContact).filter(FamilyContact.student_id == student_id).count(),
        'cadre_count': db.query(StudentCadreRecord).filter(StudentCadreRecord.student_id == student_id).count(),
        'activity_count': db.query(ActivitySignup).filter(ActivitySignup.student_id == student_id).count(),
        'employment_status': employment_status,
        'hardship_level': hardship_level,
        'honor_count': db.query(StudentHonor).filter(StudentHonor.student_id == student_id).count(),
        'leave_count': db.query(StudentLeave).filter(StudentLeave.student_id == student_id).count(),
        'discipline_count': db.query(StudentDiscipline).filter(StudentDiscipline.student_id == student_id).count(),
        'status_change_count': db.query(StudentStatusChange).filter(StudentStatusChange.student_id == student_id).count(),
        'project_count': db.query(ProjectStudent).filter(ProjectStudent.student_id == student_id).count(),
    }

    return {
        **student_data,
        'warning_status': warning_status,
        'psych_status': psych_status,
        'stats': stats,
    }


# ===== 1. 基本信息 (含学籍异动) =====

@router.get('/{student_id}/basic')
def get_basic_info(student_id: int, db: Session = Depends(get_db)):
    """获取基本信息"""
    return get_student_with_class(db, student_id)


@router.put('/{student_id}/basic')
def update_basic_info(student_id: int, data: StudentBase, db: Session = Depends(get_db)):
    """更新基本信息"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    for key, value in data.dict().items():
        if hasattr(student, key):
            setattr(student, key, value)

    db.commit()
    return get_student_with_class(db, student_id)


@router.get('/{student_id}/status-changes')
def get_status_changes(student_id: int, db: Session = Depends(get_db)):
    """获取学籍异动列表"""
    records = db.query(StudentStatusChange).filter(
        StudentStatusChange.student_id == student_id
    ).order_by(desc(StudentStatusChange.id)).all()
    return [to_dict(r, ['id', 'student_id', 'change_type', 'start_date', 'end_date',
                        'reason', 'original_info', 'target_info', 'attachment', 'notes', 'created_at'])
            for r in records]


@router.post('/{student_id}/status-changes')
def create_status_change(student_id: int, data: StatusChangeCreate, db: Session = Depends(get_db)):
    """新增学籍异动"""
    record = StudentStatusChange(student_id=student_id, **data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'change_type', 'start_date', 'end_date',
                            'reason', 'original_info', 'target_info', 'notes', 'created_at'])


@router.put('/{student_id}/status-changes/{record_id}')
def update_status_change(student_id: int, record_id: int, data: StatusChangeCreate, db: Session = Depends(get_db)):
    """编辑学籍异动"""
    record = db.query(StudentStatusChange).filter(
        StudentStatusChange.id == record_id,
        StudentStatusChange.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, value in data.dict().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'change_type', 'start_date', 'end_date',
                            'reason', 'original_info', 'target_info', 'notes', 'created_at'])


@router.delete('/{student_id}/status-changes/{record_id}')
def delete_status_change(student_id: int, record_id: int, db: Session = Depends(get_db)):
    """删除学籍异动"""
    record = db.query(StudentStatusChange).filter(
        StudentStatusChange.id == record_id,
        StudentStatusChange.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {'message': '删除成功'}


# ===== 2. 学业情况 =====

@router.get('/{student_id}/grades')
def get_grades(student_id: int, db: Session = Depends(get_db)):
    """获取成绩列表"""
    records = db.query(GradeRecord).filter(
        GradeRecord.student_id == student_id
    ).order_by(desc(GradeRecord.semester), GradeRecord.course_name).all()
    return [to_dict(r, ['id', 'student_id', 'semester', 'course_name', 'score', 'gpa', 'credit', 'is_repair', 'created_at'])
            for r in records]


@router.post('/{student_id}/grades')
def create_grade(student_id: int, data: GradeRecordCreate, db: Session = Depends(get_db)):
    """新增成绩"""
    record = GradeRecord(student_id=student_id, **data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'semester', 'course_name', 'score', 'gpa', 'credit', 'is_repair', 'created_at'])


@router.put('/{student_id}/grades/{record_id}')
def update_grade(student_id: int, record_id: int, data: GradeRecordCreate, db: Session = Depends(get_db)):
    """编辑成绩"""
    record = db.query(GradeRecord).filter(
        GradeRecord.id == record_id,
        GradeRecord.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, value in data.dict().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'semester', 'course_name', 'score', 'gpa', 'credit', 'is_repair', 'created_at'])


@router.delete('/{student_id}/grades/{record_id}')
def delete_grade(student_id: int, record_id: int, db: Session = Depends(get_db)):
    """删除成绩"""
    record = db.query(GradeRecord).filter(
        GradeRecord.id == record_id,
        GradeRecord.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {'message': '删除成功'}


# ===== 3. 党团发展 =====

@router.get('/{student_id}/party')
def get_party_progress(student_id: int, db: Session = Depends(get_db)):
    """获取党团发展记录"""
    records = db.query(PartyProgress).filter(
        PartyProgress.student_id == student_id
    ).order_by(PartyProgress.id).all()
    return [to_dict(r, ['id', 'student_id', 'stage', 'stage_date', 'contact_person', 'notes', 'created_at'])
            for r in records]


@router.post('/{student_id}/party')
def create_party_progress(student_id: int, data: PartyProgressCreate, db: Session = Depends(get_db)):
    """新增党团发展记录"""
    record = PartyProgress(student_id=student_id, **data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'stage', 'stage_date', 'contact_person', 'notes', 'created_at'])


@router.put('/{student_id}/party/{record_id}')
def update_party_progress(student_id: int, record_id: int, data: PartyProgressCreate, db: Session = Depends(get_db)):
    """编辑党团发展记录"""
    record = db.query(PartyProgress).filter(
        PartyProgress.id == record_id,
        PartyProgress.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, value in data.dict().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'stage', 'stage_date', 'contact_person', 'notes', 'created_at'])


@router.delete('/{student_id}/party/{record_id}')
def delete_party_progress(student_id: int, record_id: int, db: Session = Depends(get_db)):
    """删除党团发展记录"""
    record = db.query(PartyProgress).filter(
        PartyProgress.id == record_id,
        PartyProgress.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {'message': '删除成功'}


# ===== 4. 心理档案 =====

@router.get('/{student_id}/psychology')
def get_psychology(student_id: int, db: Session = Depends(get_db)):
    """获取心理档案"""
    records = db.query(PsychologyRecord).filter(
        PsychologyRecord.student_id == student_id
    ).order_by(desc(PsychologyRecord.id)).all()
    return [to_dict(r, ['id', 'student_id', 'record_date', 'location', 'topic', 'summary',
                        'emotion_tags', 'follow_up_plan', 'next_follow_date', 'created_at'])
            for r in records]


@router.post('/{student_id}/psychology')
def create_psychology(student_id: int, data: PsychologyRecordCreate, db: Session = Depends(get_db)):
    """新增心理档案"""
    record = PsychologyRecord(student_id=student_id, **data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'record_date', 'location', 'topic', 'summary',
                            'emotion_tags', 'follow_up_plan', 'next_follow_date', 'created_at'])


@router.put('/{student_id}/psychology/{record_id}')
def update_psychology(student_id: int, record_id: int, data: PsychologyRecordCreate, db: Session = Depends(get_db)):
    record = db.query(PsychologyRecord).filter(
        PsychologyRecord.id == record_id, PsychologyRecord.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, value in data.dict().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'record_date', 'location', 'topic', 'summary',
                            'emotion_tags', 'follow_up_plan', 'next_follow_date', 'created_at'])


@router.delete('/{student_id}/psychology/{record_id}')
def delete_psychology(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(PsychologyRecord).filter(
        PsychologyRecord.id == record_id, PsychologyRecord.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {'message': '删除成功'}


# ===== 5. 家庭联络 =====

@router.get('/{student_id}/family')
def get_family_contacts(student_id: int, db: Session = Depends(get_db)):
    records = db.query(FamilyContact).filter(
        FamilyContact.student_id == student_id
    ).order_by(desc(FamilyContact.id)).all()
    return [to_dict(r, ['id', 'student_id', 'contact_date', 'parent_name', 'contact_method',
                        'topic', 'conclusion', 'attachment', 'created_at'])
            for r in records]


@router.post('/{student_id}/family')
def create_family_contact(student_id: int, data: FamilyContactCreate, db: Session = Depends(get_db)):
    record = FamilyContact(student_id=student_id, **data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'contact_date', 'parent_name', 'contact_method',
                            'topic', 'conclusion', 'attachment', 'created_at'])


@router.put('/{student_id}/family/{record_id}')
def update_family_contact(student_id: int, record_id: int, data: FamilyContactCreate, db: Session = Depends(get_db)):
    record = db.query(FamilyContact).filter(
        FamilyContact.id == record_id, FamilyContact.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, value in data.dict().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'contact_date', 'parent_name', 'contact_method',
                            'topic', 'conclusion', 'attachment', 'created_at'])


@router.delete('/{student_id}/family/{record_id}')
def delete_family_contact(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(FamilyContact).filter(
        FamilyContact.id == record_id, FamilyContact.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {'message': '删除成功'}


# ===== 6. 学生工作 =====

@router.get('/{student_id}/cadres')
def get_cadres(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentCadreRecord).filter(
        StudentCadreRecord.student_id == student_id
    ).order_by(desc(StudentCadreRecord.id)).all()
    return [to_dict(r, ['id', 'student_id', 'position', 'term', 'notes', 'created_at'])
            for r in records]


@router.post('/{student_id}/cadres')
def create_cadre(student_id: int, data: CadreRecordCreate, db: Session = Depends(get_db)):
    record = StudentCadreRecord(student_id=student_id, **data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'position', 'term', 'notes', 'created_at'])


@router.put('/{student_id}/cadres/{record_id}')
def update_cadre(student_id: int, record_id: int, data: CadreRecordCreate, db: Session = Depends(get_db)):
    record = db.query(StudentCadreRecord).filter(
        StudentCadreRecord.id == record_id, StudentCadreRecord.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, value in data.dict().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'position', 'term', 'notes', 'created_at'])


@router.delete('/{student_id}/cadres/{record_id}')
def delete_cadre(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentCadreRecord).filter(
        StudentCadreRecord.id == record_id, StudentCadreRecord.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {'message': '删除成功'}


# ===== 7. 活动参与 =====

@router.get('/{student_id}/activities')
def get_activities(student_id: int, db: Session = Depends(get_db)):
    signups = db.query(ActivitySignup).filter(
        ActivitySignup.student_id == student_id
    ).order_by(desc(ActivitySignup.id)).all()

    result = []
    for s in signups:
        activity = db.query(Activity).filter(Activity.id == s.activity_id).first()
        result.append({
            'id': s.id,
            'activity_id': s.activity_id,
            'student_id': s.student_id,
            'signed_up': s.signed_up,
            'checked_in': s.checked_in,
            'points': s.points,
            'created_at': s.created_at.isoformat() if s.created_at else '',
            'activity_title': activity.title if activity else '',
            'activity_date': activity.activity_date if activity else '',
            'activity_type': activity.activity_type if activity else '',
            'location': activity.location if activity else '',
        })
    return result


@router.post('/{student_id}/activities')
def create_activity_signup(student_id: int, activity_id: int = Query(...), db: Session = Depends(get_db)):
    """报名活动"""
    existing = db.query(ActivitySignup).filter(
        ActivitySignup.student_id == student_id,
        ActivitySignup.activity_id == activity_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已报名该活动")

    signup = ActivitySignup(student_id=student_id, activity_id=activity_id)
    db.add(signup)
    db.commit()
    db.refresh(signup)
    return {'id': signup.id, 'activity_id': signup.activity_id, 'student_id': signup.student_id}


@router.delete('/{student_id}/activities/{record_id}')
def delete_activity_signup(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(ActivitySignup).filter(
        ActivitySignup.id == record_id, ActivitySignup.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {'message': '删除成功'}


# ===== 8. 就业信息 =====

@router.get('/{student_id}/employment')
def get_employment(student_id: int, db: Session = Depends(get_db)):
    records = db.query(EmploymentRecord).filter(
        EmploymentRecord.student_id == student_id
    ).order_by(desc(EmploymentRecord.id)).all()
    return [to_dict(r, ['id', 'student_id', 'intention_type', 'target_industry', 'target_position',
                        'internship_company', 'status', 'offer_date', 'salary_range', 'notes', 'created_at'])
            for r in records]


@router.post('/{student_id}/employment')
def create_employment(student_id: int, data: EmploymentRecordCreate, db: Session = Depends(get_db)):
    record = EmploymentRecord(student_id=student_id, **data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'intention_type', 'target_industry', 'target_position',
                            'internship_company', 'status', 'offer_date', 'salary_range', 'notes', 'created_at'])


@router.put('/{student_id}/employment/{record_id}')
def update_employment(student_id: int, record_id: int, data: EmploymentRecordCreate, db: Session = Depends(get_db)):
    record = db.query(EmploymentRecord).filter(
        EmploymentRecord.id == record_id, EmploymentRecord.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, value in data.dict().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'intention_type', 'target_industry', 'target_position',
                            'internship_company', 'status', 'offer_date', 'salary_range', 'notes', 'created_at'])


@router.delete('/{student_id}/employment/{record_id}')
def delete_employment(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(EmploymentRecord).filter(
        EmploymentRecord.id == record_id, EmploymentRecord.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {'message': '删除成功'}


# ===== 9. 资助与荣誉 (6子模块) =====

# 9.1 困难认定
@router.get('/{student_id}/hardship')
def get_hardship(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentHardship).filter(StudentHardship.student_id == student_id).order_by(desc(StudentHardship.id)).all()
    return [to_dict(r, ['id', 'student_id', 'hardship_level', 'academic_year', 'evidence', 'notes', 'created_at']) for r in records]

@router.post('/{student_id}/hardship')
def create_hardship(student_id: int, data: HardshipCreate, db: Session = Depends(get_db)):
    record = StudentHardship(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'hardship_level', 'academic_year', 'evidence', 'notes', 'created_at'])

@router.put('/{student_id}/hardship/{record_id}')
def update_hardship(student_id: int, record_id: int, data: HardshipCreate, db: Session = Depends(get_db)):
    record = db.query(StudentHardship).filter(StudentHardship.id == record_id, StudentHardship.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'hardship_level', 'academic_year', 'evidence', 'notes', 'created_at'])

@router.delete('/{student_id}/hardship/{record_id}')
def delete_hardship(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentHardship).filter(StudentHardship.id == record_id, StudentHardship.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# 9.2 助学金
@router.get('/{student_id}/grants')
def get_grants(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentGrant).filter(StudentGrant.student_id == student_id).order_by(desc(StudentGrant.id)).all()
    return [to_dict(r, ['id', 'student_id', 'grant_type', 'amount', 'academic_year', 'notes', 'created_at']) for r in records]

@router.post('/{student_id}/grants')
def create_grant(student_id: int, data: GrantCreate, db: Session = Depends(get_db)):
    record = StudentGrant(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'grant_type', 'amount', 'academic_year', 'notes', 'created_at'])

@router.put('/{student_id}/grants/{record_id}')
def update_grant(student_id: int, record_id: int, data: GrantCreate, db: Session = Depends(get_db)):
    record = db.query(StudentGrant).filter(StudentGrant.id == record_id, StudentGrant.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'grant_type', 'amount', 'academic_year', 'notes', 'created_at'])

@router.delete('/{student_id}/grants/{record_id}')
def delete_grant(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentGrant).filter(StudentGrant.id == record_id, StudentGrant.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# 9.3 奖学金
@router.get('/{student_id}/scholarships')
def get_scholarships(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentScholarship).filter(StudentScholarship.student_id == student_id).order_by(desc(StudentScholarship.id)).all()
    return [to_dict(r, ['id', 'student_id', 'scholarship_type', 'amount', 'academic_year', 'notes', 'created_at']) for r in records]

@router.post('/{student_id}/scholarships')
def create_scholarship(student_id: int, data: ScholarshipCreate, db: Session = Depends(get_db)):
    record = StudentScholarship(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'scholarship_type', 'amount', 'academic_year', 'notes', 'created_at'])

@router.put('/{student_id}/scholarships/{record_id}')
def update_scholarship(student_id: int, record_id: int, data: ScholarshipCreate, db: Session = Depends(get_db)):
    record = db.query(StudentScholarship).filter(StudentScholarship.id == record_id, StudentScholarship.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'scholarship_type', 'amount', 'academic_year', 'notes', 'created_at'])

@router.delete('/{student_id}/scholarships/{record_id}')
def delete_scholarship(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentScholarship).filter(StudentScholarship.id == record_id, StudentScholarship.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# 9.4 助学贷款
@router.get('/{student_id}/loans')
def get_loans(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentLoan).filter(StudentLoan.student_id == student_id).order_by(desc(StudentLoan.id)).all()
    return [to_dict(r, ['id', 'student_id', 'loan_type', 'amount', 'duration', 'status', 'notes', 'created_at']) for r in records]

@router.post('/{student_id}/loans')
def create_loan(student_id: int, data: LoanCreate, db: Session = Depends(get_db)):
    record = StudentLoan(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'loan_type', 'amount', 'duration', 'status', 'notes', 'created_at'])

@router.put('/{student_id}/loans/{record_id}')
def update_loan(student_id: int, record_id: int, data: LoanCreate, db: Session = Depends(get_db)):
    record = db.query(StudentLoan).filter(StudentLoan.id == record_id, StudentLoan.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'loan_type', 'amount', 'duration', 'status', 'notes', 'created_at'])

@router.delete('/{student_id}/loans/{record_id}')
def delete_loan(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentLoan).filter(StudentLoan.id == record_id, StudentLoan.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# 9.5 勤工助学
@router.get('/{student_id}/work-study')
def get_work_study(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentWorkStudy).filter(StudentWorkStudy.student_id == student_id).order_by(desc(StudentWorkStudy.id)).all()
    return [to_dict(r, ['id', 'student_id', 'position', 'hours', 'compensation', 'academic_year', 'notes', 'created_at']) for r in records]

@router.post('/{student_id}/work-study')
def create_work_study(student_id: int, data: WorkStudyCreate, db: Session = Depends(get_db)):
    record = StudentWorkStudy(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'position', 'hours', 'compensation', 'academic_year', 'notes', 'created_at'])

@router.put('/{student_id}/work-study/{record_id}')
def update_work_study(student_id: int, record_id: int, data: WorkStudyCreate, db: Session = Depends(get_db)):
    record = db.query(StudentWorkStudy).filter(StudentWorkStudy.id == record_id, StudentWorkStudy.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'position', 'hours', 'compensation', 'academic_year', 'notes', 'created_at'])

@router.delete('/{student_id}/work-study/{record_id}')
def delete_work_study(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentWorkStudy).filter(StudentWorkStudy.id == record_id, StudentWorkStudy.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# 9.6 评优评先
@router.get('/{student_id}/honors')
def get_honors(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentHonor).filter(StudentHonor.student_id == student_id).order_by(desc(StudentHonor.id)).all()
    return [to_dict(r, ['id', 'student_id', 'honor_name', 'academic_year', 'level', 'notes', 'created_at']) for r in records]

@router.post('/{student_id}/honors')
def create_honor(student_id: int, data: HonorCreate, db: Session = Depends(get_db)):
    record = StudentHonor(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'honor_name', 'academic_year', 'level', 'notes', 'created_at'])

@router.put('/{student_id}/honors/{record_id}')
def update_honor(student_id: int, record_id: int, data: HonorCreate, db: Session = Depends(get_db)):
    record = db.query(StudentHonor).filter(StudentHonor.id == record_id, StudentHonor.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'honor_name', 'academic_year', 'level', 'notes', 'created_at'])

@router.delete('/{student_id}/honors/{record_id}')
def delete_honor(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentHonor).filter(StudentHonor.id == record_id, StudentHonor.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# ===== 10. 日常管理 (5子模块) =====

# 10.1 宿舍走访
@router.get('/{student_id}/dorm-visits')
def get_dorm_visits(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentDormVisit).filter(StudentDormVisit.student_id == student_id).order_by(desc(StudentDormVisit.id)).all()
    return [to_dict(r, ['id', 'student_id', 'visit_date', 'dorm_room', 'visitor', 'situation', 'notes', 'created_at']) for r in records]

@router.post('/{student_id}/dorm-visits')
def create_dorm_visit(student_id: int, data: DormVisitCreate, db: Session = Depends(get_db)):
    record = StudentDormVisit(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'visit_date', 'dorm_room', 'visitor', 'situation', 'notes', 'created_at'])

@router.put('/{student_id}/dorm-visits/{record_id}')
def update_dorm_visit(student_id: int, record_id: int, data: DormVisitCreate, db: Session = Depends(get_db)):
    record = db.query(StudentDormVisit).filter(StudentDormVisit.id == record_id, StudentDormVisit.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'visit_date', 'dorm_room', 'visitor', 'situation', 'notes', 'created_at'])

@router.delete('/{student_id}/dorm-visits/{record_id}')
def delete_dorm_visit(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentDormVisit).filter(StudentDormVisit.id == record_id, StudentDormVisit.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# 10.2 请假记录
@router.get('/{student_id}/leaves')
def get_leaves(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentLeave).filter(StudentLeave.student_id == student_id).order_by(desc(StudentLeave.id)).all()
    return [to_dict(r, ['id', 'student_id', 'leave_type', 'start_date', 'end_date', 'destination', 'approval_status', 'approver', 'notes', 'created_at']) for r in records]

@router.post('/{student_id}/leaves')
def create_leave(student_id: int, data: LeaveCreate, db: Session = Depends(get_db)):
    record = StudentLeave(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'leave_type', 'start_date', 'end_date', 'destination', 'approval_status', 'approver', 'notes', 'created_at'])

@router.put('/{student_id}/leaves/{record_id}')
def update_leave(student_id: int, record_id: int, data: LeaveCreate, db: Session = Depends(get_db)):
    record = db.query(StudentLeave).filter(StudentLeave.id == record_id, StudentLeave.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'leave_type', 'start_date', 'end_date', 'destination', 'approval_status', 'approver', 'notes', 'created_at'])

@router.delete('/{student_id}/leaves/{record_id}')
def delete_leave(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentLeave).filter(StudentLeave.id == record_id, StudentLeave.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# 10.3 违纪处分
@router.get('/{student_id}/disciplines')
def get_disciplines(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentDiscipline).filter(StudentDiscipline.student_id == student_id).order_by(desc(StudentDiscipline.id)).all()
    return [to_dict(r, ['id', 'student_id', 'discipline_date', 'discipline_type', 'level', 'reason', 'attachment', 'notes', 'created_at']) for r in records]

@router.post('/{student_id}/disciplines')
def create_discipline(student_id: int, data: DisciplineCreate, db: Session = Depends(get_db)):
    record = StudentDiscipline(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'discipline_date', 'discipline_type', 'level', 'reason', 'attachment', 'notes', 'created_at'])

@router.put('/{student_id}/disciplines/{record_id}')
def update_discipline(student_id: int, record_id: int, data: DisciplineCreate, db: Session = Depends(get_db)):
    record = db.query(StudentDiscipline).filter(StudentDiscipline.id == record_id, StudentDiscipline.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'discipline_date', 'discipline_type', 'level', 'reason', 'attachment', 'notes', 'created_at'])

@router.delete('/{student_id}/disciplines/{record_id}')
def delete_discipline(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentDiscipline).filter(StudentDiscipline.id == record_id, StudentDiscipline.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# 10.4 寝谈记录
@router.get('/{student_id}/dorm-chats')
def get_dorm_chats(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentDormChat).filter(StudentDormChat.student_id == student_id).order_by(desc(StudentDormChat.id)).all()
    return [to_dict(r, ['id', 'student_id', 'chat_date', 'topic', 'key_points', 'follow_up', 'created_at']) for r in records]

@router.post('/{student_id}/dorm-chats')
def create_dorm_chat(student_id: int, data: DormChatCreate, db: Session = Depends(get_db)):
    record = StudentDormChat(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'chat_date', 'topic', 'key_points', 'follow_up', 'created_at'])

@router.put('/{student_id}/dorm-chats/{record_id}')
def update_dorm_chat(student_id: int, record_id: int, data: DormChatCreate, db: Session = Depends(get_db)):
    record = db.query(StudentDormChat).filter(StudentDormChat.id == record_id, StudentDormChat.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'chat_date', 'topic', 'key_points', 'follow_up', 'created_at'])

@router.delete('/{student_id}/dorm-chats/{record_id}')
def delete_dorm_chat(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentDormChat).filter(StudentDormChat.id == record_id, StudentDormChat.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# 10.5 考勤异常
@router.get('/{student_id}/attendance')
def get_attendance(student_id: int, db: Session = Depends(get_db)):
    records = db.query(StudentAttendanceException).filter(StudentAttendanceException.student_id == student_id).order_by(desc(StudentAttendanceException.id)).all()
    return [to_dict(r, ['id', 'student_id', 'exception_date', 'course_name', 'exception_type', 'notes', 'created_at']) for r in records]

@router.post('/{student_id}/attendance')
def create_attendance(student_id: int, data: AttendanceExceptionCreate, db: Session = Depends(get_db)):
    record = StudentAttendanceException(student_id=student_id, **data.dict())
    db.add(record); db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'exception_date', 'course_name', 'exception_type', 'notes', 'created_at'])

@router.put('/{student_id}/attendance/{record_id}')
def update_attendance(student_id: int, record_id: int, data: AttendanceExceptionCreate, db: Session = Depends(get_db)):
    record = db.query(StudentAttendanceException).filter(StudentAttendanceException.id == record_id, StudentAttendanceException.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items(): setattr(record, k, v)
    db.commit(); db.refresh(record)
    return to_dict(record, ['id', 'student_id', 'exception_date', 'course_name', 'exception_type', 'notes', 'created_at'])

@router.delete('/{student_id}/attendance/{record_id}')
def delete_attendance(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(StudentAttendanceException).filter(StudentAttendanceException.id == record_id, StudentAttendanceException.student_id == student_id).first()
    if not record: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record); db.commit()
    return {'message': '删除成功'}


# ===== 11. 专项工作 =====

@router.get('/{student_id}/projects')
def get_projects(student_id: int, db: Session = Depends(get_db)):
    """获取学生关联的专项工作"""
    ps_records = db.query(ProjectStudent).filter(
        ProjectStudent.student_id == student_id
    ).order_by(desc(ProjectStudent.id)).all()

    result = []
    for ps in ps_records:
        project = db.query(Project).filter(Project.id == ps.project_id).first()
        result.append({
            'id': ps.id,
            'project_id': ps.project_id,
            'student_id': ps.student_id,
            'progress': ps.progress,
            'material_status': ps.material_status,
            'notes': ps.notes,
            'created_at': ps.created_at.isoformat() if ps.created_at else '',
            'project_name': project.name if project else '',
            'project_status': project.status if project else '',
            'project_start': project.start_date if project else '',
            'project_end': project.end_date if project else '',
        })
    return result


@router.post('/{student_id}/projects')
def create_project_student(student_id: int, data: ProjectStudentCreate, db: Session = Depends(get_db)):
    record = ProjectStudent(student_id=student_id, **data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {'id': record.id, 'project_id': record.project_id, 'student_id': record.student_id}


@router.put('/{student_id}/projects/{record_id}')
def update_project_student(student_id: int, record_id: int, data: ProjectStudentCreate, db: Session = Depends(get_db)):
    record = db.query(ProjectStudent).filter(
        ProjectStudent.id == record_id, ProjectStudent.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.dict().items():
        setattr(record, k, v)
    db.commit()
    db.refresh(record)
    return {'id': record.id, 'project_id': record.project_id, 'student_id': record.student_id}


@router.delete('/{student_id}/projects/{record_id}')
def delete_project_student(student_id: int, record_id: int, db: Session = Depends(get_db)):
    record = db.query(ProjectStudent).filter(
        ProjectStudent.id == record_id, ProjectStudent.student_id == student_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {'message': '删除成功'}


# ===== 12. 时间线 =====

@router.get('/{student_id}/timeline')
def get_timeline(student_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """跨维度按时间倒序聚合展示"""
    timeline = []

    # 成绩
    grades = db.query(GradeRecord).filter(GradeRecord.student_id == student_id).all()
    for g in grades:
        timeline.append({
            'type': 'grade', 'icon': '📊', 'title': f'{g.course_name}',
            'subtitle': f'{g.semester} | 成绩: {g.score} | 绩点: {g.gpa}',
            'date': g.semester, 'created_at': g.created_at.isoformat() if g.created_at else ''
        })

    # 预警
    warnings = db.query(WarningRecord).filter(WarningRecord.student_id == student_id).all()
    for w in warnings:
        timeline.append({
            'type': 'warning', 'icon': '🚨', 'title': f'学业预警 ({w.warning_type})',
            'subtitle': w.description, 'date': w.semester,
            'created_at': w.created_at.isoformat() if w.created_at else ''
        })

    # 党团
    party = db.query(PartyProgress).filter(PartyProgress.student_id == student_id).all()
    for p in party:
        timeline.append({
            'type': 'party', 'icon': '🎯', 'title': f'党团发展: {p.stage}',
            'subtitle': p.notes, 'date': p.stage_date,
            'created_at': p.created_at.isoformat() if p.created_at else ''
        })

    # 心理
    psych = db.query(PsychologyRecord).filter(PsychologyRecord.student_id == student_id).all()
    for p in psych:
        timeline.append({
            'type': 'psychology', 'icon': '💚', 'title': f'心理关怀: {p.topic}',
            'subtitle': p.summary[:50] if p.summary else '', 'date': p.record_date,
            'created_at': p.created_at.isoformat() if p.created_at else ''
        })

    # 家庭
    family = db.query(FamilyContact).filter(FamilyContact.student_id == student_id).all()
    for f in family:
        timeline.append({
            'type': 'family', 'icon': '🏠', 'title': f'家校沟通: {f.topic}',
            'subtitle': f'联系人: {f.parent_name} | 方式: {f.contact_method}',
            'date': f.contact_date, 'created_at': f.created_at.isoformat() if f.created_at else ''
        })

    # 学籍异动
    changes = db.query(StudentStatusChange).filter(StudentStatusChange.student_id == student_id).all()
    for c in changes:
        timeline.append({
            'type': 'status_change', 'icon': '🔄', 'title': f'学籍异动: {c.change_type}',
            'subtitle': c.reason, 'date': c.start_date,
            'created_at': c.created_at.isoformat() if c.created_at else ''
        })

    # 请假
    leaves = db.query(StudentLeave).filter(StudentLeave.student_id == student_id).all()
    for l in leaves:
        timeline.append({
            'type': 'leave', 'icon': '📝', 'title': f'请假: {l.leave_type}',
            'subtitle': f'{l.start_date} ~ {l.end_date} | 去向: {l.destination}',
            'date': l.start_date, 'created_at': l.created_at.isoformat() if l.created_at else ''
        })

    # 违纪
    disciplines = db.query(StudentDiscipline).filter(StudentDiscipline.student_id == student_id).all()
    for d in disciplines:
        timeline.append({
            'type': 'discipline', 'icon': '⚠️', 'title': f'违纪处分: {d.discipline_type}',
            'subtitle': d.reason, 'date': d.discipline_date,
            'created_at': d.created_at.isoformat() if d.created_at else ''
        })

    # 荣誉
    honors = db.query(StudentHonor).filter(StudentHonor.student_id == student_id).all()
    for h in honors:
        timeline.append({
            'type': 'honor', 'icon': '🏆', 'title': f'荣誉: {h.honor_name}',
            'subtitle': f'{h.level} | {h.academic_year}',
            'date': h.academic_year, 'created_at': h.created_at.isoformat() if h.created_at else ''
        })

    # 按 created_at 排序
    timeline.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return timeline[:limit]


# ===== 13. 成长轨迹雷达图 =====

@router.get('/{student_id}/radar')
def get_radar(student_id: int, db: Session = Depends(get_db)):
    """成长轨迹雷达图 - 6维度0-100评分"""
    # 1. 学业成绩 - 基于GPA均值映射到0-100
    grade_records = db.query(GradeRecord).filter(GradeRecord.student_id == student_id).all()
    if grade_records:
        gpas = [g.gpa for g in grade_records if g.gpa is not None]
        if gpas:
            avg_gpa = sum(gpas) / len(gpas)
            # GPA 0-4.0 映射到 0-100
            academic_score = min(100, round(avg_gpa / 4.0 * 100))
        else:
            academic_score = 50
    else:
        academic_score = 50

    # 2. 德育表现 - 党团发展 + 活动参与综合
    party_score = 0
    party_records = db.query(PartyProgress).filter(PartyProgress.student_id == student_id).all()
    party_stage_map = {
        '群众': 20, '入党申请人': 35, '入党积极分子': 55,
        '发展对象': 70, '中共预备党员': 85, '中共党员': 95,
        '共青团员': 40, '共青团入团申请人': 30,
    }
    if party_records:
        # 取最高阶段
        max_stage_score = 0
        for p in party_records:
            stage_score = party_stage_map.get(p.stage, 20)
            if stage_score > max_stage_score:
                max_stage_score = stage_score
        party_score = max_stage_score
    else:
        party_score = 20

    activity_count = db.query(ActivitySignup).filter(ActivitySignup.student_id == student_id).count()
    activity_score = min(100, activity_count * 10)  # 每参加一次+10，上限100

    moral_score = min(100, round((party_score * 0.5 + activity_score * 0.5)))

    # 3. 心理状态 - 无心理记录=90，有记录看记录数
    psych_count = db.query(PsychologyRecord).filter(PsychologyRecord.student_id == student_id).count()
    if psych_count == 0:
        psychology_score = 90
    elif psych_count <= 2:
        psychology_score = 75
    elif psych_count <= 5:
        psychology_score = 60
    else:
        psychology_score = 45

    # 4. 社会实践 - 活动参与次数 + 签到率
    signups = db.query(ActivitySignup).filter(ActivitySignup.student_id == student_id).all()
    if signups:
        checked_in = sum(1 for s in signups if s.checked_in)
        checkin_rate = checked_in / len(signups)
        practice_score = min(100, round(activity_count * 5 + checkin_rate * 50))
    else:
        practice_score = 30

    # 5. 出勤表现 - 考勤异常越少分越高
    attendance_count = db.query(StudentAttendanceException).filter(
        StudentAttendanceException.student_id == student_id
    ).count()
    if attendance_count == 0:
        attendance_score = 95
    elif attendance_count <= 2:
        attendance_score = 80
    elif attendance_count <= 5:
        attendance_score = 60
    else:
        attendance_score = 40

    # 6. 综合测评 - 从综合测评表取最近一条total_score
    comp_record = db.query(ComprehensiveAssessment).filter(
        ComprehensiveAssessment.student_id == student_id
    ).order_by(desc(ComprehensiveAssessment.id)).first()
    if comp_record and comp_record.total_score:
        comprehensive_score = min(100, max(0, round(comp_record.total_score)))
    else:
        comprehensive_score = 50

    return {
        'dimensions': [
            {'name': '学业成绩', 'score': academic_score},
            {'name': '德育表现', 'score': moral_score},
            {'name': '心理状态', 'score': psychology_score},
            {'name': '社会实践', 'score': practice_score},
            {'name': '出勤表现', 'score': attendance_score},
            {'name': '综合测评', 'score': comprehensive_score}
        ]
    }
