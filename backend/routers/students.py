"""学生管理路由"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
import pandas as pd
import io
from database import get_db
from models import Student, Tag, GradeRecord, student_tags, ClassModel, Major
from schemas import (
    StudentCreate, StudentUpdate, StudentOut, StudentDetail, TagOut
)

router = APIRouter(prefix='/api/students', tags=['学生管理'])



@router.get('/simple')
def list_students_simple(db: Session = Depends(get_db)):
    """返回所有学生（仅 id, name, student_no），用于下拉选择，无分页限制"""
    students = db.query(Student).order_by(Student.student_no).all()
    return [
        {"id": s.id, "name": s.name, "student_no": s.student_no}
        for s in students
    ]

@router.get('/search')
def search_students(
    q: str = Query('', description='搜索关键词'),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """学生远程搜索 (用于关联选择器) - 支持姓名/学号/拼音首字母/班级名"""
    query = db.query(
        Student.id,
        Student.student_no,
        Student.name,
        ClassModel.class_name,
        Major.major_name
    ).outerjoin(
        ClassModel, Student.class_id == ClassModel.id
    ).outerjoin(
        Major, ClassModel.major_id == Major.id
    )

    if q and q.strip():
        keyword = q.strip()
        search_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Student.student_no.ilike(search_pattern),
                Student.name.ilike(search_pattern),
                Student.pinyin_initial.ilike(search_pattern),
                ClassModel.class_name.ilike(search_pattern),
            )
        )

    # 空关键词也返回前 N 个（按学号排序），供下拉初始展示
    results = query.order_by(Student.student_no).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "student_no": r.student_no,
            "name": r.name,
            "class_name": r.class_name or '',
            "major": r.major_name or '',
            "label": f"{r.name} ({r.student_no} · {r.class_name or ''})",
        }
        for r in results
    ]


@router.get('', response_model=dict)
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    size: int = Query(None, ge=1, le=100, description='每页大小 (别名)'),
    keyword: str = Query('', description='搜索学号/姓名'),
    search: str = Query('', description='全局搜索 (学号/姓名/班级/专业/手机号)'),
    class_name: str = Query('', description='班级筛选'),
    filter_class: str = Query('', description='班级筛选 (别名)'),
    major: str = Query('', description='专业筛选'),
    filter_major: str = Query('', description='专业筛选 (别名)'),
    gender: str = Query('', description='性别筛选'),
    filter_gender: str = Query('', description='性别筛选 (别名)'),
    political_status: str = Query('', description='政治面貌筛选'),
    filter_political: str = Query('', description='政治面貌筛选 (别名)'),
    birth_source: str = Query('', description='生源地筛选'),
    filter_source: str = Query('', description='生源地筛选 (别名)'),
    tag_id: Optional[int] = Query(None, description='标签筛选'),
    sort_by: str = Query('updated_at', description='排序字段'),
    order: str = Query('desc', description='排序方向 (asc/desc)'),
    db: Session = Depends(get_db)
):
    """获取学生列表（分页+搜索+筛选+排序）"""
    # 统一参数名
    actual_size = size or page_size
    actual_search = search or keyword
    actual_class = filter_class or class_name
    actual_major = filter_major or major
    actual_gender = filter_gender or gender
    actual_political = filter_political or political_status
    actual_source = filter_source or birth_source
    
    query = db.query(Student).outerjoin(ClassModel, Student.class_id == ClassModel.id).outerjoin(Major, ClassModel.major_id == Major.id)

    # 全局搜索 (LIKE '%keyword%')
    if actual_search:
        search_pattern = f"%{actual_search}%"
        query = query.filter(
            or_(
                Student.student_no.ilike(search_pattern),
                Student.name.ilike(search_pattern),
                ClassModel.class_name.ilike(search_pattern),
                Student.phone.ilike(search_pattern),
                Student.birth_source.ilike(search_pattern),
            )
        )
    
    # 精确筛选
    if actual_class:
        query = query.filter(ClassModel.class_name == actual_class)
    if actual_major:
        query = query.filter(Major.major_name == actual_major)
    if actual_gender:
        query = query.filter(Student.gender == actual_gender)
    if actual_political:
        query = query.filter(Student.political_status == actual_political)
    if actual_source:
        query = query.filter(Student.birth_source == actual_source)
    if tag_id:
        query = query.filter(Student.tags.any(Tag.id == tag_id))

    # 排序（白名单）
    SORT_WHITELIST = {
        'student_no': Student.student_no,
        'name': Student.name,
        'gender': Student.gender,
        'political_status': Student.political_status,
        'birth_source': Student.birth_source,
        'phone': Student.phone,
        'email': Student.email,
        'id_card': Student.id_card,
        'campus': Student.campus,
        'dorm_building': Student.dorm_building,
        'dorm_room': Student.dorm_room,
        'class_name': ClassModel.class_name,
        'major': Major.major_name,
        'created_at': Student.created_at,
        'updated_at': Student.updated_at,
    }
    sort_column = SORT_WHITELIST.get(sort_by, Student.updated_at)
    if order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    total = query.count()
    rows = query.offset((page - 1) * actual_size).limit(actual_size).all()

    items = []
    for r in rows:
        tags_list = [{'id': t.id, 'name': t.name, 'group_name': t.group_name, 'color': t.color} for t in r.tags]
        # Get major name through class relationship
        major_name = ''
        if r.class_obj and r.class_obj.major:
            major_name = r.class_obj.major.major_name
        items.append({
            'id': r.id,
            'student_no': r.student_no,
            'name': r.name,
            'class_name': r.class_obj.class_name if r.class_obj else '',
            'class_id': r.class_id,
            'major': major_name,
            'gender': r.gender,
            'political_status': r.political_status,
            'phone': r.phone,
            'email': r.email,
            'parent_phone': getattr(r, 'parent_phone', None),
            'birth_date': getattr(r, 'birth_date', '') or '',
            'birth_source': r.birth_source,
            'id_card': getattr(r, 'id_card', None),
            'campus': getattr(r, 'campus', None),
            'dorm_building': getattr(r, 'dorm_building', None),
            'dorm_room': getattr(r, 'dorm_room', None),
            'is_off_campus': getattr(r, 'is_off_campus', False),
            'off_campus_address': getattr(r, 'off_campus_address', None),
            'notes': getattr(r, 'notes', None),
            'tags': tags_list,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'updated_at': r.updated_at.isoformat() if r.updated_at else None,
        })

    return {
        'items': items,
        'total': total,
        'page': page,
        'page_size': actual_size,
    }


@router.get('/classes')
def list_classes(db: Session = Depends(get_db)):
    """获取班级列表 (用于筛选下拉)"""
    classes = db.query(ClassModel.class_name).distinct().filter(ClassModel.class_name != '').all()
    return [c[0] for c in classes]


@router.get('/export')
def export_students(
    keyword: str = Query(''),
    class_name: str = Query(''),
    major: str = Query(''),
    gender: str = Query(''),
    political_status: str = Query(''),
    birth_source: str = Query(''),
    db: Session = Depends(get_db)
):
    """导出学生 Excel"""
    query = db.query(Student).outerjoin(ClassModel, Student.class_id == ClassModel.id).outerjoin(Major, ClassModel.major_id == Major.id)
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Student.student_no.ilike(search_pattern),
                Student.name.ilike(search_pattern),
            )
        )
    if class_name:
        query = query.filter(ClassModel.class_name == class_name)
    if major:
        query = query.filter(Major.major_name == major)
    if gender:
        query = query.filter(Student.gender == gender)
    if political_status:
        query = query.filter(Student.political_status == political_status)
    if birth_source:
        query = query.filter(Student.birth_source.ilike(f'%{birth_source}%'))
    
    rows = query.all()
    
    data = []
    for r in rows:
        major_name = ''
        if r.class_obj and r.class_obj.major:
            major_name = r.class_obj.major.major_name
        data.append({
            '学号': r.student_no,
            '姓名': r.name,
            '班级': r.class_obj.class_name if r.class_obj else '',
            '专业': major_name,
            '性别': r.gender,
            '政治面貌': r.political_status,
            '手机号': r.phone,
            '邮箱': r.email,
            '生源地': r.birth_source,
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=students_export.xlsx'}
    )



@router.post('/export')
def export_students_by_ids(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """按 ID 列表批量导出学生 Excel (v3j-B-b02 · 批量选择导出)"""
    ids = payload.get('ids') or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(400, '请传入非空的 ids 列表')

    query = db.query(Student).outerjoin(ClassModel, Student.class_id == ClassModel.id).outerjoin(Major, ClassModel.major_id == Major.id)
    query = query.filter(Student.id.in_(ids))
    rows = query.all()

    data = []
    for r in rows:
        major_name = ''
        if r.class_obj and r.class_obj.major:
            major_name = r.class_obj.major.major_name
        data.append({
            '学号': r.student_no,
            '姓名': r.name,
            '班级': r.class_obj.class_name if r.class_obj else '',
            '专业': major_name,
            '性别': r.gender,
            '政治面貌': r.political_status,
            '手机号': r.phone,
            '邮箱': r.email,
            '生源地': r.birth_source,
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=students_selected.xlsx'}
    )


@router.post('/export/full')
def export_students_full(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """学生 360 完整档案批量导出 (v3j-B-b03)。
    宽表：一行一个学生，列涵盖基础信息 + 成绩汇总 + 活动 + 心理 + 预警 + 教师 + 干部 + 党团 等所有维度。
    """
    from openpyxl import Workbook
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    from datetime import datetime as _dt
    from models import (
        WarningRecord, PartyProgress, PsychologyRecord, FamilyContact,
        StudentCadreRecord, ActivitySignup, EmploymentRecord,
        StudentHardship, StudentHonor, ClassTeacher,
        StudentLeave, StudentDiscipline, StudentStatusChange
    )

    ids = payload.get('ids') or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(400, '请传入非空的 ids 列表')

    rows = db.query(Student).outerjoin(
        ClassModel, Student.class_id == ClassModel.id
    ).outerjoin(
        Major, ClassModel.major_id == Major.id
    ).filter(Student.id.in_(ids)).all()

    wb = Workbook()
    ws = wb.active
    ws.title = '学生360完整档案'

    headers = [
        # 基础信息
        '学号', '姓名', '性别', '出生日期', '政治面貌', '手机号', '邮箱',
        '家长电话', '生源地', '身份证号', '校区', '宿舍楼', '寝室号', '班级', '专业',
        # 成绩汇总
        '总课程数', '及格数', '不及格数', '平均分', '平均GPA',
        # 活动
        '活动参与数',
        # 心理
        '心理关注等级', '心理最新测评日期', '累计咨询次数', '下次跟进',
        # 预警
        '预警等级', '预警学期', '预警原因',
        # 教师评价 (班主任)
        '班主任姓名', '班主任电话', '班主任邮箱',
        # 干部履历（拼接多条）
        '干部履历',
        # 党团
        '党团进程当前阶段', '阶段日期',
        # 就业
        '就业状态', '就业单位', '就业岗位',
        # 荣誉/资助
        '荣誉数', '资助等级',
        # 违纪/请假/异动
        '违纪次数', '请假次数', '学籍异动次数',
        # 家校
        '家校沟通次数',
        # 备注
        '备注',
    ]
    ws.append(headers)

    for stu in rows:
        cls_name = stu.class_obj.class_name if stu.class_obj else ''
        major_name = stu.class_obj.major.major_name if (stu.class_obj and stu.class_obj.major) else ''

        # 成绩
        grades = db.query(GradeRecord).filter(GradeRecord.student_id == stu.id).all()
        scores = [float(g.score) for g in grades if g.score is not None]
        gpas = [float(g.gpa) for g in grades if g.gpa is not None]
        total_courses = len(grades)
        fail_cnt = sum(1 for s in scores if s < 60)
        pass_cnt = total_courses - fail_cnt
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0
        avg_gpa = round(sum(gpas) / len(gpas), 2) if gpas else 0

        # 活动
        act_cnt = db.query(ActivitySignup).filter(ActivitySignup.student_id == stu.id).count()

        # 心理
        psy = db.query(PsychologyRecord).filter(
            PsychologyRecord.student_id == stu.id
        ).order_by(PsychologyRecord.record_date.desc()).first()
        psy_level = psy.attention_level if psy else ''
        psy_date = psy.record_date if psy else ''
        psy_counsel = psy.counseling_count if psy else 0
        psy_next = psy.next_follow_date if psy else ''

        # 预警
        warn = db.query(WarningRecord).filter(
            WarningRecord.student_id == stu.id
        ).order_by(WarningRecord.created_at.desc()).first()
        warn_level = ''
        warn_sem = ''
        warn_desc = ''
        if warn:
            wt = (warn.warning_type or '').lower()
            if 'red' in wt or '红' in warn.warning_type:
                warn_level = '红色'
            elif 'yellow' in wt or '黄' in warn.warning_type:
                warn_level = '黄色'
            elif 'blue' in wt or '蓝' in warn.warning_type:
                warn_level = '蓝色'
            else:
                warn_level = warn.warning_type or ''
            warn_sem = warn.semester or ''
            warn_desc = warn.description or ''

        # 班主任 (教师评价)
        teacher = db.query(ClassTeacher).filter(ClassTeacher.class_id == stu.class_id).first() if stu.class_id else None
        t_name = teacher.name if teacher else ''
        t_phone = teacher.phone if teacher else ''
        t_email = getattr(teacher, 'email', '') if teacher else ''

        # 干部履历
        cadres = db.query(StudentCadreRecord).filter(StudentCadreRecord.student_id == stu.id).all()
        cadre_str = '; '.join([
            f"{c.position}({c.level or '-'}/{c.start_date or '-'}~{c.end_date or '-'})"
            for c in cadres
        ])

        # 党团
        party = db.query(PartyProgress).filter(
            PartyProgress.student_id == stu.id
        ).order_by(PartyProgress.stage_date.desc()).first()
        party_stage = party.stage if party else '群众'
        party_date = party.stage_date if party else ''

        # 就业
        emp = db.query(EmploymentRecord).filter(
            EmploymentRecord.student_id == stu.id
        ).order_by(EmploymentRecord.id.desc()).first()
        emp_status = emp.status if emp else '未登记'
        emp_company = (emp.internship_company or emp.target_industry) if emp else ''
        emp_position = emp.target_position if emp else ''

        # 荣誉/资助
        honor_cnt = db.query(StudentHonor).filter(StudentHonor.student_id == stu.id).count()
        hardship = db.query(StudentHardship).filter(StudentHardship.student_id == stu.id).first()
        hardship_level = hardship.hardship_level if hardship else '无'

        # 违纪/请假/异动
        disc_cnt = db.query(StudentDiscipline).filter(StudentDiscipline.student_id == stu.id).count()
        leave_cnt = db.query(StudentLeave).filter(StudentLeave.student_id == stu.id).count()
        status_cnt = db.query(StudentStatusChange).filter(StudentStatusChange.student_id == stu.id).count()

        # 家校
        family_cnt = db.query(FamilyContact).filter(FamilyContact.student_id == stu.id).count()

        ws.append([
            stu.student_no, stu.name, stu.gender or '', stu.birth_date or '',
            stu.political_status or '', stu.phone or '', stu.email or '',
            stu.parent_phone or '', stu.birth_source or '', stu.id_card or '',
            stu.campus or '', stu.dorm_building or '', stu.dorm_room or '',
            cls_name, major_name,
            total_courses, pass_cnt, fail_cnt, avg_score, avg_gpa,
            act_cnt,
            psy_level, psy_date, psy_counsel, psy_next,
            warn_level, warn_sem, warn_desc,
            t_name, t_phone, t_email,
            cadre_str,
            party_stage, party_date,
            emp_status, emp_company, emp_position,
            honor_cnt, hardship_level,
            disc_cnt, leave_cnt, status_cnt,
            family_cnt,
            stu.notes or '',
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f'students_full_{_dt.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@router.get('/filters')
def get_filters(db: Session = Depends(get_db)):
    """获取筛选选项"""
    classes = db.query(ClassModel.class_name).distinct().filter(ClassModel.class_name != '').all()
    majors = db.query(Major.major_name).distinct().filter(Major.major_name != '').all()
    
    return {
        'classes': [c[0] for c in classes],
        'majors': [m[0] for m in majors],
        'genders': ['男', '女'],
        'political_statuses': ['群众', '共青团员', '入党积极分子', '发展对象', '中共预备党员', '中共党员'],
        'sources': [],
    }


@router.post('')
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    """新增学生"""
    # 检查学号唯一性
    existing = db.query(Student).filter(Student.student_no == data.student_no).first()
    if existing:
        raise HTTPException(400, f'学号 {data.student_no} 已存在')
    
    # 只取 Student model 存在的字段
    model_cols = {c.name for c in Student.__table__.columns}
    payload = {k: v for k, v in data.dict().items() if k in model_cols}
    student = Student(**payload)
    db.add(student)
    db.commit()
    db.refresh(student)
    return {'id': student.id}


@router.get('/{student_id}/completeness')
def get_student_completeness(student_id: int, db: Session = Depends(get_db)):
    """学生信息完整度检查 - 返回百分比 + 缺失字段清单"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404, '学生不存在')
    # 定义必检查字段（含中文名 + 权重）
    checks = [
        ('student_no', '学号', 10),
        ('name', '姓名', 10),
        ('gender', '性别', 5),
        ('class_id', '所在班级', 10),
        ('birth_date', '出生日期', 5),
        ('political_status', '政治面貌', 5),
        ('phone', '本人电话', 10),
        ('email', '邮箱', 5),
        ('parent_phone', '家长电话', 10),
        ('birth_source', '生源地', 5),
    ]
    total_weight = sum(w for _, _, w in checks)
    got_weight = 0
    missing = []
    filled = []
    for field, label, weight in checks:
        val = getattr(student, field, None)
        if val is None or str(val).strip() == '':
            missing.append({'field': field, 'label': label, 'weight': weight})
        else:
            got_weight += weight
            filled.append({'field': field, 'label': label})
    # 家庭联系 / 心理关怀 / 成绩三类关系数据也纳入检查（存在即计分）
    rel_checks = [
        ('family_contacts', '家庭联系人', 5),
        ('grade_records', '成绩记录', 5),
        ('psychology_records', '心理关怀记录', 5),
    ]
    for rel_name, label, weight in rel_checks:
        total_weight += weight
        rel = getattr(student, rel_name, None)
        has = False
        try:
            if rel is not None:
                # relationship 可能是 list 或 query
                has = bool(list(rel)) if hasattr(rel, '__iter__') else bool(rel)
        except Exception:
            has = False
        if has:
            got_weight += weight
            filled.append({'field': rel_name, 'label': label})
        else:
            missing.append({'field': rel_name, 'label': label, 'weight': weight})
    percent = int(round(got_weight * 100 / total_weight)) if total_weight else 0
    if percent >= 90:
        level = 'excellent'
    elif percent >= 70:
        level = 'good'
    elif percent >= 40:
        level = 'warning'
    else:
        level = 'poor'
    return {
        'student_id': student_id,
        'percent': percent,
        'level': level,
        'missing': missing,
        'filled': filled,
        'total_items': len(checks) + len(rel_checks),
        'missing_count': len(missing),
    }


