"""学期报表 API - V5-f
聚合学期总览、学业、党团、就业、活动数据，支持 Excel 导出
"""
import io
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, case, distinct
from sqlalchemy.orm import Session
from database import get_db
from models import (
    Student, ClassModel, Major, GradeRecord, WarningRecord,
    PartyProgress, EmploymentRecord, Activity, ActivitySignup
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/semester-report', tags=['学期报表'])


# ============================================================
# 1. 学期总览
# ============================================================
@router.get('/summary')
def semester_summary(db: Session = Depends(get_db)):
    """学期总览：学生数、班级数、专业数、政治面貌、性别、住宿、校区"""
    result = {
        'total_students': 0,
        'total_classes': 0,
        'total_majors': 0,
        'political_distribution': {},
        'gender_distribution': {},
        'housing_distribution': {'外宿': 0, '住校': 0},
        'campus_distribution': {},
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

    # 外宿 / 住校
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

    return result


# ============================================================
# 2. 学业数据
# ============================================================
@router.get('/academics')
def semester_academics(db: Session = Depends(get_db)):
    """学业汇总：各班平均成绩、挂科率、Top10、预警统计"""
    result = {
        'class_averages': [],
        'fail_rate': 0.0,
        'fail_count': 0,
        'total_students_with_grades': 0,
        'top10': [],
        'warning_stats': {'red': 0, 'yellow': 0, 'total': 0},
    }

    # 各班平均成绩
    try:
        rows = (
            db.query(
                ClassModel.class_name,
                func.avg(GradeRecord.score)
            )
            .join(Student, Student.class_id == ClassModel.id)
            .join(GradeRecord, GradeRecord.student_id == Student.id)
            .filter(GradeRecord.score.isnot(None))
            .group_by(ClassModel.id, ClassModel.class_name)
            .all()
        )
        result['class_averages'] = [
            {'class_name': name, 'avg_score': round(avg, 2) if avg else 0}
            for name, avg in rows
        ]
    except Exception as e:
        logger.warning(f"academics 班级平均异常: {e}")

    # 挂科率（有不及格记录的学生占比）
    try:
        total_with_grades = (
            db.query(func.count(distinct(GradeRecord.student_id)))
            .scalar() or 0
        )
        fail_students = (
            db.query(func.count(distinct(GradeRecord.student_id)))
            .filter(GradeRecord.score.isnot(None), GradeRecord.score < 60)
            .scalar() or 0
        )
        result['total_students_with_grades'] = total_with_grades
        result['fail_count'] = fail_students
        result['fail_rate'] = (
            round(fail_students / total_with_grades * 100, 2)
            if total_with_grades > 0 else 0.0
        )
    except Exception as e:
        logger.warning(f"academics 挂科率异常: {e}")

    # 成绩排名 Top 10
    try:
        rows = (
            db.query(
                Student.student_no,
                Student.name,
                func.avg(GradeRecord.score).label('avg_score')
            )
            .join(GradeRecord, GradeRecord.student_id == Student.id)
            .filter(GradeRecord.score.isnot(None))
            .group_by(Student.id, Student.student_no, Student.name)
            .order_by(func.avg(GradeRecord.score).desc())
            .limit(10)
            .all()
        )
        result['top10'] = [
            {
                'student_no': r[0],
                'name': r[1],
                'avg_score': round(r[2], 2) if r[2] else 0
            }
            for r in rows
        ]
    except Exception as e:
        logger.warning(f"academics Top10 异常: {e}")

    # 学业预警统计
    try:
        red = db.query(WarningRecord).filter(WarningRecord.warning_type == 'red').count()
        yellow = db.query(WarningRecord).filter(WarningRecord.warning_type == 'yellow').count()
        result['warning_stats'] = {
            'red': red,
            'yellow': yellow,
            'total': red + yellow,
        }
    except Exception as e:
        logger.warning(f"academics 预警异常: {e}")

    return result


# ============================================================
# 3. 党团发展
# ============================================================
@router.get('/party-development')
def party_development(db: Session = Depends(get_db)):
    """党团发展进度：各阶段人数 + 本学期新发展人数"""
    stage_map = {
        '递交入党申请书': 0,
        '入党积极分子': 0,
        '发展对象': 0,
        '中共预备党员': 0,
        '中共党员': 0,
    }
    total_new_this_semester = 0

    # 各阶段最新人数（取每个学生最新 stage）
    try:
        # 每个学生的最新 party_progress（按 id 降序取第一条）
        subq = (
            db.query(
                PartyProgress.student_id,
                func.max(PartyProgress.id).label('max_id')
            )
            .group_by(PartyProgress.student_id)
            .subquery()
        )
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

    # 本学期新发展人数（stage_date 在当前学期范围）
    try:
        now = datetime.now()
        if now.month >= 9:
            sem_start = f"{now.year}-09-01"
        else:
            sem_start = f"{now.year}-03-01"
        total_new_this_semester = (
            db.query(func.count(PartyProgress.id))
            .filter(PartyProgress.stage_date >= sem_start)
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
def employment_stats(db: Session = Depends(get_db)):
    """就业状态分布与就业率"""
    status_map = {
        '已签约': 0,
        '考研': 0,
        '出国': 0,
        '待就业': 0,
        '未知': 0,
    }
    total = 0

    try:
        rows = (
            db.query(EmploymentRecord.status, func.count(EmploymentRecord.id))
            .group_by(EmploymentRecord.status)
            .all()
        )
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

    # 就业率 = 已签约 / total
    employed = status_map.get('已签约', 0)
    employment_rate = round(employed / total * 100, 2) if total > 0 else 0.0

    return {
        'distribution': status_map,
        'total_records': total,
        'employment_rate': employment_rate,
    }


# ============================================================
# 5. 学生活动
# ============================================================
@router.get('/activities')
def activity_stats(db: Session = Depends(get_db)):
    """活动总数、参与人次、各活动参与人数排名"""
    total_activities = 0
    total_participants = 0
    activity_ranking = []

    try:
        total_activities = db.query(Activity).count()
    except Exception as e:
        logger.warning(f"activities 总数异常: {e}")

    try:
        total_participants = db.query(ActivitySignup).count()
    except Exception as e:
        logger.warning(f"activities 人次异常: {e}")

    try:
        rows = (
            db.query(
                Activity.title,
                Activity.activity_type,
                func.count(ActivitySignup.id).label('participants')
            )
            .join(ActivitySignup, ActivitySignup.activity_id == Activity.id)
            .group_by(Activity.id, Activity.title, Activity.activity_type)
            .order_by(func.count(ActivitySignup.id).desc())
            .limit(20)
            .all()
        )
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
# 6. 导出 Excel
# ============================================================
@router.get('/export')
def export_semester_report(db: Session = Depends(get_db)):
    """导出学期报表为 Excel（多 Sheet）- 空数据时返回空白模板不报 500"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
    except ImportError:
        raise HTTPException(500, 'openpyxl 未安装，无法导出 Excel，请在 requirements.txt 中添加 openpyxl')

    wb = Workbook()

    # ---------- 样式 ----------
    header_font = Font(bold=True, size=12, color='FFFFFF')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_align = Alignment(horizontal='center', vertical='center')
    title_font = Font(bold=True, size=14)

    def write_title(ws, title, col=3):
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=col)
        cell = ws.cell(row=1, column=1, value=title)
        cell.font = title_font
        cell.alignment = Alignment(horizontal='center')

    def write_headers(ws, row, headers):
        for i, h in enumerate(headers, 1):
            cell = ws.cell(row=row, column=i, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align

    # ==================== Sheet 1: 总览 ====================
    ws1 = wb.active
    ws1.title = '总览'
    write_title(ws1, '学期总览')

    # 基础数据
    try:
        total_students = db.query(Student).count()
        total_classes = db.query(ClassModel).count()
        total_majors = db.query(Major).count()
    except Exception:
        total_students = total_classes = total_majors = 0

    r = 3
    ws1.cell(row=r, column=1, value='指标')
    ws1.cell(row=r, column=2, value='数值')
    ws1.cell(row=r, column=1).font = header_font
    ws1.cell(row=r, column=2).font = header_font
    for label, val in [('学生总数', total_students), ('班级数', total_classes), ('专业数', total_majors)]:
        r += 1
        ws1.cell(row=r, column=1, value=label)
        ws1.cell(row=r, column=2, value=val)

    # 政治面貌
    r += 2
    ws1.cell(row=r, column=1, value='政治面貌分布')
    ws1.cell(row=r, column=1).font = Font(bold=True, size=12)
    r += 1
    write_headers(ws1, r, ['政治面貌', '人数'])
    try:
        rows = (
            db.query(Student.political_status, func.count(Student.id))
            .group_by(Student.political_status)
            .all()
        )
        for status, cnt in rows:
            r += 1
            ws1.cell(row=r, column=1, value=status or '群众')
            ws1.cell(row=r, column=2, value=cnt)
    except Exception:
        pass

    # 性别
    r += 2
    ws1.cell(row=r, column=1, value='性别分布')
    ws1.cell(row=r, column=1).font = Font(bold=True, size=12)
    r += 1
    write_headers(ws1, r, ['性别', '人数'])
    try:
        rows = (
            db.query(Student.gender, func.count(Student.id))
            .group_by(Student.gender)
            .all()
        )
        for g, cnt in rows:
            r += 1
            ws1.cell(row=r, column=1, value=g or '未知')
            ws1.cell(row=r, column=2, value=cnt)
    except Exception:
        pass

    # 住宿
    r += 2
    ws1.cell(row=r, column=1, value='住宿分布')
    ws1.cell(row=r, column=1).font = Font(bold=True, size=12)
    r += 1
    write_headers(ws1, r, ['类型', '人数'])
    try:
        off = db.query(Student).filter(Student.is_off_campus == True).count()
        ws1.cell(row=r+1, column=1, value='住校')
        ws1.cell(row=r+1, column=2, value=total_students - off)
        ws1.cell(row=r+2, column=1, value='外宿')
        ws1.cell(row=r+2, column=2, value=off)
        r += 2
    except Exception:
        pass

    # 校区
    r += 2
    ws1.cell(row=r, column=1, value='校区分布')
    ws1.cell(row=r, column=1).font = Font(bold=True, size=12)
    r += 1
    write_headers(ws1, r, ['校区', '人数'])
    try:
        rows = (
            db.query(Student.campus, func.count(Student.id))
            .group_by(Student.campus)
            .all()
        )
        for c, cnt in rows:
            r += 1
            ws1.cell(row=r, column=1, value=c or '未知')
            ws1.cell(row=r, column=2, value=cnt)
    except Exception:
        pass

    # ==================== Sheet 2: 学业 ====================
    ws2 = wb.create_sheet('学业')
    write_title(ws2, '学业数据汇总')

    r = 3
    ws2.cell(row=r, column=1, value='班级')
    ws2.cell(row=r, column=2, value='平均成绩')
    ws2.cell(row=r, column=1).font = header_font
    ws2.cell(row=r, column=2).font = header_font
    try:
        rows = (
            db.query(
                ClassModel.class_name,
                func.avg(GradeRecord.score)
            )
            .join(Student, Student.class_id == ClassModel.id)
            .join(GradeRecord, GradeRecord.student_id == Student.id)
            .filter(GradeRecord.score.isnot(None))
            .group_by(ClassModel.id, ClassModel.class_name)
            .all()
        )
        for name, avg in rows:
            r += 1
            ws2.cell(row=r, column=1, value=name)
            ws2.cell(row=r, column=2, value=round(avg, 2) if avg else 0)
    except Exception:
        pass

    # 挂科率
    r += 2
    ws2.cell(row=r, column=1, value='挂科统计')
    ws2.cell(row=r, column=1).font = Font(bold=True, size=12)
    r += 1
    try:
        total_with_grades = (
            db.query(func.count(distinct(GradeRecord.student_id))).scalar() or 0
        )
        fail_students = (
            db.query(func.count(distinct(GradeRecord.student_id)))
            .filter(GradeRecord.score.isnot(None), GradeRecord.score < 60)
            .scalar() or 0
        )
        fail_rate = round(fail_students / total_with_grades * 100, 2) if total_with_grades > 0 else 0.0
        ws2.cell(row=r, column=1, value='有成绩学生数')
        ws2.cell(row=r, column=2, value=total_with_grades)
        r += 1
        ws2.cell(row=r, column=1, value='挂科学生数')
        ws2.cell(row=r, column=2, value=fail_students)
        r += 1
        ws2.cell(row=r, column=1, value='挂科率(%)')
        ws2.cell(row=r, column=2, value=fail_rate)
    except Exception:
        pass

    # Top10
    r += 2
    ws2.cell(row=r, column=1, value='成绩排名 Top 10')
    ws2.cell(row=r, column=1).font = Font(bold=True, size=12)
    r += 1
    write_headers(ws2, r, ['排名', '学号', '姓名', '平均成绩'])
    try:
        rows = (
            db.query(
                Student.student_no,
                Student.name,
                func.avg(GradeRecord.score)
            )
            .join(GradeRecord, GradeRecord.student_id == Student.id)
            .filter(GradeRecord.score.isnot(None))
            .group_by(Student.id, Student.student_no, Student.name)
            .order_by(func.avg(GradeRecord.score).desc())
            .limit(10)
            .all()
        )
        for idx, (sno, sname, avg) in enumerate(rows, 1):
            r += 1
            ws2.cell(row=r, column=1, value=idx)
            ws2.cell(row=r, column=2, value=sno)
            ws2.cell(row=r, column=3, value=sname)
            ws2.cell(row=r, column=4, value=round(avg, 2) if avg else 0)
    except Exception:
        pass

    # 预警
    r += 2
    ws2.cell(row=r, column=1, value='学业预警统计')
    ws2.cell(row=r, column=1).font = Font(bold=True, size=12)
    r += 1
    write_headers(ws2, r, ['预警等级', '人数'])
    try:
        red = db.query(WarningRecord).filter(WarningRecord.warning_type == 'red').count()
        yellow = db.query(WarningRecord).filter(WarningRecord.warning_type == 'yellow').count()
        r += 1
        ws2.cell(row=r, column=1, value='红色预警')
        ws2.cell(row=r, column=2, value=red)
        r += 1
        ws2.cell(row=r, column=1, value='黄色预警')
        ws2.cell(row=r, column=2, value=yellow)
        r += 1
        ws2.cell(row=r, column=1, value='合计')
        ws2.cell(row=r, column=2, value=red + yellow)
    except Exception:
        pass

    # ==================== Sheet 3: 党团 ====================
    ws3 = wb.create_sheet('党团')
    write_title(ws3, '党团发展进度')

    r = 3
    write_headers(ws3, r, ['阶段', '人数'])
    try:
        subq = (
            db.query(
                PartyProgress.student_id,
                func.max(PartyProgress.id).label('max_id')
            )
            .group_by(PartyProgress.student_id)
            .subquery()
        )
        rows = (
            db.query(PartyProgress.stage, func.count(PartyProgress.student_id))
            .join(subq, PartyProgress.id == subq.c.max_id)
            .group_by(PartyProgress.stage)
            .all()
        )
        for stage, cnt in rows:
            r += 1
            ws3.cell(row=r, column=1, value=stage)
            ws3.cell(row=r, column=2, value=cnt)
    except Exception:
        pass

    # 本学期新发展
    r += 2
    try:
        now = datetime.now()
        sem_start = f"{now.year}-09-01" if now.month >= 9 else f"{now.year}-03-01"
        new_cnt = (
            db.query(func.count(PartyProgress.id))
            .filter(PartyProgress.stage_date >= sem_start)
            .scalar() or 0
        )
        ws3.cell(row=r, column=1, value='本学期新发展人数')
        ws3.cell(row=r, column=2, value=new_cnt)
    except Exception:
        pass

    # ==================== Sheet 4: 就业 ====================
    ws4 = wb.create_sheet('就业')
    write_title(ws4, '就业跟踪统计')

    r = 3
    write_headers(ws4, r, ['就业状态', '人数'])
    try:
        rows = (
            db.query(EmploymentRecord.status, func.count(EmploymentRecord.id))
            .group_by(EmploymentRecord.status)
            .all()
        )
        total_emp = sum(cnt for _, cnt in rows)
        for status, cnt in rows:
            r += 1
            ws4.cell(row=r, column=1, value=status or '未知')
            ws4.cell(row=r, column=2, value=cnt)
        r += 1
        ws4.cell(row=r, column=1, value='合计')
        ws4.cell(row=r, column=2, value=total_emp)
        r += 1
        employed = sum(cnt for s, cnt in rows if s == '已签约')
        rate = round(employed / total_emp * 100, 2) if total_emp > 0 else 0.0
        ws4.cell(row=r, column=1, value='就业率(%)')
        ws4.cell(row=r, column=2, value=rate)
    except Exception:
        pass

    # ==================== Sheet 5: 活动 ====================
    ws5 = wb.create_sheet('活动')
    write_title(ws5, '学生活动统计')

    r = 3
    try:
        total_act = db.query(Activity).count()
        total_ppl = db.query(ActivitySignup).count()
    except Exception:
        total_act = total_ppl = 0

    ws5.cell(row=r, column=1, value='活动总数')
    ws5.cell(row=r, column=2, value=total_act)
    r += 1
    ws5.cell(row=r, column=1, value='参与人次')
    ws5.cell(row=r, column=2, value=total_ppl)

    r += 2
    ws5.cell(row=r, column=1, value='活动参与人数排名')
    ws5.cell(row=r, column=1).font = Font(bold=True, size=12)
    r += 1
    write_headers(ws5, r, ['活动名称', '类型', '参与人数'])
    try:
        rows = (
            db.query(
                Activity.title,
                Activity.activity_type,
                func.count(ActivitySignup.id)
            )
            .join(ActivitySignup, ActivitySignup.activity_id == Activity.id)
            .group_by(Activity.id, Activity.title, Activity.activity_type)
            .order_by(func.count(ActivitySignup.id).desc())
            .limit(20)
            .all()
        )
        for title, atype, cnt in rows:
            r += 1
            ws5.cell(row=r, column=1, value=title)
            ws5.cell(row=r, column=2, value=atype or '')
            ws5.cell(row=r, column=3, value=cnt)
    except Exception:
        pass

    # ---------- 写入 buffer 并返回 ----------
    try:
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
    except Exception as e:
        logger.error(f'semester report export save failed: {e}')
        raise HTTPException(500, f'Excel 生成失败: {type(e).__name__}: {str(e)}')

    filename = f"学期报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        buf,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
