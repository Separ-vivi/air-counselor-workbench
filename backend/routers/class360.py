"""班级360 API - 班级全景视图（v3j 重写：返回明细字段与前端对齐）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import (
    ClassModel, Major, Grade, Student,
    GradeRecord, PartyProgress, PsychologyRecord, FamilyContact,
    StudentHardship, StudentGrant, StudentScholarship, StudentLoan,
    StudentWorkStudy, StudentHonor,
    StudentLeave, StudentDiscipline, StudentDormVisit, StudentDormChat,
    StudentAttendanceException,
    Activity, ActivitySignup, ClassMeeting
)

router = APIRouter(prefix='/api/class360', tags=['class360'])


def _class_student_map(db, class_id):
    students = db.query(Student).filter(Student.class_id == class_id).all()
    return students, {s.id: s for s in students}, [s.id for s in students]


@router.get('/{class_id}/summary')
def get_class_summary(class_id: int, db: Session = Depends(get_db)):
    """班级概要 - 顶部信息卡"""
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    students, _, student_ids = _class_student_map(db, class_id)

    grade_count = db.query(GradeRecord).filter(GradeRecord.student_id.in_(student_ids)).count() if student_ids else 0
    warning_count = db.query(GradeRecord).filter(
        GradeRecord.student_id.in_(student_ids),
        GradeRecord.score < 60
    ).count() if student_ids else 0

    party_members = db.query(PartyProgress).filter(
        PartyProgress.student_id.in_(student_ids),
        PartyProgress.stage.in_(['预备党员', '中共预备党员', '正式党员', '中共党员', '党员'])
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

    avg_score = 0
    fail_rate = 0
    if student_ids:
        result = db.query(func.avg(GradeRecord.score)).filter(
            GradeRecord.student_id.in_(student_ids)
        ).scalar()
        avg_score = round(result, 2) if result else 0
        if grade_count > 0:
            fail_rate = round(warning_count * 100.0 / grade_count, 2)

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
            'fail_rate': fail_rate,
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
    """Tab: 学生名单 (含班干部职务)"""
    from models import StudentCadreRecord
    students = db.query(Student).filter(Student.class_id == class_id).order_by(Student.student_no).all()
    result = []
    for s in students:
        warning_status = 'green'
        grades = db.query(GradeRecord).filter(GradeRecord.student_id == s.id).all()
        if grades:
            avg = sum(g.score for g in grades) / len(grades)
            if avg < 60:
                warning_status = 'red'
            elif avg < 70:
                warning_status = 'yellow'
        cadres = db.query(StudentCadreRecord).filter(StudentCadreRecord.student_id == s.id).all()
        positions = [c.position for c in cadres if c.position]
        result.append({
            'id': s.id, 'student_no': s.student_no, 'name': s.name,
            'gender': s.gender, 'phone': s.phone, 'parent_phone': s.parent_phone,
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
    class_teacher = {'name': cls.class_teacher or '', 'phone': '', 'role': '班主任'}

    def _find(name):
        if not name:
            return None
        return db.query(Student).filter(Student.class_id == class_id, Student.name == name).first()

    m_stu = _find(cls.monitor)
    monitor = {
        'name': cls.monitor or '', 'phone': m_stu.phone if m_stu else '',
        'student_no': m_stu.student_no if m_stu else '', 'role': '班长',
        'student_id': m_stu.id if m_stu else None,
    }
    ls_stu = _find(cls.league_secretary)
    league_secretary = {
        'name': cls.league_secretary or '', 'phone': ls_stu.phone if ls_stu else '',
        'student_no': ls_stu.student_no if ls_stu else '', 'role': '团支书',
        'student_id': ls_stu.id if ls_stu else None,
    }
    cadre_rows = db.query(StudentCadreRecord, Student).join(
        Student, StudentCadreRecord.student_id == Student.id
    ).filter(Student.class_id == class_id).all()
    cadres = [
        {'position': c.position, 'name': stu.name, 'phone': stu.phone,
         'student_no': stu.student_no, 'student_id': stu.id}
        for c, stu in cadre_rows
    ]
    return {
        'class_teacher': class_teacher, 'monitor': monitor,
        'league_secretary': league_secretary, 'cadres': cadres,
    }


@router.get('/{class_id}/party-branch')
def get_class_party_branch(class_id: int, db: Session = Depends(get_db)):
    """班级党/团支部：各类政治面貌详细名单 + 统计"""
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not cls:
        raise HTTPException(404, '班级不存在')
    students = db.query(Student).filter(Student.class_id == class_id).all()
    from collections import Counter
    ps_counter = Counter()
    party_members, league_members, reserved_members, activists, masses = [], [], [], [], []
    for s in students:
        ps = s.political_status or '群众'
        ps_counter[ps] += 1
        item = {'id': s.id, 'name': s.name, 'student_no': s.student_no, 'phone': s.phone,
                'political_status': ps}
        if '中共党员' in ps or ps in ('党员', '正式党员'):
            party_members.append(item)
        elif '预备' in ps:
            reserved_members.append(item)
        elif '积极分子' in ps:
            activists.append(item)
        elif '团员' in ps:
            league_members.append(item)
        else:
            masses.append(item)
    return {
        'class_id': class_id, 'class_name': cls.class_name,
        'league_secretary': cls.league_secretary or '', 'monitor': cls.monitor or '',
        'total': len(students), 'stats': dict(ps_counter),
        'party_members': party_members, 'reserved_members': reserved_members,
        'activists': activists, 'league_members': league_members, 'masses': masses,
    }


@router.get('/{class_id}/featured-activities')
def get_class_featured_activities(class_id: int, db: Session = Depends(get_db)):
    """班级特色活动：从活动主表按班级学生参与关联"""
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not cls:
        raise HTTPException(404, '班级不存在')
    student_ids = [s.id for s in db.query(Student.id).filter(Student.class_id == class_id).all()]
    if not student_ids:
        return []
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
            'id': act.id, 'title': act.title or '',
            'activity_type': act.activity_type or '',
            'activity_date': act.activity_date or '', 'end_date': act.end_date or '',
            'location': act.location or '', 'status': act.status or '',
            'signup_count': signup_count,
        })
    return result


# ==================== v3j 明细结构接口 ====================

@router.get('/{class_id}/grades')
def get_class_grades(class_id: int, db: Session = Depends(get_db)):
    """Tab: 成绩明细 - 返回每条成绩记录（前端要明细展示）"""
    students, stu_map, student_ids = _class_student_map(db, class_id)
    if not student_ids:
        return []
    grades = db.query(GradeRecord).filter(GradeRecord.student_id.in_(student_ids)).all()
    result = []
    for g in grades:
        s = stu_map.get(g.student_id)
        if not s:
            continue
        result.append({
            'id': g.id,
            'student_id': g.student_id,
            'student_no': s.student_no,
            'name': s.name,
            'student_name': s.name,
            'semester': g.semester or '',
            'course_name': g.course_name or '',
            'course_code': getattr(g, 'course_code', '') or '',
            'score': g.score,
            'gpa': g.gpa,
            'credit': g.credit,
            'is_repair': bool(getattr(g, 'is_repair', False) or getattr(g, 'is_makeup', False)),
            'grade_level': getattr(g, 'grade_level', '') or '',
        })
    result.sort(key=lambda x: (x['student_no'] or '', x['semester'] or ''))
    return result


@router.get('/{class_id}/party')
def get_class_party(class_id: int, db: Session = Depends(get_db)):
    """Tab: 党团发展 - 每学生一条主状态"""
    students, _, _ = _class_student_map(db, class_id)
    result = []
    for s in students:
        party = db.query(PartyProgress).filter(PartyProgress.student_id == s.id).order_by(desc(PartyProgress.stage_date)).first()
        # 兼容旧字段 join_date：不存在直接用 stage_date
        stage_date = None
        if party:
            stage_date = getattr(party, 'stage_date', None) or getattr(party, 'join_date', None)
        result.append({
            'student_id': s.id,
            'student_no': s.student_no,
            'name': s.name,
            'student_name': s.name,
            'stage': (party.stage if party else None) or (s.political_status or '群众'),
            'join_date': stage_date,
            'stage_date': stage_date,
            'contact_person': party.contact_person if party else '',
            'notes': party.notes if party else '',
        })
    return result


@router.get('/{class_id}/psychology')
def get_class_psychology(class_id: int, db: Session = Depends(get_db)):
    """Tab: 心理关怀 - 记录明细"""
    students, stu_map, student_ids = _class_student_map(db, class_id)
    if not student_ids:
        return {'stats': {}, 'records': []}
    records = db.query(PsychologyRecord).filter(PsychologyRecord.student_id.in_(student_ids)).all()
    result_records = []
    from collections import Counter
    level_counter = Counter()
    for r in records:
        s = stu_map.get(r.student_id)
        if not s:
            continue
        level = getattr(r, 'attention_level', '') or '普通'
        level_counter[level] += 1
        result_records.append({
            'id': r.id,
            'student_id': r.student_id,
            'student_no': s.student_no,
            'name': s.name,
            'student_name': s.name,
            'attention_level': level,
            'assessment_date': getattr(r, 'record_date', '') or '',
            'record_date': getattr(r, 'record_date', '') or '',
            'topic': r.topic or '',
            'location': r.location or '',
            'counseling_count': getattr(r, 'counseling_count', 0) or 0,
            'next_follow_up': getattr(r, 'next_follow_date', '') or '',
            'next_follow_date': getattr(r, 'next_follow_date', '') or '',
            'notes': r.summary or '',
            'summary': r.summary or '',
        })
    result_records.sort(key=lambda x: (x['assessment_date'] or ''), reverse=True)
    return {
        'stats': dict(level_counter),
        'records': result_records,
    }


@router.get('/{class_id}/funding')
def get_class_funding(class_id: int, db: Session = Depends(get_db)):
    """Tab: 资助分布 - 明细分类返回"""
    students, stu_map, student_ids = _class_student_map(db, class_id)
    if not student_ids:
        return {'hardship': [], 'grants': [], 'scholarships': [], 'loans': [], 'work_study': [], 'honors': []}

    def _sn(sid):
        s = stu_map.get(sid)
        return (s.name if s else '', s.student_no if s else '')

    hardship = []
    for h in db.query(StudentHardship).filter(StudentHardship.student_id.in_(student_ids)).all():
        name, no = _sn(h.student_id)
        hardship.append({
            'id': h.id, 'student_id': h.student_id, 'student_name': name, 'student_no': no,
            'hardship_level': h.hardship_level or '', 'school_year': h.academic_year or '',
            'family_situation': h.evidence or '', 'notes': h.notes or '',
        })
    grants = []
    for g in db.query(StudentGrant).filter(StudentGrant.student_id.in_(student_ids)).all():
        name, no = _sn(g.student_id)
        grants.append({
            'id': g.id, 'student_id': g.student_id, 'student_name': name, 'student_no': no,
            'grant_level': g.grant_type or '', 'amount': g.amount,
            'school_year': g.academic_year or '', 'notes': g.notes or '',
        })
    scholarships = []
    for sc in db.query(StudentScholarship).filter(StudentScholarship.student_id.in_(student_ids)).all():
        name, no = _sn(sc.student_id)
        # 尝试从 scholarship_type 拆等级 例："校一等奖学金" 拆成 name="校一等奖学金" level="一等"
        sname = sc.scholarship_type or ''
        lvl = ''
        for hint in ['特等', '一等', '二等', '三等', '国家']:
            if hint in sname:
                lvl = hint
                break
        scholarships.append({
            'id': sc.id, 'student_id': sc.student_id, 'student_name': name, 'student_no': no,
            'scholarship_name': sname, 'level': lvl, 'amount': sc.amount,
            'school_year': sc.academic_year or '', 'notes': sc.notes or '',
        })
    loans = []
    for l in db.query(StudentLoan).filter(StudentLoan.student_id.in_(student_ids)).all():
        name, no = _sn(l.student_id)
        loans.append({
            'id': l.id, 'student_id': l.student_id, 'student_name': name, 'student_no': no,
            'loan_type': l.loan_type or '', 'amount': l.amount, 'status': l.status or '',
            'school_year': getattr(l, 'academic_year', '') or (str(l.duration) if l.duration else ''),
            'notes': l.notes or '',
        })
    work_study = []
    for w in db.query(StudentWorkStudy).filter(StudentWorkStudy.student_id.in_(student_ids)).all():
        name, no = _sn(w.student_id)
        work_study.append({
            'id': w.id, 'student_id': w.student_id, 'student_name': name, 'student_no': no,
            'position': w.position or '', 'hours': w.hours or 0,
            'salary': w.compensation or 0, 'school_year': w.academic_year or '',
            'notes': w.notes or '',
        })
    honors = []
    for h in db.query(StudentHonor).filter(StudentHonor.student_id.in_(student_ids)).all():
        name, no = _sn(h.student_id)
        honors.append({
            'id': h.id, 'student_id': h.student_id, 'student_name': name, 'student_no': no,
            'honor_name': h.honor_name or '', 'level': h.level or '',
            'school_year': h.academic_year or '', 'notes': h.notes or '',
        })
    return {
        'hardship': hardship, 'grants': grants, 'scholarships': scholarships,
        'loans': loans, 'work_study': work_study, 'honors': honors,
    }


@router.get('/{class_id}/daily')
def get_class_daily(class_id: int, db: Session = Depends(get_db)):
    """Tab: 日常管理 - 明细分类返回"""
    students, stu_map, student_ids = _class_student_map(db, class_id)
    if not student_ids:
        return {'dorm_visits': [], 'leaves': [], 'disciplines': [], 'dorm_chats': [], 'attendance': []}

    def _sn(sid):
        s = stu_map.get(sid)
        return (s.name if s else '', s.student_no if s else '')

    dorm_visits = []
    for v in db.query(StudentDormVisit).filter(StudentDormVisit.student_id.in_(student_ids)).all():
        name, no = _sn(v.student_id)
        dorm_visits.append({
            'id': v.id, 'student_id': v.student_id, 'student_name': name, 'student_no': no,
            'visit_date': v.visit_date or '',
            'dorm_no': getattr(v, 'dorm_room', '') or '',
            'situation': v.situation or '', 'notes': v.notes or '',
        })
    leaves = []
    for l in db.query(StudentLeave).filter(StudentLeave.student_id.in_(student_ids)).all():
        name, no = _sn(l.student_id)
        leaves.append({
            'id': l.id, 'student_id': l.student_id, 'student_name': name, 'student_no': no,
            'leave_type': l.leave_type or '',
            'start_date': l.start_date or '', 'end_date': l.end_date or '',
            'reason': (l.notes or l.destination or '') , 'destination': l.destination or '',
            'approval_status': l.approval_status or '',
        })
    disciplines = []
    for d in db.query(StudentDiscipline).filter(StudentDiscipline.student_id.in_(student_ids)).all():
        name, no = _sn(d.student_id)
        disciplines.append({
            'id': d.id, 'student_id': d.student_id, 'student_name': name, 'student_no': no,
            'discipline_type': d.discipline_type or '',
            'punishment_level': d.level or '',
            'incident_date': d.discipline_date or '',
            'description': d.reason or '', 'reason': d.reason or '',
            'notes': d.notes or '',
        })
    dorm_chats = []
    try:
        for c in db.query(StudentDormChat).filter(StudentDormChat.student_id.in_(student_ids)).all():
            name, no = _sn(c.student_id)
            dorm_chats.append({
                'id': c.id, 'student_id': c.student_id, 'student_name': name, 'student_no': no,
                'chat_date': c.chat_date or '', 'topic': c.topic or '',
                'content': c.key_points or '', 'follow_up': c.follow_up or '',
            })
    except Exception:
        pass
    attendance = []
    try:
        for a in db.query(StudentAttendanceException).filter(StudentAttendanceException.student_id.in_(student_ids)).all():
            name, no = _sn(a.student_id)
            attendance.append({
                'id': a.id, 'student_id': a.student_id, 'student_name': name, 'student_no': no,
                'exception_type': a.exception_type or '',
                'course_name': a.course_name or '',
                'date': a.exception_date or '',
                'notes': a.notes or '',
            })
    except Exception:
        pass
    return {
        'dorm_visits': dorm_visits, 'leaves': leaves, 'disciplines': disciplines,
        'dorm_chats': dorm_chats, 'attendance': attendance,
    }


@router.get('/{class_id}/activities')
def get_class_activities(class_id: int, db: Session = Depends(get_db)):
    """Tab: 活动参与 - 每条签到明细"""
    students, stu_map, student_ids = _class_student_map(db, class_id)
    if not student_ids:
        return []
    signups = db.query(ActivitySignup).filter(ActivitySignup.student_id.in_(student_ids)).all()
    activity_ids = list({sp.activity_id for sp in signups})
    activities = db.query(Activity).filter(Activity.id.in_(activity_ids)).all() if activity_ids else []
    act_map = {a.id: a for a in activities}

    result = []
    for sp in signups:
        a = act_map.get(sp.activity_id)
        if not a:
            continue
        s = stu_map.get(sp.student_id)
        if not s:
            continue
        result.append({
            'id': sp.id,
            'activity_id': a.id,
            'student_id': sp.student_id,
            'student_name': s.name,
            'student_no': s.student_no,
            'activity_name': a.title or '',
            'title': a.title or '',
            'activity_type': a.activity_type or '',
            'activity_date': a.activity_date or '',
            'location': a.location or '',
            'role': '组织者' if getattr(a, 'organizer', None) == s.name else '参与者',
            'status': a.status or '',
            'signed_up': sp.signed_up, 'checked_in': sp.checked_in,
            'points': sp.points,
            'notes': '',
        })
    result.sort(key=lambda x: x['activity_date'] or '', reverse=True)
    return result