@router.get('/{student_id}')
def get_student(student_id: int, db: Session = Depends(get_db)):
    """获取学生详情"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404, '学生不存在')
    
    tags_list = [{'id': t.id, 'name': t.name, 'group_name': t.group_name, 'color': t.color} for t in student.tags]
    major_name = ''
    if student.class_obj and student.class_obj.major:
        major_name = student.class_obj.major.major_name
    
    return {
        'id': student.id,
        'student_no': student.student_no,
        'name': student.name,
        'class_name': student.class_obj.class_name if student.class_obj else '',
        'class_id': student.class_id,
        'major': major_name,
        'gender': student.gender,
        'birth_date': student.birth_date,
        'political_status': student.political_status,
        'phone': student.phone,
        'email': student.email,
        'parent_phone': getattr(student, 'parent_phone', None),
        'birth_source': student.birth_source,
        'id_card': getattr(student, 'id_card', None),
        'campus': getattr(student, 'campus', None),
        'dorm_building': getattr(student, 'dorm_building', None),
        'dorm_room': getattr(student, 'dorm_room', None),
        'is_off_campus': getattr(student, 'is_off_campus', False),
        'off_campus_address': getattr(student, 'off_campus_address', None),
        'notes': getattr(student, 'notes', None),
        'tags': tags_list,
        'created_at': student.created_at.isoformat() if student.created_at else None,
        'updated_at': student.updated_at.isoformat() if student.updated_at else None,
    }


@router.put('/{student_id}')
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    """更新学生信息"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404, '学生不存在')
    
    update_data = data.dict(exclude_unset=True)
    model_cols = {col.name for col in Student.__table__.columns}
    for key, value in update_data.items():
        if key in model_cols:
            setattr(student, key, value)
    
    db.commit()
    return {'ok': True}


