"""奖助贷模块路由 — 困难认定 / 助学金 / 奖学金 / 助学贷款 / 勤工助学 / 评优评先"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Optional
from database import get_db
from models import (
    Student, StudentHardship, StudentGrant, StudentScholarship,
    StudentLoan, StudentWorkStudy, StudentHonor, ClassModel,
)

router = APIRouter(prefix='/api/financial-aid')


# ===== 1. 总览统计 =====
@router.get('/summary')
def financial_aid_summary(db: Session = Depends(get_db)):
    """奖助贷总览统计"""
    hardship_count = db.query(func.count(StudentHardship.id)).scalar() or 0
    grant_count = db.query(func.count(StudentGrant.id)).scalar() or 0
    scholarship_count = db.query(func.count(StudentScholarship.id)).scalar() or 0
    loan_count = db.query(func.count(StudentLoan.id)).scalar() or 0
    work_study_count = db.query(func.count(StudentWorkStudy.id)).scalar() or 0
    honor_count = db.query(func.count(StudentHonor.id)).scalar() or 0

    # 总金额 = 助学金 + 奖学金 + 贷款 + 勤工助学报酬
    grant_total = db.query(func.coalesce(func.sum(StudentGrant.amount), 0)).scalar() or 0
    scholarship_total = db.query(func.coalesce(func.sum(StudentScholarship.amount), 0)).scalar() or 0
    loan_total = db.query(func.coalesce(func.sum(StudentLoan.amount), 0)).scalar() or 0
    work_total = db.query(func.coalesce(func.sum(StudentWorkStudy.compensation), 0)).scalar() or 0
    total_amount = float(grant_total) + float(scholarship_total) + float(loan_total) + float(work_total)

    # 覆盖率 = 获得过资助的不重复学生数 / 总学生数
    total_students = db.query(func.count(Student.id)).scalar() or 1
    aided_ids = set()
    for model in [StudentHardship, StudentGrant, StudentScholarship, StudentLoan, StudentWorkStudy, StudentHonor]:
        ids = db.query(distinct(model.student_id)).all()
        aided_ids.update(id for (id,) in ids)
    coverage_rate = round(len(aided_ids) / total_students, 4) if total_students else 0

    return {
        'hardship_count': hardship_count,
        'grant_count': grant_count,
        'scholarship_count': scholarship_count,
        'loan_count': loan_count,
        'work_study_count': work_study_count,
        'honor_count': honor_count,
        'total_amount': total_amount,
        'coverage_rate': coverage_rate,
    }


# ===== 2. 图表数据 =====
@router.get('/chart-data')
def financial_aid_chart_data(db: Session = Depends(get_db)):
    """奖助贷图表数据"""
    # 2a. 困难等级分布
    hardship_distribution = [
        {'level': row.hardship_level, 'count': row.cnt}
        for row in db.query(
            StudentHardship.hardship_level,
            func.count(StudentHardship.id).label('cnt')
        ).group_by(StudentHardship.hardship_level).all()
    ]

    # 2b. 助学金按类型
    grant_by_type = [
        {'type': row.grant_type, 'count': row.cnt, 'amount': float(row.amt or 0)}
        for row in db.query(
            StudentGrant.grant_type,
            func.count(StudentGrant.id).label('cnt'),
            func.sum(StudentGrant.amount).label('amt')
        ).group_by(StudentGrant.grant_type).all()
    ]

    # 2c. 奖学金按类型
    scholarship_by_type = [
        {'type': row.scholarship_type, 'count': row.cnt, 'amount': float(row.amt or 0)}
        for row in db.query(
            StudentScholarship.scholarship_type,
            func.count(StudentScholarship.id).label('cnt'),
            func.sum(StudentScholarship.amount).label('amt')
        ).group_by(StudentScholarship.scholarship_type).all()
    ]

    # 2d. 荣誉级别分布
    honor_by_level = [
        {'level': row.level, 'count': row.cnt}
        for row in db.query(
            StudentHonor.level,
            func.count(StudentHonor.id).label('cnt')
        ).group_by(StudentHonor.level).all()
    ]

    # 2e. 贷款类型分布
    loan_by_type = [
        {'type': row.loan_type, 'count': row.cnt, 'amount': float(row.amt or 0)}
        for row in db.query(
            StudentLoan.loan_type,
            func.count(StudentLoan.id).label('cnt'),
            func.sum(StudentLoan.amount).label('amt')
        ).group_by(StudentLoan.loan_type).all()
    ]

    # 2f. 勤工助学统计
    work_study_stats = [
        {'position': row.position, 'count': row.cnt, 'hours': float(row.hrs or 0)}
        for row in db.query(
            StudentWorkStudy.position,
            func.count(StudentWorkStudy.id).label('cnt'),
            func.sum(StudentWorkStudy.hours).label('hrs')
        ).group_by(StudentWorkStudy.position).all()
    ]

    # 2g. 学年资助趋势（合并助学金+奖学金+贷款+勤工助学金额）
    year_amounts = {}
    for model, amount_col in [
        (StudentGrant, StudentGrant.amount),
        (StudentScholarship, StudentScholarship.amount),
        (StudentWorkStudy, StudentWorkStudy.compensation),
    ]:
        for row in db.query(
            model.academic_year,
            func.sum(amount_col).label('amt')
        ).group_by(model.academic_year).all():
            if row.academic_year:
                year_amounts[row.academic_year] = year_amounts.get(row.academic_year, 0) + float(row.amt or 0)
    yearly_trend = [
        {'year': y, 'total_amount': round(a, 2)}
        for y, a in sorted(year_amounts.items())
    ]

    # 2h. TOP资助学生（助学金+奖学金+勤工助学 金额合计前5）
    student_amounts = {}
    for model, amount_col in [
        (StudentGrant, StudentGrant.amount),
        (StudentScholarship, StudentScholarship.amount),
        (StudentWorkStudy, StudentWorkStudy.compensation),
    ]:
        for row in db.query(
            model.student_id,
            func.sum(amount_col).label('amt')
        ).group_by(model.student_id).all():
            student_amounts[row.student_id] = student_amounts.get(row.student_id, 0) + float(row.amt or 0)

    top_ids = sorted(student_amounts, key=student_amounts.get, reverse=True)[:5]
    top_recipients = []
    for sid in top_ids:
        stu = db.get(Student, sid)
        if stu:
            top_recipients.append({
                'student_name': stu.name,
                'student_no': stu.student_no,
                'total_amount': round(student_amounts[sid], 2),
            })

    return {
        'hardship_distribution': hardship_distribution,
        'grant_by_type': grant_by_type,
        'scholarship_by_type': scholarship_by_type,
        'honor_by_level': honor_by_level,
        'loan_by_type': loan_by_type,
        'work_study_stats': work_study_stats,
        'yearly_trend': yearly_trend,
        'top_recipients': top_recipients,
    }


# ===== 3. 综合列表（分页 + 筛选） =====
@router.get('/list')
def financial_aid_list(
    search: str = Query('', description='搜索学号/姓名'),
    aid_type: Optional[str] = Query(None, description='hardship/grant/scholarship/loan/work_study/honor'),
    academic_year: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """奖助贷综合列表，支持分页和筛选"""
    class_map = {c.id: c.class_name for c in db.query(ClassModel).all()}
    items = []

    def _base_student_filter(q):
        if search:
            pattern = f'%{search.strip()}%'
            q = q.filter(
                (Student.name.ilike(pattern)) | (Student.student_no.ilike(pattern))
            )
        return q

    def _add_student_info(row_dict, student_id):
        stu = db.get(Student, student_id)
        if stu:
            row_dict['student_name'] = stu.name
            row_dict['student_no'] = stu.student_no
            row_dict['class_name'] = class_map.get(stu.class_id, '')
        else:
            row_dict['student_name'] = ''
            row_dict['student_no'] = ''
            row_dict['class_name'] = ''

    types_to_query = [aid_type] if aid_type else ['hardship', 'grant', 'scholarship', 'loan', 'work_study', 'honor']

    for t in types_to_query:
        if t == 'hardship':
            q = db.query(StudentHardship).join(Student, StudentHardship.student_id == Student.id)
            q = _base_student_filter(q)
            if academic_year:
                q = q.filter(StudentHardship.academic_year == academic_year)
            for row in q.order_by(StudentHardship.created_at.desc()).all():
                d = {
                    'id': row.id, 'aid_type': 'hardship', 'aid_type_label': '困难认定',
                    'detail': row.hardship_level or '',
                    'amount': 0, 'academic_year': row.academic_year or '',
                }
                _add_student_info(d, row.student_id)
                items.append(d)

        elif t == 'grant':
            q = db.query(StudentGrant).join(Student, StudentGrant.student_id == Student.id)
            q = _base_student_filter(q)
            if academic_year:
                q = q.filter(StudentGrant.academic_year == academic_year)
            for row in q.order_by(StudentGrant.created_at.desc()).all():
                d = {
                    'id': row.id, 'aid_type': 'grant', 'aid_type_label': '助学金',
                    'detail': row.grant_type or '',
                    'amount': float(row.amount or 0), 'academic_year': row.academic_year or '',
                }
                _add_student_info(d, row.student_id)
                items.append(d)

        elif t == 'scholarship':
            q = db.query(StudentScholarship).join(Student, StudentScholarship.student_id == Student.id)
            q = _base_student_filter(q)
            if academic_year:
                q = q.filter(StudentScholarship.academic_year == academic_year)
            for row in q.order_by(StudentScholarship.created_at.desc()).all():
                d = {
                    'id': row.id, 'aid_type': 'scholarship', 'aid_type_label': '奖学金',
                    'detail': row.scholarship_type or '',
                    'amount': float(row.amount or 0), 'academic_year': row.academic_year or '',
                }
                _add_student_info(d, row.student_id)
                items.append(d)

        elif t == 'loan':
            q = db.query(StudentLoan).join(Student, StudentLoan.student_id == Student.id)
            q = _base_student_filter(q)
            for row in q.order_by(StudentLoan.created_at.desc()).all():
                d = {
                    'id': row.id, 'aid_type': 'loan', 'aid_type_label': '助学贷款',
                    'detail': row.loan_type or '',
                    'amount': float(row.amount or 0), 'academic_year': '',
                    'extra': f"期限:{row.duration or '-'} 状态:{row.status or '-'}",
                }
                _add_student_info(d, row.student_id)
                items.append(d)

        elif t == 'work_study':
            q = db.query(StudentWorkStudy).join(Student, StudentWorkStudy.student_id == Student.id)
            q = _base_student_filter(q)
            if academic_year:
                q = q.filter(StudentWorkStudy.academic_year == academic_year)
            for row in q.order_by(StudentWorkStudy.created_at.desc()).all():
                d = {
                    'id': row.id, 'aid_type': 'work_study', 'aid_type_label': '勤工助学',
                    'detail': row.position or '',
                    'amount': float(row.compensation or 0), 'academic_year': row.academic_year or '',
                    'extra': f"工时:{row.hours or 0}h",
                }
                _add_student_info(d, row.student_id)
                items.append(d)

        elif t == 'honor':
            q = db.query(StudentHonor).join(Student, StudentHonor.student_id == Student.id)
            q = _base_student_filter(q)
            if academic_year:
                q = q.filter(StudentHonor.academic_year == academic_year)
            for row in q.order_by(StudentHonor.created_at.desc()).all():
                d = {
                    'id': row.id, 'aid_type': 'honor', 'aid_type_label': '评优评先',
                    'detail': row.honor_name or '',
                    'amount': 0, 'academic_year': row.academic_year or '',
                    'extra': row.level or '',
                }
                _add_student_info(d, row.student_id)
                items.append(d)

    total = len(items)
    start = (page - 1) * size
    end = start + size
    return {
        'items': items[start:end],
        'total': total,
        'page': page,
        'size': size,
    }


# ===== 4. 学年列表 =====
@router.get('/semesters')
def financial_aid_semesters(db: Session = Depends(get_db)):
    """获取所有可用学年列表"""
    years = set()
    for model in [StudentHardship, StudentGrant, StudentScholarship, StudentWorkStudy, StudentHonor]:
        rows = db.query(model.academic_year).filter(model.academic_year != '').distinct().all()
        years.update(r[0] for r in rows if r[0])
    return sorted(years, reverse=True)
