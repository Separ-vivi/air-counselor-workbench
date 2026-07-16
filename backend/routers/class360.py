"""班级360 API - 班级全景视图"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import (
    ClassModel, Major, Grade, Student,
    GradeRecord, PartyProgress, PsychologyRecord, FamilyContact,
    StudentHardship, StudentGrant, StudentScholarship, StudentHonor,
    StudentLeave, StudentDiscipline, StudentDormVisit,
    Activity, ActivitySignup, ClassMeeting
)

router = APIRouter(prefix='/api/class360', tags=['class360'])


@router.get('/{class_id}/summary')
def get_class_summary(class_id: int, db: Session = Depends(get_db)):
    """班级概要 - 顶部信息卡"""
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    
    students = db.query(Student).filter(Student.class_id == class_id).all()
    student_ids = [s.id for s in students]
    
    # 统计数据
    grade_count = db.query(GradeRecord).filter(GradeRecord.student_id.in_(student_ids)).count() if student_ids else 0
    warning_count = db.query(GradeRecord).filter(
        GradeRecord.student_id.in_(student_ids),
        GradeRecord.score < 60
    ).count() if student_ids else 0
    
    party_members = db.query(PartyProgress).filter(
        PartyProgress.student_id.in_(student_ids),
        PartyProgress.stage.in_(['预备党员', '正式党员'])
    ).count() if student_ids else 0
    
    psych_attention = db.query(PsychologyRecord).filter(
        PsychologyRecord.student_id.in_(student_ids)
    ).count() if student_ids else 0
    
    hardship_count = db.query(StudentHardship).filter(
        StudentHardship.student_id.in_(student_ids)
    ).count() if student_ids else 0
    
    leave_count = db.query(StudentLeave).filter(
        StudentLeave.student_id.in_(student_ids)
    ).count() if student_ids else 0
    
    discipline_count = db.query(StudentDiscipline).filter(
        StudentDiscipline.student_id.in_(student_ids)
    ).count() if student_ids else 0
    
    activity_count = db.query(Activity).filter(
        Activity.student_id.in_(student_ids)
    ).count() if student_ids else 0
    
    # 成绩统计
    avg_score = 0
    if student_ids:
        result = db.query(func.avg(GradeRecord.score)).filter(
            GradeRecord.student_id.in_(student_ids)
        ).scalar()
        avg_score = round(result, 2) if result else 0
    
    return {
        'id': cls.id,
        'class_name': cls.class_name,
        'major_name': cls.major.major_name if cls.major else '',
        'grade_name': cls.major.grade.grade_name if cls.major and cls.major.grade else '',
        'class_teacher': cls.class_teacher or '',
        'monitor': cls.monitor or '',
        'league_secretary': cls.league_secretary or '',
        'student_count': len(students),
        'male_count': sum(1 for s in students if s.gender == '男'),
        'female_count': sum(1 for s in students if s.gender == '女'),
        'stats': {
            'grade_count': grade_count,
            'warning_count': warning_count,
            'avg_score': avg_score,
            'party_members': party_members,
            'psych_attention': psych_attention,
            'hardship_count': hardship_count,
            'leave_count': leave_count,
            'discipline_count': discipline_count,
            'activity_count': activity_count,
        }
    }


@router.get('/{class_id}/students')
def get_class_students(class_id: int, db: Session = Depends(get_db)):
    """Tab 2: 学生名单"""
    students = db.query(Student).filter(Student.class_id == class_id).order_by(Student.student_no).all()
    result = []
    for s in students:
        # 获取预警状态
        warning_status = 'green'
        grades = db.query(GradeRecord).filter(GradeRecord.student_id == s.id).all()
        if grades:
            avg = sum(g.score for g in grades) / len(grades)
            if avg < 60:
                warning_status = 'red'
            elif avg < 70:
                warning_status = 'yellow'
        
        result.append({
            'id': s.id,
            'student_no': s.student_no,
            'name': s.name,
            'gender': s.gender,
            'phone': s.phone,
            'political_status': s.political_status,
            'warning_status': warning_status,
        })
    return result


@router.get('/{class_id}/grades')
def get_class_grades(class_id: int, db: Session = Depends(get_db)):
    """Tab 3: 成绩总览"""
    students = db.query(Student).filter(Student.class_id == class_id).all()
    result = []
    for s in students:
        grades = db.query(GradeRecord).filter(GradeRecord.student_id == s.id).all()
        if grades:
            avg_score = sum(g.score for g in grades) / len(grades)
            total_credits = sum(g.credit for g in grades)
            failed_count = sum(1 for g in grades if g.score < 60)
            result.append({
                'student_id': s.id,
                'student_no': s.student_no,
                'name': s.name,
                'grade_count': len(grades),
                'avg_score': round(avg_score, 2),
                'total_credits': total_credits,
                'failed_count': failed_count,
            })
    return sorted(result, key=lambda x: x['avg_score'], reverse=True)


@router.get('/{class_id}/party')
def get_class_party(class_id: int, db: Session = Depends(get_db)):
    """Tab 4: 党团发展"""
    students = db.query(Student).filter(Student.class_id == class_id).all()
    result = []
    for s in students:
        party = db.query(PartyProgress).filter(PartyProgress.student_id == s.id).first()
        result.append({
            'student_id': s.id,
            'student_no': s.student_no,
            'name': s.name,
            'stage': party.stage if party else '群众',
            'join_date': party.join_date if party else None,
        })
    return result


@router.get('/{class_id}/psychology')
def get_class_psychology(class_id: int, db: Session = Depends(get_db)):
    """Tab 5: 心理概览"""
    students = db.query(Student).filter(Student.class_id == class_id).all()
    result = []
    for s in students:
        records = db.query(PsychologyRecord).filter(PsychologyRecord.student_id == s.id).all()
        if records:
            latest = max(records, key=lambda r: r.created_at or datetime.min)
            result.append({
                'student_id': s.id,
                'student_no': s.student_no,
                'name': s.name,
                'topic': latest.topic,
                'record_count': len(records),
            })
    return result


@router.get('/{class_id}/funding')
def get_class_funding(class_id: int, db: Session = Depends(get_db)):
    """Tab 6: 资助概览"""
    students = db.query(Student).filter(Student.class_id == class_id).all()
    student_ids = [s.id for s in students]
    
    hardship = db.query(StudentHardship).filter(StudentHardship.student_id.in_(student_ids)).all() if student_ids else []
    grants = db.query(StudentGrant).filter(StudentGrant.student_id.in_(student_ids)).all() if student_ids else []
    scholarships = db.query(StudentScholarship).filter(StudentScholarship.student_id.in_(student_ids)).all() if student_ids else []
    honors = db.query(StudentHonor).filter(StudentHonor.student_id.in_(student_ids)).all() if student_ids else []
    
    # 按学生聚合
    result = {}
    for s in students:
        result[s.id] = {
            'student_id': s.id,
            'student_no': s.student_no,
            'name': s.name,
            'hardship': [],
            'grants': [],
            'scholarships': [],
            'honors': [],
        }
    
    for h in hardship:
        if h.student_id in result:
            result[h.student_id]['hardship'].append({'level': h.hardship_level, 'year': h.academic_year})
    for g in grants:
        if g.student_id in result:
            result[g.student_id]['grants'].append({'type': g.grant_type, 'amount': g.amount})
    for s in scholarships:
        if s.student_id in result:
            result[s.student_id]['scholarships'].append({'type': s.scholarship_type, 'amount': s.amount})
    for h in honors:
        if h.student_id in result:
            result[h.student_id]['honors'].append({'title': h.honor_title, 'year': h.academic_year})
    
    return [r for r in result.values() if r['hardship'] or r['grants'] or r['scholarships'] or r['honors']]


@router.get('/{class_id}/daily')
def get_class_daily(class_id: int, db: Session = Depends(get_db)):
    """Tab 7: 日常管理"""
    students = db.query(Student).filter(Student.class_id == class_id).all()
    student_ids = [s.id for s in students]
    
    leaves = db.query(StudentLeave).filter(StudentLeave.student_id.in_(student_ids)).all() if student_ids else []
    disciplines = db.query(StudentDiscipline).filter(StudentDiscipline.student_id.in_(student_ids)).all() if student_ids else []
    dorm_visits = db.query(StudentDormVisit).filter(
        StudentDormVisit.student_id.in_(student_ids)
    ).all() if student_ids else []
    
    return {
        'leaves': [{'id': l.id, 'student_id': l.student_id, 'leave_type': l.leave_type, 
                    'start_date': l.start_date, 'end_date': l.end_date, 'status': l.status} for l in leaves],
        'disciplines': [{'id': d.id, 'student_id': d.student_id, 'discipline_type': d.discipline_type,
                         'date': d.date, 'level': d.level} for d in disciplines],
        'dorm_visits': [{'id': v.id, 'student_id': v.student_id, 'visit_date': v.visit_date,
                         'dorm_no': v.dorm_no, 'visitor': v.visitor} for v in dorm_visits],
    }


@router.get('/{class_id}/activities')
def get_class_activities(class_id: int, db: Session = Depends(get_db)):
    """Tab 8: 活动记录"""
    students = db.query(Student).filter(Student.class_id == class_id).all()
    student_ids = [s.id for s in students]
    
    activities = db.query(Activity).filter(Activity.student_id.in_(student_ids)).all() if student_ids else []
    
    result = []
    for a in activities:
        student = next((s for s in students if s.id == a.student_id), None)
        result.append({
            'id': a.id,
            'student_id': a.student_id,
            'student_name': student.name if student else '',
            'activity_name': a.activity_name,
            'activity_type': a.activity_type,
            'activity_date': a.activity_date,
            'role': a.role,
            'award': a.award,
        })
    return result