@router.delete('/{student_id}')
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """删除学生"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404, '学生不存在')
    
    db.delete(student)
    db.commit()
    return {'ok': True}


@router.post('/import')
async def import_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """批量导入学生"""
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    required_cols = ['学号', '姓名']
    for col in required_cols:
        if col not in df.columns:
            raise HTTPException(400, f'缺少必填列: {col}')
    
    imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            student_no = str(row['学号']).strip()
            name = str(row['姓名']).strip()
            
            if not student_no or not name:
                errors.append(f'第{idx + 2}行: 学号或姓名为空')
                continue
            
            # 检查是否已存在
            existing = db.query(Student).filter(Student.student_no == student_no).first()
            if existing:
                errors.append(f'第{idx + 2}行: 学号 {student_no} 已存在')
                continue
            
            student = Student(
                student_no=student_no,
                name=name,
                gender=str(row.get('性别', '')),
                phone=str(row.get('手机号', '')),
                email=str(row.get('邮箱', '')),
                birth_source=str(row.get('生源地', '')),
                political_status=str(row.get('政治面貌', '共青团员')),
            )
            db.add(student)
            imported += 1
        except Exception as e:
            errors.append(f'第{idx + 2}行: {str(e)}')
    
    db.commit()
    
    return {
        'imported': imported,
        'errors': errors[:10],
        'total_errors': len(errors)
    }
