"""学期报表 API - V5-h-hotfix11
全面重构：增加考勤/心理/资助/荣誉/违纪/访谈/宿舍维度
修复导出500、修复空数据崩溃
增加semester参数到心理/违纪/荣誉/访谈API + 党员人数 + 访谈覆盖率
V5-h-hotfix10: 所有统计指标严格按学期筛选 + 对比指标扩展到12项
V5-h-hotfix11: 修复学期过滤 - 党团/活动/宿舍/就业端点增加semester参数;
                宿舍端点实际应用学期日期过滤; 对比区增加请假人次和宿舍走访指标
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, case, distinct
from sqlalchemy.orm import Session
from database import get_db
from models import (
    Student, ClassModel, Major, GradeRecord, WarningRecord,
    PartyProgress, EmploymentRecord, Activity, ActivitySignup,
    PsychologyRecord, StudentDiscipline, StudentHardship,
    StudentGrant, StudentScholarship, StudentLoan, StudentWorkStudy,
    StudentHonor, StudentDormVisit, StudentLeave, StudentDormChat,
    StudentAttendanceException, StudentInterview
)

from routers.semester_report_utils import (
    _get_current_semester, _format_semester_display,
    _semester_date_range, _semester_to_academic_year,
)
from routers.semester_report_queries import (
    _get_semester_metric, _get_cumulative_party_member_count,
)
from routers.semester_report_export import export_semester_report as _export_semester_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/semester-report', tags=['学期报表'])


# ============================================================
# 0. 获取可用学期列表
# ============================================================
@router.get('/semesters')
def list_semesters(db: Session = Depends(get_db)):
    """返回数据库中已有的学期列表"""
    semesters = set()
    try:
        rows = db.query(GradeRecord.semester).distinct().all()
        for r in rows:
            if r[0]:
                semesters.add(r[0])
    except Exception:
        pass
    try:
        rows = db.query(WarningRecord.semester).distinct().all()
        for r in rows:
            if r[0]:
                semesters.add(r[0])
    except Exception:
        pass
    sorted_sems = sorted(semesters, reverse=True)
    return [
        {'code': s, 'label': _format_semester_display(s)}
        for s in sorted_sems
    ]


# ============================================================
# 1. 学期总览（增强）
# ============================================================
@router.get('/summary')
def semester_summary(semester: str = Query(None), db: Session = Depends(get_db)):
    """学期总览：增加考勤异常、心理关注、资助人次、违纪人数、荣誉人次"""
    result = {
        'total_students': 0,
        'total_classes': 0,
        'total_majors': 0,
        'political_distribution': {},
        'gender_distribution': {},
        'housing_distribution': {'外宿': 0, '住校': 0},
        'campus_distribution': {},
        # 新增字段
        'attendance_exception_count': 0,
        'psychology_attention_count': 0,
        'financial_aid_count': 0,
        'discipline_count': 0,
        'honor_count': 0,
        'party_member_count': 0,
        'leave_count': 0,
        'dormitory_visit_count': 0,
    }
    try:
        result['total_students'] = db.query(Student).count()
        result['total_classes'] = db.query(ClassModel).count()
        result['total_majors'] = db.query(Major).count()
    except Exception as e:
        logger.warning(f"summary 基础统计异常: {e}")

    # 政治面貌分布
    try:
        rows = (
            db.query(Student.political_status, func.count(Student.id))
            .group_by(Student.political_status)
            .all()
        )
        result['political_distribution'] = {
            (status or '群众'): cnt for status, cnt in rows
        }
    except Exception as e:
        logger.warning(f"summary 政治面貌异常: {e}")

    # 性别分布
    try:
        rows = (
            db.query(Student.gender, func.count(Student.id))
            .group_by(Student.gender)
            .all()
        )
        result['gender_distribution'] = {
            (g or '未知'): cnt for g, cnt in rows
        }
    except Exception as e:
        logger.warning(f"summary 性别异常: {e}")

    # 外宿/住校
    try:
        off = db.query(Student).filter(Student.is_off_campus == True).count()
        total = result['total_students']
        result['housing_distribution'] = {'外宿': off, '住校': total - off}
    except Exception as e:
        logger.warning(f"summary 住宿异常: {e}")

    # 校区分布
    try:
        rows = (
            db.query(Student.campus, func.count(Student.id))
            .group_by(Student.campus)
            .all()
        )
        result['campus_distribution'] = {
            (c or '未知'): cnt for c, cnt in rows
        }
    except Exception as e:
        logger.warning(f"summary 校区异常: {e}")

    # 考勤异常总次数
    try:
        q = db.query(StudentAttendanceException)
        if semester and semester != 'all':
            start, end = _semester_date_range(semester)
            if start and end:
                q = q.filter(
                    StudentAttendanceException.exception_date >= start,
                    StudentAttendanceException.exception_date <= end
                )
        result['attendance_exception_count'] = q.count()
    except Exception as e:
        logger.warning(f"summary 考勤异常异常: {e}")

    # 心理关注人数（非普通等级，按学期日期范围筛选）
    try:
        q = db.query(PsychologyRecord.student_id).filter(
            PsychologyRecord.attention_level.in_(['一级关注', '二级关注', '三级关注'])
        )
        if semester and semester != 'all':
            start, end = _semester_date_range(semester)
            if start and end:
                q = q.filter(
                    PsychologyRecord.record_date >= start,
                    PsychologyRecord.record_date <= end
                )
        result['psychology_attention_count'] = q.distinct().count()
    except Exception as e:
        logger.warning(f"summary 心理关注异常: {e}")

    # 资助总人次
    try:
        aid_year = _semester_to_academic_year(semester)
        hardship_q = db.query(StudentHardship)
        grant_q = db.query(StudentGrant)
        scholarship_q = db.query(StudentScholarship)
        loan_q = db.query(StudentLoan)
        work_q = db.query(StudentWorkStudy)
        if aid_year:
            hardship_q = hardship_q.filter(StudentHardship.academic_year == aid_year)
            grant_q = grant_q.filter(StudentGrant.academic_year == aid_year)
            scholarship_q = scholarship_q.filter(StudentScholarship.academic_year == aid_year)
            work_q = work_q.filter(StudentWorkStudy.academic_year == aid_year)
        cnt = hardship_q.count() + grant_q.count() + scholarship_q.count() + loan_q.count() + work_q.count()
        result['financial_aid_count'] = cnt
    except Exception as e:
        logger.warning(f"summary 资助人次异常: {e}")

    # 违纪人数（按学期日期范围筛选）
    try:
        q = db.query(StudentDiscipline.student_id).distinct()
        if semester and semester != 'all':
            start, end = _semester_date_range(semester)
            if start and end:
                q = q.filter(
                    StudentDiscipline.discipline_date >= start,
                    StudentDiscipline.discipline_date <= end
                )
        result['discipline_count'] = q.count()
    except Exception as e:
        logger.warning(f"summary 违纪人数异常: {e}")

    # 荣誉总人次（按学年筛选）
    try:
        q = db.query(StudentHonor)
        honor_year = _semester_to_academic_year(semester)
        if honor_year:
            q = q.filter(StudentHonor.academic_year == honor_year)
        result['honor_count'] = q.count()
    except Exception as e:
        logger.warning(f"summary 荣誉人次异常: {e}")

    # 党员人数（累计值：截止到该学期结束日期的最新 stage）
    try:
        _pp_subq = db.query(
            PartyProgress.student_id,
            func.max(PartyProgress.id).label('max_id')
        )
        if semester and semester != 'all':
            _pp_start, _pp_end = _semester_date_range(semester)
            if _pp_end:
                _pp_subq = _pp_subq.filter(
                    PartyProgress.stage_date <= _pp_end
                )
        _pp_subq = _pp_subq.group_by(PartyProgress.student_id).subquery()
        result['party_member_count'] = (
            db.query(func.count(PartyProgress.student_id))
            .join(_pp_subq, PartyProgress.id == _pp_subq.c.max_id)
            .filter(PartyProgress.stage.in_(['中共预备党员', '中共党员']))
            .scalar() or 0
        )
    except Exception as e:
        logger.warning(f"summary 党员人数异常: {e}")

    # 请假人次（按学期日期范围筛选）
    try:
        q = db.query(StudentLeave)
        if semester and semester != 'all':
            start, end = _semester_date_range(semester)
            if start and end:
                q = q.filter(
                    StudentLeave.start_date >= start,
                    StudentLeave.start_date <= end
                )
        result['leave_count'] = q.count()
    except Exception as e:
        logger.warning(f"summary 请假人次异常: {e}")

    # 宿舍走访次数（按学期日期范围筛选）
    try:
        q = db.query(StudentDormVisit)
        if semester and semester != 'all':
            start, end = _semester_date_range(semester)
            if start and end:
                q = q.filter(
                    StudentDormVisit.visit_date >= start,
                    StudentDormVisit.visit_date <= end
                )
        result['dormitory_visit_count'] = q.count()
    except Exception as e:
        logger.warning(f"summary 宿舍走访异常: {e}")

    return result


# ============================================================
# 2. 学业数据
# ============================================================
@router.get('/academics')
def semester_academics(semester: str = Query(None), db: Session = Depends(get_db)):
    """学业汇总"""
    result = {
        'class_averages': [],
        'fail_rate': 0.0,
        'fail_count': 0,
        'total_students_with_grades': 0,
        'top10': [],
        'warning_stats': [],
    }

    grade_filters = [GradeRecord.score.isnot(None)]
    warn_filters = []
    if semester and semester != 'all':
        grade_filters.append(GradeRecord.semester == semester)
        warn_filters.append(WarningRecord.semester == semester)

    # 各班平均成绩
    try:
        rows = (
            db.query(
                ClassModel.class_name,
                func.avg(GradeRecord.score)
            )
            .join(Student, Student.class_id == ClassModel.id)
            .join(GradeRecord, GradeRecord.student_id == Student.id)
            .filter(*grade_filters)
            .group_by(ClassModel.id, ClassModel.class_name)
            .all()
        )
        result['class_averages'] = [
            {'class_name': name, 'avg_score': round(avg, 2) if avg else 0}
            for name, avg in rows
        ]
    except Exception as e:
        logger.warning(f"academics 班级平均异常: {e}")

    # 挂科率
    try:
        base_q = db.query(GradeRecord.student_id).filter(*grade_filters)
        total_with_grades = base_q.distinct().count() or 0
        fail_students = base_q.filter(GradeRecord.score < 60).distinct().count() or 0
        result['total_students_with_grades'] = total_with_grades
        result['fail_count'] = fail_students
        result['fail_rate'] = (
            round(fail_students / total_with_grades * 100, 2)
            if total_with_grades > 0 else 0.0
        )
    except Exception as e:
        logger.warning(f"academics 挂科率异常: {e}")

    # 成绩 Top 10
    try:
        rows = (
            db.query(
                Student.student_no,
                Student.name,
                ClassModel.class_name,
                func.avg(GradeRecord.score).label('avg_score')
            )
            .join(Student, GradeRecord.student_id == Student.id)
            .join(ClassModel, Student.class_id == ClassModel.id)
            .filter(*grade_filters)
            .group_by(Student.id, Student.student_no, Student.name, ClassModel.class_name)
            .order_by(func.avg(GradeRecord.score).desc())
            .limit(10)
            .all()
        )
        result['top10'] = [
            {
                'student_no': r[0],
                'name': r[1],
                'class_name': r[2],
                'avg_score': round(r[3], 2) if r[3] else 0
            }
            for r in rows
        ]
    except Exception as e:
        logger.warning(f"academics Top10 异常: {e}")

    # 学业预警统计
    try:
        red_q = db.query(WarningRecord).filter(WarningRecord.warning_type == 'red')
        yellow_q = db.query(WarningRecord).filter(WarningRecord.warning_type == 'yellow')
        if warn_filters:
            red_q = red_q.filter(*warn_filters)
            yellow_q = yellow_q.filter(*warn_filters)
        red = red_q.count()
        yellow = yellow_q.count()
        result['warning_stats'] = [
            {'level': 'red', 'level_label': '红色预警', 'count': red},
            {'level': 'yellow', 'level_label': '黄色预警', 'count': yellow},
            {'level': 'normal', 'level_label': '正常', 'count': max(0, result['total_students_with_grades'] - red - yellow)},
        ]
    except Exception as e:
        logger.warning(f"academics 预警异常: {e}")

    return result


# ============================================================
# 3. 党团发展
# ============================================================
@router.get('/party-development')
def party_development(semester: str = Query(None), db: Session = Depends(get_db)):
    """党团发展进度（支持学期筛选）"""
    stage_map = {
        '递交入党申请书': 0,
        '入党积极分子': 0,
        '发展对象': 0,
        '中共预备党员': 0,
        '中共党员': 0,
    }
    total_new_this_semester = 0

    sem_start, sem_end = _semester_date_range(semester)

    try:
        subq = (
            db.query(
                PartyProgress.student_id,
                func.max(PartyProgress.id).label('max_id')
            )
        )
        if sem_end:
            subq = subq.filter(PartyProgress.stage_date <= sem_end)
        subq = subq.group_by(PartyProgress.student_id).subquery()
        rows = (
            db.query(PartyProgress.stage, func.count(PartyProgress.student_id))
            .join(subq, PartyProgress.id == subq.c.max_id)
            .group_by(PartyProgress.stage)
            .all()
        )
        for stage, cnt in rows:
            if stage in stage_map:
                stage_map[stage] = cnt
            else:
                stage_map[stage] = cnt
    except Exception as e:
        logger.warning(f"party 各阶段异常: {e}")

    try:
        if sem_start and sem_end:
            total_new_this_semester = (
                db.query(func.count(PartyProgress.id))
                .filter(
                    PartyProgress.stage_date >= sem_start,
                    PartyProgress.stage_date <= sem_end
                )
                .scalar() or 0
            )
        else:
            now = datetime.now()
            if now.month >= 9:
                fallback_start = f"{now.year}-09-01"
            else:
                fallback_start = f"{now.year}-02-01"
            total_new_this_semester = (
                db.query(func.count(PartyProgress.id))
                .filter(PartyProgress.stage_date >= fallback_start)
                .scalar() or 0
            )
    except Exception as e:
        logger.warning(f"party 新发展异常: {e}")

    return {
        'stages': stage_map,
        'new_this_semester': total_new_this_semester,
    }


# ============================================================
# 4. 就业跟踪
# ============================================================
@router.get('/employment')
def employment_stats(semester: str = Query(None), db: Session = Depends(get_db)):
    """就业状态分布与就业率（支持学期筛选）"""
    status_map = {
        '已签约': 0,
        '考研': 0,
        '出国': 0,
        '待就业': 0,
        '未知': 0,
    }
    total = 0

    emp_filters = []
    if semester and semester != 'all':
        start, end = _semester_date_range(semester)
        if start and end:
            emp_filters.append(EmploymentRecord.offer_date >= start)
            emp_filters.append(EmploymentRecord.offer_date <= end)

    try:
        q = (
            db.query(EmploymentRecord.status, func.count(EmploymentRecord.id))
            .group_by(EmploymentRecord.status)
        )
        if emp_filters:
            q = q.filter(*emp_filters)
        rows = q.all()
        total = sum(cnt for _, cnt in rows)
        for status, cnt in rows:
            s = (status or '').strip()
            if s in status_map:
                status_map[s] = cnt
            elif s:
                status_map[s] = cnt
            else:
                status_map['未知'] += cnt
    except Exception as e:
        logger.warning(f"employment 异常: {e}")

    employed = status_map.get('已签约', 0)
    employment_rate = round(employed / total * 100, 2) if total > 0 else 0.0

    return {
        'distribution': status_map,
        'total_records': total,
        'total_count': total,
        'employed_count': employed,
        'employment_rate': employment_rate,
    }


# ============================================================
# 5. 学生活动
# ============================================================
@router.get('/activities')
def activity_stats(semester: str = Query(None), db: Session = Depends(get_db)):
    """活动统计（支持学期筛选）"""
    total_activities = 0
    total_participants = 0
    activity_ranking = []

    act_filters = []
    if semester and semester != 'all':
        start, end = _semester_date_range(semester)
        if start and end:
            act_filters.append(Activity.activity_date >= start)
            act_filters.append(Activity.activity_date <= end)

    try:
        q = db.query(Activity)
        if act_filters:
            q = q.filter(*act_filters)
        total_activities = q.count()
    except Exception as e:
        logger.warning(f"activities 总数异常: {e}")

    try:
        q = db.query(ActivitySignup).join(Activity)
        if act_filters:
            q = q.filter(*act_filters)
        total_participants = q.count()
    except Exception as e:
        logger.warning(f"activities 人次异常: {e}")

    try:
        q = (
            db.query(
                Activity.title,
                Activity.activity_type,
                func.count(ActivitySignup.id).label('participants')
            )
            .join(ActivitySignup, ActivitySignup.activity_id == Activity.id)
            .group_by(Activity.id, Activity.title, Activity.activity_type)
            .order_by(func.count(ActivitySignup.id).desc())
            .limit(10)
        )
        if act_filters:
            q = q.filter(*act_filters)
        rows = q.all()
        activity_ranking = [
            {
                'title': r[0],
                'activity_type': r[1],
                'participants': r[2],
            }
            for r in rows
        ]
    except Exception as e:
        logger.warning(f"activities 排名异常: {e}")

    return {
        'total_activities': total_activities,
        'total_participants': total_participants,
        'activity_ranking': activity_ranking,
    }


# ============================================================
# 6. 考勤汇总
# ============================================================
@router.get('/attendance')
def attendance_summary(semester: str = Query(None), db: Session = Depends(get_db)):
    """考勤汇总：总异常次数、按类型分类、按班级分组"""
    result = {
        'total_exceptions': 0,
        'by_type': {},
        'by_class': [],
    }
    try:
        q = db.query(StudentAttendanceException)
        if semester and semester != 'all':
            start, end = _semester_date_range(semester)
            if start and end:
                q = q.filter(
                    StudentAttendanceException.exception_date >= start,
                    StudentAttendanceException.exception_date <= end
                )
        result['total_exceptions'] = q.count()
    except Exception as e:
        logger.warning(f"attendance 总数异常: {e}")

    try:
        q = db.query(
            StudentAttendanceException.exception_type,
            func.count(StudentAttendanceException.id)
        ).group_by(StudentAttendanceException.exception_type)
        if semester and semester != 'all':
            start, end = _semester_date_range(semester)
            if start and end:
                q = q.filter(
                    StudentAttendanceException.exception_date >= start,
                    StudentAttendanceException.exception_date <= end
                )
        rows = q.all()
        result['by_type'] = {(t or '未知'): cnt for t, cnt in rows}
    except Exception as e:
        logger.warning(f"attendance 按类型异常: {e}")

    try:
        q = (
            db.query(
                ClassModel.class_name,
                func.count(StudentAttendanceException.id)
            )
            .join(Student, StudentAttendanceException.student_id == Student.id)
            .join(ClassModel, Student.class_id == ClassModel.id)
            .group_by(ClassModel.id, ClassModel.class_name)
        )
        if semester and semester != 'all':
            start, end = _semester_date_range(semester)
            if start and end:
                q = q.filter(
                    StudentAttendanceException.exception_date >= start,
                    StudentAttendanceException.exception_date <= end
                )
        rows = q.all()
        result['by_class'] = [
            {'class_name': name, 'count': cnt}
            for name, cnt in rows
        ]
    except Exception as e:
        logger.warning(f"attendance 按班级异常: {e}")

    return result


# ============================================================
# 7. 心理档案汇总
# ============================================================
@router.get('/psychology')
def psychology_summary(semester: str = Query(None), db: Session = Depends(get_db)):
    """心理档案汇总：关注等级、咨询次数、需跟进人数"""
    result = {
        'by_attention_level': {},
        'total_counseling_count': 0,
        'need_follow_up': 0,
    }

    psych_filters = []
    if semester and semester != 'all':
        start, end = _semester_date_range(semester)
        if start and end:
            psych_filters.append(PsychologyRecord.record_date >= start)
            psych_filters.append(PsychologyRecord.record_date <= end)

    try:
        q = (
            db.query(
                PsychologyRecord.attention_level,
                func.count(PsychologyRecord.student_id.distinct())
            )
            .group_by(PsychologyRecord.attention_level)
        )
        if psych_filters:
            q = q.filter(*psych_filters)
        rows = q.all()
        result['by_attention_level'] = {
            (level or '普通'): cnt for level, cnt in rows
        }
    except Exception as e:
        logger.warning(f"psychology 关注等级异常: {e}")

    try:
        q = db.query(func.sum(PsychologyRecord.counseling_count))
        if psych_filters:
            q = q.filter(*psych_filters)
        total = q.scalar()
        result['total_counseling_count'] = total or 0
    except Exception as e:
        logger.warning(f"psychology 咨询次数异常: {e}")

    try:
        today = datetime.now().strftime('%Y-%m-%d')
        q = (
            db.query(PsychologyRecord.student_id)
            .filter(
                PsychologyRecord.follow_up_plan != '',
                PsychologyRecord.follow_up_plan.isnot(None),
            )
            .distinct()
        )
        if psych_filters:
            q = q.filter(*psych_filters)
        need_follow = q.count()
        result['need_follow_up'] = need_follow or 0
    except Exception as e:
        logger.warning(f"psychology 跟进人数异常: {e}")

    return result


# ============================================================
# 8. 违纪统计
# ============================================================
@router.get('/discipline')
def discipline_summary(semester: str = Query(None), db: Session = Depends(get_db)):
    """违纪统计：按处分类型统计、涉及学生数"""
    result = {
        'by_type': {},
        'student_count': 0,
    }

    disc_filters = []
    if semester and semester != 'all':
        start, end = _semester_date_range(semester)
        if start and end:
            disc_filters.append(StudentDiscipline.discipline_date >= start)
            disc_filters.append(StudentDiscipline.discipline_date <= end)

    try:
        q = (
            db.query(
                StudentDiscipline.discipline_type,
                func.count(StudentDiscipline.id)
            )
            .group_by(StudentDiscipline.discipline_type)
        )
        if disc_filters:
            q = q.filter(*disc_filters)
        rows = q.all()
        result['by_type'] = {(t or '未知'): cnt for t, cnt in rows}
    except Exception as e:
        logger.warning(f"discipline 按类型异常: {e}")

    try:
        q = db.query(StudentDiscipline.student_id).distinct()
        if disc_filters:
            q = q.filter(*disc_filters)
        result['student_count'] = q.count()
    except Exception as e:
        logger.warning(f"discipline 学生数异常: {e}")

    return result


# ============================================================
# 9. 资助汇总
# ============================================================
@router.get('/financial-aid')
def financial_aid_summary(semester: str = Query(None), db: Session = Depends(get_db)):
    """资助汇总：困难认定、助学金、奖学金、贷款、勤工助学"""
    aid_year = _semester_to_academic_year(semester)
    result = {
        'hardship_by_level': {},
        'hardship_count': 0,
        'grant_total_amount': 0,
        'grant_count': 0,
        'scholarship_total_amount': 0,
        'scholarship_count': 0,
        'loan_total_amount': 0,
        'loan_count': 0,
        'work_study_count': 0,
        'work_study_total_compensation': 0,
    }

    try:
        q = db.query(
            StudentHardship.hardship_level,
            func.count(StudentHardship.id)
        ).group_by(StudentHardship.hardship_level)
        q_total = db.query(StudentHardship)
        if aid_year:
            q = q.filter(StudentHardship.academic_year == aid_year)
            q_total = q_total.filter(StudentHardship.academic_year == aid_year)
        rows = q.all()
        result['hardship_by_level'] = {(level or '未知'): cnt for level, cnt in rows}
        result['hardship_count'] = q_total.count()
    except Exception as e:
        logger.warning(f"financial-aid 困难认定异常: {e}")

    try:
        q = db.query(func.sum(StudentGrant.amount), func.count(StudentGrant.id))
        if aid_year:
            q = q.filter(StudentGrant.academic_year == aid_year)
        total_amount, count = q.first()
        result['grant_total_amount'] = total_amount or 0
        result['grant_count'] = count or 0
    except Exception as e:
        logger.warning(f"financial-aid 助学金异常: {e}")

    try:
        q = db.query(func.sum(StudentScholarship.amount), func.count(StudentScholarship.id))
        if aid_year:
            q = q.filter(StudentScholarship.academic_year == aid_year)
        total_amount, count = q.first()
        result['scholarship_total_amount'] = total_amount or 0
        result['scholarship_count'] = count or 0
    except Exception as e:
        logger.warning(f"financial-aid 奖学金异常: {e}")

    try:
        q = db.query(func.sum(StudentLoan.amount), func.count(StudentLoan.id))
        total_amount, count = q.first()
        result['loan_total_amount'] = total_amount or 0
        result['loan_count'] = count or 0
    except Exception as e:
        logger.warning(f"financial-aid 助学贷款异常: {e}")

    try:
        q = db.query(func.sum(StudentWorkStudy.compensation), func.count(StudentWorkStudy.id))
        if aid_year:
            q = q.filter(StudentWorkStudy.academic_year == aid_year)
        total_comp, count = q.first()
        result['work_study_total_compensation'] = total_comp or 0
        result['work_study_count'] = count or 0
    except Exception as e:
        logger.warning(f"financial-aid 勤工助学异常: {e}")

    return result


# ============================================================
# 10. 荣誉统计
# ============================================================
@router.get('/honors')
def honors_summary(semester: str = Query(None), db: Session = Depends(get_db)):
    """荣誉统计：按级别统计获奖人次、获奖学生数"""
    result = {
        'by_level': {},
        'student_count': 0,
    }

    honor_filters = []
    honor_year = _semester_to_academic_year(semester)
    if honor_year:
        honor_filters.append(StudentHonor.academic_year == honor_year)

    try:
        q = (
            db.query(
                StudentHonor.level,
                func.count(StudentHonor.id)
            )
            .group_by(StudentHonor.level)
        )
        if honor_filters:
            q = q.filter(*honor_filters)
        rows = q.all()
        result['by_level'] = {(level or '未知'): cnt for level, cnt in rows}
    except Exception as e:
        logger.warning(f"honors 按级别异常: {e}")

    try:
        q = db.query(StudentHonor.student_id).distinct()
        if honor_filters:
            q = q.filter(*honor_filters)
        result['student_count'] = q.count()
    except Exception as e:
        logger.warning(f"honors 学生数异常: {e}")

    return result


# ============================================================
# 11. 访谈统计
# ============================================================
@router.get('/interviews')
def interview_summary(semester: str = Query(None), db: Session = Depends(get_db)):
    """访谈统计：总次数、按类型、待跟进、访谈覆盖率"""
    result = {
        'total_count': 0,
        'by_type': {},
        'pending_count': 0,
        'covered_student_count': 0,
        'total_student_count': 0,
        'coverage_rate': 0.0,
    }

    interview_filters = []
    if semester and semester != 'all':
        start, end = _semester_date_range(semester)
        if start and end:
            interview_filters.append(StudentInterview.interview_date >= start)
            interview_filters.append(StudentInterview.interview_date <= end)

    try:
        q = db.query(StudentInterview)
        if interview_filters:
            q = q.filter(*interview_filters)
        result['total_count'] = q.count()
    except Exception as e:
        logger.warning(f"interviews 总数异常: {e}")

    try:
        q = (
            db.query(
                StudentInterview.interview_type,
                func.count(StudentInterview.id)
            )
            .group_by(StudentInterview.interview_type)
        )
        if interview_filters:
            q = q.filter(*interview_filters)
        rows = q.all()
        result['by_type'] = {(t or '未知'): cnt for t, cnt in rows}
    except Exception as e:
        logger.warning(f"interviews 按类型异常: {e}")

    try:
        q = db.query(StudentInterview).filter(StudentInterview.status == '需跟进')
        if interview_filters:
            q = q.filter(*interview_filters)
        result['pending_count'] = q.count()
    except Exception as e:
        logger.warning(f"interviews 待跟进异常: {e}")

    try:
        q_covered = db.query(StudentInterview.student_id).distinct()
        if interview_filters:
            q_covered = q_covered.filter(*interview_filters)
        covered = q_covered.count()
        total_students = db.query(Student).count()
        rate = round(covered / total_students * 100, 1) if total_students > 0 else 0.0
        result['covered_student_count'] = covered
        result['total_student_count'] = total_students
        result['coverage_rate'] = rate
    except Exception as e:
        logger.warning(f"interviews 覆盖率异常: {e}")

    return result


# ============================================================
# 12. 宿舍管理汇总
# ============================================================
@router.get('/dormitory')
def dormitory_summary(semester: str = Query(None), db: Session = Depends(get_db)):
    """宿舍管理汇总：走访、寝谈、请假统计"""
    result = {
        'visit_count': 0,
        'chat_count': 0,
        'leave_by_type': {},
        'leave_by_status': {},
        'leave_total': 0,
    }

    dorm_visit_filters = []
    dorm_chat_filters = []
    leave_filters = []
    if semester and semester != 'all':
        start, end = _semester_date_range(semester)
        if start and end:
            dorm_visit_filters.extend([StudentDormVisit.visit_date >= start, StudentDormVisit.visit_date <= end])
            dorm_chat_filters.extend([StudentDormChat.chat_date >= start, StudentDormChat.chat_date <= end])
            leave_filters.extend([StudentLeave.start_date >= start, StudentLeave.start_date <= end])

    try:
        q = db.query(StudentDormVisit)
        if dorm_visit_filters:
            q = q.filter(*dorm_visit_filters)
        result['visit_count'] = q.count()
    except Exception as e:
        logger.warning(f"dormitory 走访异常: {e}")

    try:
        q = db.query(StudentDormChat)
        if dorm_chat_filters:
            q = q.filter(*dorm_chat_filters)
        result['chat_count'] = q.count()
    except Exception as e:
        logger.warning(f"dormitory 寝谈异常: {e}")

    try:
        q = (
            db.query(StudentLeave.leave_type, func.count(StudentLeave.id))
            .group_by(StudentLeave.leave_type)
        )
        if leave_filters:
            q = q.filter(*leave_filters)
        rows = q.all()
        result['leave_by_type'] = {(t or '未知'): cnt for t, cnt in rows}
    except Exception as e:
        logger.warning(f"dormitory 请假按类型异常: {e}")

    try:
        q = (
            db.query(StudentLeave.approval_status, func.count(StudentLeave.id))
            .group_by(StudentLeave.approval_status)
        )
        if leave_filters:
            q = q.filter(*leave_filters)
        rows = q.all()
        status_labels = {'pending': '待审批', 'approved': '已批准', 'rejected': '已驳回'}
        result['leave_by_status'] = {
            status_labels.get(s, s or '未知'): cnt for s, cnt in rows
        }
    except Exception as e:
        logger.warning(f"dormitory 请假按状态异常: {e}")

    try:
        q = db.query(StudentLeave)
        if leave_filters:
            q = q.filter(*leave_filters)
        result['leave_total'] = q.count()
    except Exception as e:
        logger.warning(f"dormitory 请假总数异常: {e}")

    return result


# ============================================================
# 13. 导出 Excel
# ============================================================
@router.get('/export')
def export_endpoint(semester: str = Query(None), db: Session = Depends(get_db)):
    """导出学期报表为 Excel（多 Sheet）"""
    return _export_semester_report(semester, db)


# ============================================================
# 14. 学期差值统计
# ============================================================
@router.get('/compare')
def semester_compare(semester: str = Query(None), db: Session = Depends(get_db)):
    """与上一学期对比"""
    if not semester or semester == 'all':
        return {'comparison': {}}

    parts = semester.split('-')
    if len(parts) != 3:
        return {'comparison': {}}

    try:
        y1, y2, term = int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        return {'comparison': {}}

    if term == 2:
        prev_semester = f"{y1}-{y2}-1"
    else:
        prev_semester = f"{y1-1}-{y1}-2"

    result = {
        'current_semester': semester,
        'prev_semester': prev_semester,
        'comparison': {}
    }

    metrics = [
        'avg_score', 'fail_rate', 'warning_count', 'activity_participants',
        'attendance_exception_count', 'psychology_attention_count',
        'financial_aid_count', 'discipline_count', 'honor_count',
        'interview_count', 'interview_coverage',
        'leave_count', 'dormitory_visit_count',
    ]

    for metric in metrics:
        curr_val = _get_semester_metric(db, semester, metric)
        prev_val = _get_semester_metric(db, prev_semester, metric)

        if curr_val is not None and prev_val is not None:
            diff = curr_val - prev_val
            pct = (diff / prev_val * 100) if prev_val != 0 else 0
            result['comparison'][metric] = {
                'current': round(curr_val, 2),
                'previous': round(prev_val, 2),
                'diff': round(diff, 2),
                'change_pct': round(pct, 1)
            }
        else:
            result['comparison'][metric] = None

    # 党员人数变化（累计值差值）
    try:
        curr_party = _get_cumulative_party_member_count(db, semester)
        prev_party = _get_cumulative_party_member_count(db, prev_semester)
        diff = curr_party - prev_party
        pct = (diff / prev_party * 100) if prev_party != 0 else 0
        result['comparison']['party_member_change'] = {
            'current': curr_party,
            'previous': prev_party,
            'diff': diff,
            'change_pct': round(pct, 1)
        }
    except Exception as e:
        logger.warning(f"party_member_change 异常: {e}")
        result['comparison']['party_member_change'] = None

    return result
