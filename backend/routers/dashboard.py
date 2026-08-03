"""驾驶舱数据路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
from models import Student, Tag, GradeRecord, WarningRecord, student_tags, ClassModel, Major, Activity, PartyProgress
from datetime import datetime, timedelta

router = APIRouter(prefix='/api/dashboard', tags=['驾驶舱'])


@router.get('')
def get_dashboard(
    class_name: Optional[str] = Query(None),
    major: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取驾驶舱数据"""
    # 基础查询 - 使用 join
    base_query = db.query(Student).outerjoin(ClassModel, Student.class_id == ClassModel.id).outerjoin(Major, ClassModel.major_id == Major.id)
    if class_name:
        base_query = base_query.filter(ClassModel.class_name == class_name)
    if major:
        base_query = base_query.filter(Major.major_name == major)

    total_students = base_query.count()

    # 班级数
    if class_name:
        total_classes = 1
    else:
        total_classes = db.query(func.count(func.distinct(ClassModel.id))).join(
            Student, Student.class_id == ClassModel.id
        ).filter(ClassModel.class_name != '').scalar() or 0

    # 专业数
    if major:
        total_majors = 1
    else:
        total_majors = db.query(func.count(func.distinct(Major.id))).join(
            ClassModel, ClassModel.major_id == Major.id
        ).join(Student, Student.class_id == ClassModel.id).filter(Major.major_name != '').scalar() or 0

    # 预警统计
    student_ids = [s.id for s in base_query.all()]
    warning_query = db.query(WarningRecord)
    if student_ids:
        warning_query = warning_query.filter(WarningRecord.student_id.in_(student_ids))

    red_count = warning_query.filter(WarningRecord.warning_type == 'red').count()
    yellow_count = warning_query.filter(WarningRecord.warning_type == 'yellow').count()

    # 班级分布
    class_dist_query = db.query(
        ClassModel.class_name, func.count(Student.id)
    ).outerjoin(Student, Student.class_id == ClassModel.id).filter(
        ClassModel.class_name != ''
    )
    if major:
        class_dist_query = class_dist_query.filter(Major.major_name == major)
    class_distribution = [
        {'name': name, 'value': count}
        for name, count in class_dist_query.group_by(ClassModel.id).all()
    ]

    # 专业分布
    major_dist_query = db.query(
        Major.major_name, func.count(Student.id)
    ).outerjoin(ClassModel, ClassModel.major_id == Major.id).outerjoin(
        Student, Student.class_id == ClassModel.id
    ).filter(Major.major_name != '')
    if class_name:
        major_dist_query = major_dist_query.filter(ClassModel.class_name == class_name)
    major_distribution = [
        {'name': name, 'value': count}
        for name, count in major_dist_query.group_by(Major.id).all()
        if count > 0
    ]

    # 标签分布 TOP 10
    tag_dist = db.query(
        Tag.name, Tag.color, func.count(student_tags.c.student_id)
    ).join(student_tags, Tag.id == student_tags.c.tag_id)
    if student_ids:
        tag_dist = tag_dist.filter(student_tags.c.student_id.in_(student_ids))
    tag_distribution = [
        {'name': name, 'color': color, 'value': count}
        for name, color, count in tag_dist.group_by(Tag.id).order_by(
            func.count(student_tags.c.student_id).desc()
        ).limit(10).all()
    ]

    # 近期新增/更新学生
    recent_query = base_query.order_by(Student.updated_at.desc()).limit(5)
    recent_students = [
        {
            'id': s.id, 'name': s.name, 'student_no': s.student_no,
            'class_name': s.class_obj.class_name if s.class_obj else '',
            'updated_at': s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in recent_query.all()
    ]

    # 党员/发展对象数（去重学生 id，取过党团发展阶段的学生）
    party_query = db.query(func.count(func.distinct(PartyProgress.student_id)))
    if student_ids:
        party_query = party_query.filter(PartyProgress.student_id.in_(student_ids))
    party_count = party_query.scalar() or 0

    # 本月活动数（按 activity_date 字符串 YYYY-MM 前缀匹配当月）
    now = datetime.now()
    month_prefix = now.strftime('%Y-%m')
    month_activities = db.query(Activity).filter(Activity.activity_date.like(f'{month_prefix}%')).count()

    # 预警清单 TOP 20（含学生姓名/班级）
    warn_q = db.query(WarningRecord).join(Student, WarningRecord.student_id == Student.id).order_by(WarningRecord.created_at.desc())
    if student_ids:
        warn_q = warn_q.filter(WarningRecord.student_id.in_(student_ids))
    warnings_list = []
    for w in warn_q.limit(20).all():
        s = w.student
        warnings_list.append({
            'id': w.id,
            'student_id': s.id if s else None,
            'name': s.name if s else '',
            'student_no': s.student_no if s else '',
            'class_name': s.class_obj.class_name if s and s.class_obj else '',
            'warning_type': w.warning_type,
            'description': w.description or '',
            'semester': w.semester or '',
        })

    # 近期活动 TOP 5（按 activity_date 倒序）
    recent_act_list = [
        {
            'id': a.id, 'title': a.title, 'activity_date': a.activity_date,
            'location': a.location, 'activity_type': a.activity_type, 'status': a.status,
        }
        for a in db.query(Activity).order_by(Activity.activity_date.desc()).limit(5).all()
    ]

    return {
        'total_students': total_students,
        'total_classes': total_classes,
        'total_majors': total_majors,
        'party_count': party_count,
        'month_activities': month_activities,
        'red_count': red_count,
        'yellow_count': yellow_count,
        'normal_count': total_students - red_count - yellow_count,
        'class_distribution': class_distribution,
        'major_distribution': major_distribution,
        'tag_distribution': tag_distribution,
        'recent_students': recent_students,
        'warnings': warnings_list,
        'recent_activities': recent_act_list,
    }


# ===== V6.10: AI 智能预警 =====

import json as _json
import logging
from models import StudentInterview, PsychologyRecord, StudentAttendanceException, StudentDiscipline

_logger = logging.getLogger(__name__)

# 简单的内存缓存（进程内，5分钟过期 — V6.11hotfix: 缩短TTL确保数据及时刷新）
_ai_warnings_cache = {'data': None, 'ts': 0}
_CACHE_TTL = 300  # 5分钟


@router.get('/ai-warnings')
def get_ai_warnings(
    force: Optional[bool] = Query(False, description='强制刷新，跳过缓存'),
    db: Session = Depends(get_db)
):
    """V6.10: AI 智能预警 - 规则引擎 + LLM 增强分析"""
    import time
    now = time.time()

    # 检查缓存 — V6.11hotfix: 修复缓存返回结构（展开 result_data，与非缓存一致）
    if not force and _ai_warnings_cache['data'] and (now - _ai_warnings_cache['ts']) < _CACHE_TTL:
        return {'cached': True, **_ai_warnings_cache['data']}

    warnings = []

    # ===== 规则引擎：快速筛选 =====

    # 1. 成绩预警 - 有 red 类型预警记录的学生（V6.14: 附带详细信息）
    red_warnings = db.query(WarningRecord).filter(WarningRecord.warning_type == 'red').all()
    red_student_ids = set(w.student_id for w in red_warnings)
    for sid in red_student_ids:
        student = db.query(Student).filter(Student.id == sid).first()
        if student:
            # V6.14: 收集该学生所有red预警的详细信息
            student_red = [w for w in red_warnings if w.student_id == sid]
            details = []
            for rw in student_red:
                details.append({
                    'date': rw.created_at.strftime('%Y-%m-%d') if rw.created_at else '',
                    'info': rw.description or '红色预警',
                    'type': 'red'
                })
            warnings.append({
                'student_id': student.id,
                'name': student.name,
                'student_no': student.student_no,
                'class_name': student.class_name,
                'warning_type': '成绩预警',
                'reason': f'存在 {len(student_red)} 条红色学业预警',
                'severity': 'high',
                'source': 'rule',
                'details': details[:5]  # V6.14: 最多5条
            })

    # 2. 缺勤过多 - 考勤异常>=1次（V6.14: 附带具体日期和课程名）
    from sqlalchemy import func as sa_func
    absence_rows = db.query(
        StudentAttendanceException.student_id,
        sa_func.count(StudentAttendanceException.id).label('cnt')
    ).group_by(StudentAttendanceException.student_id).having(sa_func.count(StudentAttendanceException.id) >= 1).all()

    # V6.14: 预加载所有考勤异常记录用于生成详细信息
    all_absence_records = db.query(StudentAttendanceException).filter(
        StudentAttendanceException.student_id.in_([r[0] for r in absence_rows])
    ).order_by(StudentAttendanceException.exception_date.desc()).all()
    absence_by_student = {}
    for rec in all_absence_records:
        absence_by_student.setdefault(rec.student_id, []).append(rec)

    for sid, cnt in absence_rows:
        if any(w['student_id'] == sid for w in warnings):
            continue
        student = db.query(Student).filter(Student.id == sid).first()
        if student:
            # V6.14: 构建详细信息
            student_absences = absence_by_student.get(sid, [])
            details = []
            for a in student_absences[:5]:
                details.append({
                    'date': a.exception_date or '',
                    'course': a.course_name or '',
                    'type': a.exception_type or ''
                })
            # 构建更具体的原因描述
            types_set = set(a.exception_type for a in student_absences if a.exception_type)
            type_str = '/'.join(types_set) if types_set else '异常'
            recent_dates = [a.exception_date for a in student_absences[:3] if a.exception_date]
            date_str = f"（最近：{', '.join(recent_dates)}）" if recent_dates else ""
            warnings.append({
                'student_id': student.id,
                'name': student.name,
                'student_no': student.student_no,
                'class_name': student.class_name,
                'warning_type': '缺勤过多',
                'reason': f'考勤异常 {cnt} 次（{type_str}）{date_str}',
                'severity': 'medium' if cnt < 5 else 'high',
                'source': 'rule',
                'details': details
            })

    # 3. 心理关注 - 有一级/二级关注等级的学生（V6.14: 附带详细信息）
    psych_high = db.query(PsychologyRecord).filter(
        PsychologyRecord.attention_level.in_(['一级关注', '二级关注'])
    ).all()
    psych_student_ids = set()
    for rec in psych_high:
        if rec.student_id in psych_student_ids:
            continue
        psych_student_ids.add(rec.student_id)
        if any(w['student_id'] == rec.student_id for w in warnings):
            continue
        student = db.query(Student).filter(Student.id == rec.student_id).first()
        if student:
            # V6.14: 收集该学生所有心理记录
            student_psych = [p for p in psych_high if p.student_id == rec.student_id]
            details = []
            for p in student_psych[:5]:
                details.append({
                    'date': p.record_date or '',
                    'info': f"{p.attention_level} - {p.topic or '心理记录'}",
                    'type': p.attention_level
                })
            warnings.append({
                'student_id': student.id,
                'name': student.name,
                'student_no': student.student_no,
                'class_name': student.class_name,
                'warning_type': '心理关注',
                'reason': f'心理关注等级：{rec.attention_level}（{len(student_psych)}条记录）',
                'severity': 'high' if rec.attention_level == '一级关注' else 'medium',
                'source': 'rule',
                'details': details
            })

    # 4. 纪律处分（V6.14: 附带详细信息）
    discipline_records = db.query(StudentDiscipline).all()
    disc_student_ids = set()
    for rec in discipline_records:
        if rec.student_id in disc_student_ids:
            continue
        disc_student_ids.add(rec.student_id)
        if any(w['student_id'] == rec.student_id for w in warnings):
            continue
        student = db.query(Student).filter(Student.id == rec.student_id).first()
        if student:
            # V6.14: 收集该学生所有处分记录
            student_disc = [d for d in discipline_records if d.student_id == rec.student_id]
            details = []
            for d in student_disc[:5]:
                details.append({
                    'date': d.discipline_date or '',
                    'info': f"{d.discipline_type} - {d.reason or '违纪'}",
                    'type': d.discipline_type or ''
                })
            warnings.append({
                'student_id': student.id,
                'name': student.name,
                'student_no': student.student_no,
                'class_name': student.class_name,
                'warning_type': '纪律处分',
                'reason': f'处分类型：{getattr(rec, "discipline_type", "未知")}（{len(student_disc)}条）',
                'severity': 'medium',
                'source': 'rule',
                'details': details
            })

    # 5. 访谈标记"需跟进"的学生（V6.14: 附带详细信息）
    follow_up_interviews = db.query(StudentInterview).filter(StudentInterview.status == '需跟进').all()
    for item in follow_up_interviews:
        if any(w['student_id'] == item.student_id for w in warnings):
            continue
        student = db.query(Student).filter(Student.id == item.student_id).first()
        if student:
            warnings.append({
                'student_id': student.id,
                'name': student.name,
                'student_no': student.student_no,
                'class_name': student.class_name,
                'warning_type': '访谈待跟进',
                'reason': f'访谈"{item.topic or "未命名"}"标记为需跟进（{item.interview_date}）',
                'severity': 'medium',
                'source': 'rule',
                'details': [{
                    'date': item.interview_date or '',
                    'info': f"访谈主题：{item.topic or '未命名'}",
                    'type': '跟进'
                }]
            })

    # ===== LLM 增强分析（可选）=====
    llm_enhanced = False
    ai_advice = ''
    top_priority = []
    if warnings:
        try:
            from services.llm_adapter import LLMAdapter
            llm = LLMAdapter()
            if llm.is_configured:
                # 取前20条给 LLM 分析
                sample = warnings[:20]
                summary_lines = []
                for i, w in enumerate(sample, 1):
                    summary_lines.append(f"{i}. {w['name']}({w['student_no']}) - {w['warning_type']}: {w['reason']}")

                prompt = f"""你是高校辅导员AI助手。以下学生存在需要关注的情况，请分析并给出：
1. 按紧急程度排序建议（前3名最需要关注的学生）
2. 给出一句整体工作建议

学生列表：
{chr(10).join(summary_lines)}

请返回JSON格式：
{{
  "top_priority": [前3名学生姓名],
  "advice": "整体工作建议（50字以内）"
}}"""

                messages = [
                    {"role": "system", "content": "你是高校辅导员AI助手，擅长学生风险研判。请始终返回有效JSON。"},
                    {"role": "user", "content": prompt}
                ]
                result_text = llm.chat(messages)

                # 清理 markdown
                cleaned = result_text.strip()
                if cleaned.startswith('```'):
                    lines = cleaned.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]
                    cleaned = '\n'.join(lines)

                llm_result = _json.loads(cleaned)
                llm_enhanced = True

                # 将 LLM 的建议附加到返回结果
                ai_advice = llm_result.get('advice', '')
                top_priority = llm_result.get('top_priority', [])

                # 调整排序：top_priority 中的学生排前面
                priority_set = set(top_priority)
                if priority_set:
                    warnings.sort(key=lambda w: (0 if w['name'] in priority_set else 1, {'high': 0, 'medium': 1, 'low': 2}.get(w['severity'], 3)))

        except Exception as e:
            _logger.warning(f"LLM 增强分析失败，降级为纯规则引擎: {e}")
            ai_advice = ''
            top_priority = []

    # V6.11: 按严重程度排序（high > medium > low），返回完整列表
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    warnings.sort(key=lambda w: (severity_order.get(w['severity'], 3), w.get('name', '')))

    high_count = sum(1 for w in warnings if w['severity'] == 'high')
    medium_count = sum(1 for w in warnings if w['severity'] == 'medium')
    low_count = sum(1 for w in warnings if w['severity'] == 'low')

    # 构造返回结果 — V6.11: 返回完整预警列表，不再截断
    result_data = {
        'warnings': warnings,
        'total': len(warnings),
        'high_count': high_count,
        'medium_count': medium_count,
        'low_count': low_count,
        'llm_enhanced': llm_enhanced,
        'ai_advice': ai_advice if llm_enhanced else '',
        'top_priority': top_priority if llm_enhanced else [],
    }

    # 缓存
    _ai_warnings_cache['data'] = result_data
    _ai_warnings_cache['ts'] = now

    return {'cached': False, **result_data}
