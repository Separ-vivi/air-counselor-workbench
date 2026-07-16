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
    
    activity_count = db.query(ActivitySignup).filter(
        ActivitySignup.student_id.in_(student_ids)
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
    """Tab 2: 学生名单 (含班干部职务)"""
    from models import StudentCadreRecord
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
        # 班干部职务
        cadres = db.query(StudentCadreRecord).filter(StudentCadreRecord.student_id == s.id).all()
        positions = [c.position for c in cadres if c.position]
        result.append({
            'id': s.id,
            'student_no': s.student_no,
            'name': s.name,
            'gender': s.gender,
            'phone': s.phone,
            'parent_phone': s.parent_phone,
            'political_status': s.political_status,
            'warning_status': warning_status,
            'cadre_positions': positions,
        })
    return result


@router.get('/{class_id}/contacts')
def get_class_contacts(class_id: int, db: Session = Depends(get_db)):
    """班级联系方式：班主任 + 班长 + 团支书 + 所有班干部"""
    from models import StudentCadreRecord
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not cls:
        raise HTTPException(404, '班级不存在')

    # 班主任 (存的是姓名字符串)
    class_teacher = {'name': cls.class_teacher or '', 'phone': '', 'role': '班主任'}

    def _find_student_by_name(name):
        if not name:
            return None
        s = db.query(Student).filter(Student.class_id == class_id, Student.name == name).first()
        return s

    # 班长
    monitor_stu = _find_student_by_name(cls.monitor)
    monitor = {
        'name': cls.monitor or '',
        'phone': monitor_stu.phone if monitor_stu else '',
        'student_no': monitor_stu.student_no if monitor_stu else '',
        'role': '班长',
        'student_id': monitor_stu.id if monitor_stu else None,
    }
    # 团支书
    ls_stu = _find_student_by_name(cls.league_secretary)
    league_secretary = {
        'name': cls.league_secretary or '',
        'phone': ls_stu.phone if ls_stu else '',
        'student_no': ls_stu.student_no if ls_stu else '',
        'role': '团支书',
        'student_id': ls_stu.id if ls_stu else None,
    }

    # 全部班干部
    cadre_rows = db.query(StudentCadreRecord, Student).join(
        Student, StudentCadreRecord.student_id == Student.id
    ).filter(Student.class_id == class_id).all()
    cadres = [
        {
            'position': c.position,
            'name': stu.name,
            'phone': stu.phone,
            'student_no': stu.student_no,
            'student_id': stu.id,
        }
        for c, stu in cadre_rows
    ]

    return {
        'class_teacher': class_teacher,
        'monitor': monitor,
        'league_secretary': league_secretary,
        'cadres': cadres,
    }


@router.get('/{class_id}/party-branch')
def get_class_party_branch(class_id: int, db: Session = Depends(get_db)):
    """班级党/团支部：党员/团员名单 + 政治面貌统计"""
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not cls:
        raise HTTPException(404, '班级不存在')
    students = db.query(Student).filter(Student.class_id == class_id).all()
    from collections import Counter
    ps_counter = Counter()
    party_members = []
    league_members = []
    reserved_members = []
    activists = []
    masses = []
    for s in students:
        ps = s.political_status or '群众'
        ps_counter[ps] += 1
        item = {'id': s.id, 'name': s.name, 'student_no': s.student_no, 'phone': s.phone,
                'political_status': ps}
        if '中共党员' in ps or ps == '党员':
            party_members.append(item)
        elif '预备党员' in ps:
            reserved_members.append(item)
        elif '积极分子' in ps:
            activists.append(item)
        elif '团员' in ps:
            league_members.append(item)
        else:
            masses.append(item)
    return {
        'class_id': class_id,
        'class_name': cls.class_name,
        'league_secretary': cls.league_secretary or '',
        'monitor': cls.monitor or '',
        'total': len(students),
        'stats': dict(ps_counter),
        'party_members': party_members,
        'reserved_members': reserved_members,
        'activists': activists,
        'league_members': league_members,
        'masses': masses,
    }


@router.get('/{class_id}/featured-activities')
def get_class_featured_activities(class_id: int, db: Session = Depends(get_db)):
    """班级特色活动：从活动主表按班级筛选（class_id 精确匹配 + class_name 兼容）"""
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not cls:
        raise HTTPException(404, '班级不存在')
    # Activity 表的班级识别：优先 activity 中若有 class_id 字段则用；否则通过 ActivitySignup 关联查班级学生参与的活动
    student_ids = [s.id for s in db.query(Student.id).filter(Student.class_id == class_id).all()]
    if not student_ids:
        return []
    # 与班级学生有关联签到的活动
    act_ids = [row[0] for row in db.query(ActivitySignup.activity_id).filter(
        ActivitySignup.student_id.in_(student_ids)
    ).distinct().all()]
    if not act_ids:
        return []
    all_acts = db.query(Activity).filter(Activity.id.in_(act_ids)).order_by(desc(Activity.activity_date)).all()
    result = []
    for act in all_acts:
        signup_count = db.query(ActivitySignup).filter(
            ActivitySignup.activity_id == act.id,
            ActivitySignup.student_id.in_(student_ids),
        ).count()
        result.append({
            'id': act.id,
            'title': act.title or '',
            'activity_type': act.activity_type or '',
            'activity_date': act.activity_date or '',
            'end_date': act.end_date or '',
            'location': act.location or '',
            'status': act.status or '',
            'signup_count': signup_count,
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
    """Tab 8: 活动记录 - 通过 ActivitySignup 联表"""
    students = db.query(Student).filter(Student.class_id == class_id).all()
    student_ids = [s.id for s in students]
    if not student_ids:
        return []

    signups = db.query(ActivitySignup).filter(ActivitySignup.student_id.in_(student_ids)).all()
    activity_ids = list({sp.activity_id for sp in signups})
    activities = db.query(Activity).filter(Activity.id.in_(activity_ids)).all() if activity_ids else []
    act_map = {a.id: a for a in activities}
    student_map = {s.id: s for s in students}

    result = []
    for sp in signups:
        a = act_map.get(sp.activity_id)
        if not a:
            continue
        student = student_map.get(sp.student_id)
        result.append({
            'id': sp.id,
            'activity_id': a.id,
            'student_id': sp.student_id,
            'student_name': student.name if student else '',
            'student_no': student.student_no if student else '',
            'title': a.title,
            'activity_type': a.activity_type,
            'activity_date': a.activity_date,
            'location': a.location,
            'status': a.status,
            'signed_up': sp.signed_up,
            'checked_in': sp.checked_in,
            'points': sp.points,
        })
    return result
