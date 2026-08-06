"""学期报表查询辅助函数"""
import logging
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import (
    Student, GradeRecord, WarningRecord, PartyProgress,
    EmploymentRecord, Activity, ActivitySignup,
    PsychologyRecord, StudentDiscipline, StudentHardship,
    StudentGrant, StudentScholarship, StudentLoan, StudentWorkStudy,
    StudentHonor, StudentDormVisit, StudentLeave, StudentInterview,
    StudentAttendanceException
)
from routers.semester_report_utils import _semester_date_range, _semester_to_academic_year

logger = logging.getLogger(__name__)


def _get_cumulative_party_member_count(db, semester):
    """获取截止到指定学期结束的累计党员数"""
    from routers.utils import semester_to_date_range
    try:
        _subq = db.query(
            PartyProgress.student_id,
            func.max(PartyProgress.id).label('max_id')
        )
        if semester and semester != 'all':
            _start, _end = semester_to_date_range(semester)
            if _end:
                _subq = _subq.filter(PartyProgress.stage_date <= _end)
        _subq = _subq.group_by(PartyProgress.student_id).subquery()
        count = (
            db.query(func.count(PartyProgress.student_id))
            .join(_subq, PartyProgress.id == _subq.c.max_id)
            .filter(PartyProgress.stage.in_(['中共预备党员', '中共党员']))
            .scalar() or 0
        )
        return count
    except Exception as e:
        logger.warning(f"累计党员数异常: {e}")
        return 0


def _get_semester_metric(db: Session, semester: str, metric: str):
    """获取指定学期的某个指标值"""
    try:
        if metric == 'avg_score':
            rows = db.query(func.avg(GradeRecord.score)).filter(
                GradeRecord.semester == semester,
                GradeRecord.score.isnot(None)
            ).all()
            return rows[0][0] if rows and rows[0][0] else None
        elif metric == 'fail_rate':
            total = db.query(GradeRecord.student_id).filter(
                GradeRecord.semester == semester,
                GradeRecord.score.isnot(None)
            ).distinct().count()
            if total == 0:
                return None
            fail = db.query(GradeRecord.student_id).filter(
                GradeRecord.semester == semester,
                GradeRecord.score < 60
            ).distinct().count()
            return fail / total * 100
        elif metric == 'warning_count':
            return db.query(WarningRecord).filter(
                WarningRecord.semester == semester
            ).count()
        elif metric == 'activity_participants':
            start, end = _semester_date_range(semester)
            if not start or not end:
                return None
            return db.query(func.count(ActivitySignup.id)).join(Activity).filter(
                Activity.activity_date >= start,
                Activity.activity_date <= end
            ).scalar() or 0
        elif metric == 'attendance_exception_count':
            start, end = _semester_date_range(semester)
            if not start or not end:
                return None
            return db.query(StudentAttendanceException).filter(
                StudentAttendanceException.exception_date >= start,
                StudentAttendanceException.exception_date <= end
            ).count()
        elif metric == 'psychology_attention_count':
            start, end = _semester_date_range(semester)
            if not start or not end:
                return None
            return db.query(PsychologyRecord.student_id).filter(
                PsychologyRecord.attention_level.in_(['一级关注', '二级关注', '三级关注']),
                PsychologyRecord.record_date >= start,
                PsychologyRecord.record_date <= end
            ).distinct().count()
        elif metric == 'financial_aid_count':
            aid_year = _semester_to_academic_year(semester)
            if not aid_year:
                return None
            cnt = 0
            cnt += db.query(StudentHardship).filter(StudentHardship.academic_year == aid_year).count()
            cnt += db.query(StudentGrant).filter(StudentGrant.academic_year == aid_year).count()
            cnt += db.query(StudentScholarship).filter(StudentScholarship.academic_year == aid_year).count()
            cnt += db.query(StudentLoan).count()  # 贷款无学年字段
            cnt += db.query(StudentWorkStudy).filter(StudentWorkStudy.academic_year == aid_year).count()
            return cnt
        elif metric == 'discipline_count':
            start, end = _semester_date_range(semester)
            if not start or not end:
                return None
            return db.query(StudentDiscipline.student_id).filter(
                StudentDiscipline.discipline_date >= start,
                StudentDiscipline.discipline_date <= end
            ).distinct().count()
        elif metric == 'honor_count':
            honor_year = _semester_to_academic_year(semester)
            if not honor_year:
                return None
            return db.query(StudentHonor).filter(
                StudentHonor.academic_year == honor_year
            ).count()
        elif metric == 'interview_count':
            start, end = _semester_date_range(semester)
            if not start or not end:
                return None
            return db.query(StudentInterview).filter(
                StudentInterview.interview_date >= start,
                StudentInterview.interview_date <= end
            ).count()
        elif metric == 'interview_coverage':
            start, end = _semester_date_range(semester)
            if not start or not end:
                return None
            total_students = db.query(Student).count()
            if total_students == 0:
                return None
            covered = db.query(StudentInterview.student_id).filter(
                StudentInterview.interview_date >= start,
                StudentInterview.interview_date <= end
            ).distinct().count()
            return covered / total_students * 100
        elif metric == 'leave_count':
            start, end = _semester_date_range(semester)
            if not start or not end:
                return None
            return db.query(StudentLeave).filter(
                StudentLeave.start_date >= start,
                StudentLeave.start_date <= end
            ).count()
        elif metric == 'dormitory_visit_count':
            start, end = _semester_date_range(semester)
            if not start or not end:
                return None
            return db.query(StudentDormVisit).filter(
                StudentDormVisit.visit_date >= start,
                StudentDormVisit.visit_date <= end
            ).count()
    except Exception as e:
        logger.warning(f"获取指标 {metric} 异常: {e}")
    return None
