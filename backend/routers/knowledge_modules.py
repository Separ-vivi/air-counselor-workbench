"""知识库 + FAQ + 文书生成 + 周汇总 路由"""
import json
import re
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import KnowledgeDoc, FAQ, DocumentTemplate, GeneratedDocument, Student, WeeklySummary

router = APIRouter(prefix='/api')


# ===== 知识库 =====
@router.get('/knowledge')
def list_knowledge(db: Session = Depends(get_db)):
    items = db.query(KnowledgeDoc).order_by(KnowledgeDoc.created_at.desc()).all()
    return [{
        'id': d.id, 'title': d.title, 'doc_type': d.doc_type,
        'content': d.content[:200] + '...' if len(d.content) > 200 else d.content,
        'chunk_count': d.chunk_count, 'created_at': str(d.created_at),
    } for d in items]


@router.get('/knowledge/{kid}')
def get_knowledge(kid: int, db: Session = Depends(get_db)):
    d = db.query(KnowledgeDoc).get(kid)
    if not d:
        raise HTTPException(404)
    return {'id': d.id, 'title': d.title, 'content': d.content, 'doc_type': d.doc_type}


@router.post('/knowledge')
def create_knowledge(data: dict, db: Session = Depends(get_db)):
    d = KnowledgeDoc(**data)
    db.add(d)
    db.commit()
    db.refresh(d)
    return {'id': d.id}


@router.delete('/knowledge/{kid}')
def delete_knowledge(kid: int, db: Session = Depends(get_db)):
    d = db.query(KnowledgeDoc).get(kid)
    if d:
        db.delete(d)
        db.commit()
    return {'ok': True}


# ===== FAQ =====
@router.get('/faqs')
def list_faqs(published_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(FAQ)
    if published_only:
        q = q.filter(FAQ.is_published == True)
    items = q.order_by(FAQ.created_at.desc()).all()
    return [{
        'id': f.id, 'question': f.question, 'answer': f.answer,
        'category': f.category, 'is_published': f.is_published,
    } for f in items]


@router.get('/faqs/export')
def export_faqs(format: str = 'excel', category: Optional[str] = None, db: Session = Depends(get_db)):
    """FAQ 多格式导出：支持 excel / csv / json"""
    q = db.query(FAQ)
    if category:
        q = q.filter(FAQ.category == category)
    items = q.order_by(FAQ.created_at.desc()).all()

    status_map = {True: '已发布', False: '草稿'}
    rows_data = [{
        'category': f.category or '',
        'question': f.question or '',
        'answer': f.answer or '',
        'status': status_map.get(f.is_published, '草稿'),
    } for f in items]

    fmt = format.lower().strip()

    if fmt == 'json':
        return rows_data

    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['分类', '问题', '答案', '状态'])
        for r in rows_data:
            writer.writerow([r['category'], r['question'], r['answer'], r['status']])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue().encode('utf-8-sig')]),
            media_type='text/csv',
            headers={'Content-Disposition': "attachment; filename*=UTF-8''FAQ_export.csv"},
        )

    # 默认 excel
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'FAQ导出'
    ws.append(['分类', '问题', '答案', '状态'])
    for r in rows_data:
        ws.append([r['category'], r['question'], r['answer'], r['status']])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': "attachment; filename*=UTF-8''FAQ_export.xlsx"},
    )


@router.get('/faqs/{faq_id}')
def get_faq(faq_id: int, db: Session = Depends(get_db)):
    f = db.query(FAQ).get(faq_id)
    if not f:
        raise HTTPException(404, 'FAQ不存在')
    return {
        'id': f.id, 'question': f.question, 'answer': f.answer,
        'category': f.category, 'is_published': f.is_published,
    }


@router.post('/faqs')
def create_faq(data: dict, db: Session = Depends(get_db)):
    f = FAQ(**data)
    db.add(f)
    db.commit()
    db.refresh(f)
    return {'id': f.id}


@router.put('/faqs/{fid}')
def update_faq(fid: int, data: dict, db: Session = Depends(get_db)):
    f = db.query(FAQ).get(fid)
    if not f:
        raise HTTPException(404)
    for k, v in data.items():
        if hasattr(f, k):
            setattr(f, k, v)
    db.commit()
    return {'ok': True}


@router.delete('/faqs/{fid}')
def delete_faq(fid: int, db: Session = Depends(get_db)):
    f = db.query(FAQ).get(fid)
    if f:
        db.delete(f)
        db.commit()
    return {'ok': True}


# ===== 文书模板 =====

# 预置模板数据
_DEFAULT_TEMPLATES = [
    {
        'name': '个人情况说明',
        'template_type': '个人材料',
        'content': (
            '个人情况说明\n\n'
            '姓名：{{姓名}}，学号：{{学号}}，性别：{{性别}}，'
            '就读于{{专业}}专业{{班级}}班，政治面貌：{{政治面貌}}。\n\n'
            '特此说明。\n\n'
            '日期：{{当前日期}}'
        ),
    },
    {
        'name': '家访通知',
        'template_type': '家校沟通',
        'content': (
            '家访通知\n\n'
            '尊敬的 {{家长姓名}} 家长：\n\n'
            '您好！为进一步加强家校联系，拟于近期对您家中 {{学生姓名}}（{{班级}}）同学进行家访，'
            '届时就学习、生活等情况进行沟通。\n\n'
            '日期：{{当前日期}}'
        ),
    },
    {
        'name': '评优推荐信',
        'template_type': '评优推荐',
        'content': (
            '评优推荐信\n\n'
            '兹推荐 {{姓名}}（学号：{{学号}}），{{专业}}专业{{班级}}班学生，'
            '政治面貌：{{政治面貌}}。该生在校期间表现优秀，特此推荐。\n\n'
            '日期：{{当前日期}}'
        ),
    },
    {
        'name': '奖学金申请确认书',
        'template_type': '奖助学金',
        'content': (
            '奖学金申请确认书\n\n'
            '学生 {{姓名}}（学号：{{学号}}），经评审，拟授予 {{奖学金名称}}，'
            '金额：{{金额}}元。请确认以上信息无误后签字。\n\n'
            '日期：{{当前日期}}'
        ),
    },
    {
        'name': '党员发展公示',
        'template_type': '党建材料',
        'content': (
            '党员发展公示\n\n'
            '经支部讨论，拟确定 {{姓名}}（{{班级}}）为 {{发展阶段}} 发展对象，'
            '现予以公示。如有异议，请在公示期内反映。\n\n'
            '日期：{{当前日期}}'
        ),
    },
]


def ensure_default_templates(db: Session):
    """如果数据库模板为空，自动插入预置模板"""
    count = db.query(DocumentTemplate).count()
    if count == 0:
        for tpl_data in _DEFAULT_TEMPLATES:
            tpl = DocumentTemplate(**tpl_data)
            db.add(tpl)
        db.commit()


@router.get('/document-templates')
def list_templates(db: Session = Depends(get_db)):
    ensure_default_templates(db)  # 首次访问自动初始化预置模板
    items = db.query(DocumentTemplate).all()
    return [{
        'id': t.id, 'name': t.name, 'template_type': t.template_type,
        'content': t.content,
    } for t in items]


@router.post('/document-templates')
def create_template(data: dict, db: Session = Depends(get_db)):
    t = DocumentTemplate(**data)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {'id': t.id}


@router.put('/document-templates/{tid}')
def update_template(tid: int, data: dict, db: Session = Depends(get_db)):
    """更新模板：支持 name / template_type / content"""
    t = db.query(DocumentTemplate).get(tid)
    if not t:
        raise HTTPException(404, '模板不存在')
    for key in ('name', 'template_type', 'content'):
        if key in data:
            setattr(t, key, data[key])
    db.commit()
    return {'ok': True}


@router.delete('/document-templates/{tid}')
def delete_template(tid: int, db: Session = Depends(get_db)):
    """删除模板"""
    t = db.query(DocumentTemplate).get(tid)
    if not t:
        raise HTTPException(404, '模板不存在')
    db.delete(t)
    db.commit()
    return {'ok': True}


# ===== 文书生成（变量插值增强） =====

# 当前学年自动计算
def _current_academic_year() -> str:
    """返回当前学年，如 '2025-2026'"""
    now = datetime.now()
    if now.month >= 9:
        return f'{now.year}-{now.year + 1}'
    return f'{now.year - 1}-{now.year}'


# 变量名 → Student 字段的映射表
_VARIABLE_FIELD_MAP = {
    '姓名': 'name',
    '学号': 'student_no',
    '性别': 'gender',
    '政治面貌': 'political_status',
    '电话': 'phone',
    '邮箱': 'email',
    '家长电话': 'parent_phone',
    '生源地': 'birth_source',
    '身份证号': 'id_card',
    '校区': 'campus',
    '宿舍楼': 'dorm_building',
    '房间号': 'dorm_room',
}


def _build_variable_dict(stu: Student) -> dict:
    """根据 Student 对象构建变量字典"""
    from models import ClassModel, Major

    # 基础字段映射
    var_dict = {}
    for var_name, field_name in _VARIABLE_FIELD_MAP.items():
        var_dict[var_name] = getattr(stu, field_name, '') or ''

    # 需要通过关系获取的字段
    cls_name = ''
    major_name = ''
    grade_name = ''
    if stu.class_obj:
        cls_name = stu.class_obj.class_name or ''
        if stu.class_obj.major:
            major_name = stu.class_obj.major.major_name or ''
            if stu.class_obj.major.grade:
                grade_name = stu.class_obj.major.grade.grade_name or ''

    var_dict['班级'] = cls_name
    var_dict['专业'] = major_name
    var_dict['年级'] = grade_name

    # 日期变量
    var_dict['当前日期'] = datetime.now().strftime('%Y-%m-%d')
    var_dict['当前学年'] = _current_academic_year()

    return var_dict


@router.post('/documents/generate')
def generate_document(data: dict, db: Session = Depends(get_db)):
    """基于模板和学生数据生成文书 — 增强版变量插值"""
    student_id = data.get('student_id')
    template_id = data.get('template_id')
    doc_type = data.get('doc_type', '')
    title = data.get('title', '')

    content = ''
    if template_id:
        tpl = db.query(DocumentTemplate).get(template_id)
        if tpl:
            content = tpl.content

    # 增强变量替换
    if student_id:
        stu = db.query(Student).get(student_id)
        if stu:
            var_dict = _build_variable_dict(stu)

            # 同时兼容旧模板中的硬编码变量（如家长姓名、奖学金名称等用户自定义变量）
            # 对 data 中额外传入的自定义变量也做合并
            extra_vars = data.get('variables', {})
            if isinstance(extra_vars, dict):
                var_dict.update(extra_vars)

            # 正则替换：支持 {{变量名}} 和 {{ 变量名 }}（允许空格）
            def _replace_var(match):
                var_name = match.group(1).strip()
                return var_dict.get(var_name, '')

            content = re.sub(r'\{\{\s*(.+?)\s*\}\}', _replace_var, content)

    # 对仍未替换的变量（学生数据中无此字段），替换为空字符串
    content = re.sub(r'\{\{\s*.+?\s*\}\}', '', content)

    doc = GeneratedDocument(
        student_id=student_id, template_id=template_id,
        title=title, content=content, doc_type=doc_type
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {'id': doc.id, 'content': content}


@router.get('/documents')
def list_documents(student_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(GeneratedDocument)
    if student_id:
        q = q.filter(GeneratedDocument.student_id == student_id)
    items = q.order_by(GeneratedDocument.created_at.desc()).all()
    result = []
    for d in items:
        stu = db.query(Student).get(d.student_id) if d.student_id else None
        result.append({
            'id': d.id, 'title': d.title, 'doc_type': d.doc_type,
            'content': d.content, 'student_name': stu.name if stu else '',
            'created_at': str(d.created_at),
        })
    return result


@router.get('/documents/{doc_id}')
def get_document(doc_id: int, db: Session = Depends(get_db)):
    d = db.query(GeneratedDocument).get(doc_id)
    if not d:
        raise HTTPException(404, '文档不存在')
    stu = db.query(Student).get(d.student_id) if d.student_id else None
    return {
        'id': d.id, 'title': d.title, 'doc_type': d.doc_type,
        'content': d.content, 'student_name': stu.name if stu else '',
        'created_at': str(d.created_at),
    }


@router.put('/documents/{did}')
def update_document(did: int, data: dict, db: Session = Depends(get_db)):
    d = db.query(GeneratedDocument).get(did)
    if not d:
        raise HTTPException(404)
    for k, v in data.items():
        if hasattr(d, k):
            setattr(d, k, v)
    db.commit()
    return {'ok': True}


@router.delete('/documents/{did}')
def delete_document(did: int, db: Session = Depends(get_db)):
    d = db.query(GeneratedDocument).get(did)
    if d:
        db.delete(d)
        db.commit()
    return {'ok': True}


# ===== 周汇总 =====
@router.get('/weekly-summaries')
def list_weekly_summaries(db: Session = Depends(get_db)):
    items = db.query(WeeklySummary).order_by(WeeklySummary.created_at.desc()).all()
    from models import WeeklySummary as WS
    return [{
        'id': s.id, 'week_start': s.week_start, 'week_end': s.week_end,
        'content': s.content, 'summary_type': s.summary_type,
        'created_at': str(s.created_at),
    } for s in items]


@router.get('/weekly-summaries/{summary_id}')
def get_weekly_summary(summary_id: int, db: Session = Depends(get_db)):
    s = db.query(WeeklySummary).get(summary_id)
    if not s:
        raise HTTPException(404, '周汇总不存在')
    return {
        'id': s.id, 'week_start': s.week_start, 'week_end': s.week_end,
        'content': s.content, 'summary_type': s.summary_type,
        'created_at': str(s.created_at),
    }


@router.post('/weekly-summaries/generate')
def generate_weekly_summary(payload: dict = None, db: Session = Depends(get_db)):
    """自动生成周汇总（v3h-hotfix1：三 format 真差异化 + 日程本本周回顾/下周计划）
    payload 可选字段：
      dimensions: [academic|party|psychology|aid|employment|daily|activity] 多选
      format: bullet | paragraph | mixed
      week_offset: int，0=本周，-1=上周
    """
    from datetime import datetime, timedelta
    from models import (
        PsychologyRecord, FamilyContact, PartyProgress, WarningRecord,
        ClassMeeting, WeeklySummary as WS,
        Activity, StudentGrant, EmploymentRecord, GradeRecord,
        StudentDiscipline, StudentDormVisit, Student, ClassModel,
        Note, Countdown, Project
    )

    payload = payload or {}

    # 日期窗口
    today = datetime.now().date()
    week_offset = int(payload.get('week_offset', 0))
    base = today + timedelta(weeks=week_offset)
    ws = base - timedelta(days=base.weekday())  # 周一
    we = ws + timedelta(days=6)                 # 周日
    nws = we + timedelta(days=1)
    nwe = nws + timedelta(days=6)

    def _in_week(d):
        """日期是否在 [ws, we] 区间内"""
        if d is None:
            return False
        try:
            if isinstance(d, str):
                d = datetime.strptime(str(d)[:10], '%Y-%m-%d').date()
            elif isinstance(d, datetime):
                d = d.date()
            return ws <= d <= we
        except Exception:
            return False

    def _in_next_week(d):
        if d is None:
            return False
        try:
            if isinstance(d, str):
                d = datetime.strptime(str(d)[:10], '%Y-%m-%d').date()
            elif isinstance(d, datetime):
                d = d.date()
            return nws <= d <= nwe
        except Exception:
            return False

    def _fmt_date(d):
        if d is None:
            return '??-??'
        try:
            if isinstance(d, str):
                return str(d)[:10]
            return d.strftime('%m-%d')
        except Exception:
            return str(d)[:10]

    def _stu(sid):
        s = db.query(Student).get(sid) if sid else None
        if s:
            cn = s.class_obj.class_name if s.class_obj else ''
            return s.name, cn
        return '(未知)', ''

    def _names(records):
        names = []
        for r in records[:5]:
            n, _ = _stu(r.student_id)
            names.append(n)
        return '、'.join(names)

    MAX_PER_DIM = int(payload.get('max_per_dim', 15))

    dims = payload.get('dimensions')
    if isinstance(dims, list) and dims:
        pass
    else:
        dims = ['academic', 'party', 'psychology', 'aid', 'employment', 'daily', 'activity']

    fmt = (payload.get('format') or 'mixed').lower()
    if fmt not in ('bullet', 'paragraph', 'mixed'):
        fmt = 'mixed'

    def _render(cfg, mode):
        parts = [cfg['title']]
        if mode in ('paragraph', 'mixed'):
            parts.append(cfg.get('header', ''))
            parts.append(cfg.get('narrative', ''))
            parts.append('')
        if mode in ('bullet', 'mixed'):
            for b in cfg.get('bullets', [])[:MAX_PER_DIM]:
                parts.append(b)
            if cfg.get('kpis'):
                kpi_line = ' '.join(f'{e} {n}={c}' for e, n, c in cfg['kpis'])
                parts.append(f'> {kpi_line}')
            parts.append('')
        return '\n'.join(parts)

    sections = []
    sections.append(f'# 第{today.isocalendar()[1]}周工作汇总（{ws} ~ {we}）\n')

    # ---------- 学业 ----------
    if 'academic' in dims:
        warns = [w for w in db.query(WarningRecord).all() if _in_week(w.created_at)]
        new_grades = [g for g in db.query(GradeRecord).all() if _in_week(g.created_at)]

        bullets = []
        for w in warns[:MAX_PER_DIM]:
            name, cn = _stu(w.student_id)
            bullets.append(f'- ⚠️ {_fmt_date(w.created_at)} · {name}（{cn}）· {w.warning_type or "预警"} · 触发条件：{(w.trigger_reason or "").strip()[:50]}')
        for g in new_grades[:MAX_PER_DIM]:
            name, cn = _stu(g.student_id)
            bullets.append(f'- 📝 {_fmt_date(g.created_at)} · {name}（{cn}）· {g.course_name}：{g.score if g.score is not None else "？"}分')

        parts = []
        if warns:
            parts.append(f'新增学业预警 {len(warns)} 条（{_names(warns)}）')
        if new_grades:
            parts.append(f'录入成绩 {len(new_grades)} 条')
        if parts:
            narrative = f'**学业**：本周' + '，'.join(parts) + '。'
        else:
            narrative = '**学业**：本周无新增学业预警或成绩录入。'
        kpis = []
        if warns:
            kpis.append(('⚠️', '预警', len(warns)))
        if new_grades:
            kpis.append(('📝', '成绩', len(new_grades)))

        sections.append(_render({
            'title': '## 📚 学业情况',
            'header': f'本周学业合计 **{len(warns) + len(new_grades)}** 项：',
            'narrative': narrative,
            'bullets': bullets, 'kpis': kpis,
        }, fmt))

    # ---------- 党团 ----------
    if 'party' in dims:
        progresses = [p for p in db.query(PartyProgress).all() if _in_week(p.created_at)]
        bullets = []
        for p in progresses[:MAX_PER_DIM]:
            name, cn = _stu(p.student_id)
            bullets.append(f'- 🚩 {_fmt_date(p.created_at)} · {name}（{cn}）· 阶段：{p.stage or "未指定"}' +
                           (f' · 培养联系人：{p.contact_person}' if p.contact_person else ''))
        if progresses:
            narrative = f'**党团发展**：本周新增发展记录 {len(progresses)} 条（{_names(progresses)}）。'
        else:
            narrative = '**党团发展**：本周无新增党团发展记录。'
        kpis = [('🚩', '发展', len(progresses))] if progresses else []
        sections.append(_render({
            'title': '## 🚩 党团发展',
            'header': f'本周新增发展记录 **{len(progresses)}** 条：',
            'narrative': narrative, 'bullets': bullets, 'kpis': kpis,
        }, fmt))

    # ---------- 心理 ----------
    if 'psychology' in dims:
        recs = [r for r in db.query(PsychologyRecord).all() if _in_week(r.record_date)]
        bullets = []
        for r in recs[:MAX_PER_DIM]:
            name, cn = _stu(r.student_id)
            bullets.append(f'- 🧠 {_fmt_date(r.record_date)} · {name}（{cn}）· 类型：{r.record_type or "面谈"}' +
                           (f' · 严重程度：{r.severity}' if r.severity else ''))
        if recs:
            narrative = f'**心理辅导**：本周记录 {len(recs)} 条（{_names(recs)}）。'
        else:
            narrative = '**心理辅导**：本周无新增心理辅导记录。'
        kpis = [('🧠', '辅导', len(recs))] if recs else []
        sections.append(_render({
            'title': '## 🧠 心理辅导',
            'header': f'本周心理辅导记录 **{len(recs)}** 条：',
            'narrative': narrative, 'bullets': bullets, 'kpis': kpis,
        }, fmt))

    # ---------- 资助 ----------
    if 'aid' in dims:
        grants = [g for g in db.query(StudentGrant).all() if _in_week(g.created_at)]
        bullets = []
        for g in grants[:MAX_PER_DIM]:
            name, cn = _stu(g.student_id)
            bullets.append(f'- 💰 {_fmt_date(g.created_at)} · {name}（{cn}）· {g.grant_type or "助学金"} · ¥{g.amount or 0}')
        if grants:
            narrative = f'**资助**：本周发放/确认助学金 {len(grants)} 笔（{_names(grants)}）。'
        else:
            narrative = '**资助**：本周无新增资助记录。'
        kpis = [('💰', '资助', len(grants))] if grants else []
        sections.append(_render({
            'title': '## 💰 资助工作',
            'header': f'本周资助记录 **{len(grants)}** 笔：',
            'narrative': narrative, 'bullets': bullets, 'kpis': kpis,
        }, fmt))

    # ---------- 就业 ----------
    if 'employment' in dims:
        emps = [e for e in db.query(EmploymentRecord).all() if _in_week(e.created_at)]
        bullets = []
        for e in emps[:MAX_PER_DIM]:
            name, cn = _stu(e.student_id)
            bullets.append(f'- 💼 {_fmt_date(e.created_at)} · {name}（{cn}）· {e.intention_type or "未填"} · {(e.internship_company or "").strip()[:30]}')
        if emps:
            narrative = f'**就业**：本周新增就业记录 {len(emps)} 条（{_names(emps)}）。'
        else:
            narrative = '**就业**：本周无新增就业升学记录。'
        kpis = [('💼', '就业', len(emps))] if emps else []
        sections.append(_render({
            'title': '## 💼 就业升学',
            'header': f'本周就业升学记录 **{len(emps)}** 条：',
            'narrative': narrative, 'bullets': bullets, 'kpis': kpis,
        }, fmt))

    # ---------- 日常（家校+违纪+走访） ----------
    if 'daily' in dims:
        fc = [r for r in db.query(FamilyContact).all() if _in_week(r.contact_date)]
        dc = [r for r in db.query(StudentDiscipline).all() if _in_week(r.discipline_date)]
        vs = [r for r in db.query(StudentDormVisit).all() if _in_week(r.visit_date)]

        bullets = []
        for r in fc:
            name, cn = _stu(r.student_id)
            bullets.append(f'- {_fmt_date(r.contact_date)} · 联系 {name}（{cn}）家长 {r.parent_name or ""} · 方式：{r.contact_method or "电话"} · 主题：{r.topic or "常规沟通"}')
        for r in dc:
            name, cn = _stu(r.student_id)
            bullets.append(f'- {_fmt_date(r.discipline_date)} · {name}（{cn}）· {r.level or ""}{r.discipline_type or "处分"} · 原因：{(r.reason or "").strip()[:40]}')
        for r in vs:
            name, cn = _stu(r.student_id)
            sit = (r.situation or '').strip()[:40]
            bullets.append(f'- {_fmt_date(r.visit_date)} · 走访 {name}（{cn}）· 寝室 {r.dorm_room or "?"} · 走访人：{r.visitor or "本人"}' + (f' · {sit}' if sit else ''))

        parts = []
        if fc: parts.append(f'家校沟通 {len(fc)} 次（{_names(fc)}）')
        if dc: parts.append(f'违纪处理 {len(dc)} 次（{_names(dc)}）')
        if vs: parts.append(f'宿舍走访 {len(vs)} 次（{_names(vs)}）')
        if parts:
            narrative = f'**日常事务**：本周' + '、'.join(parts) + '。'
        else:
            narrative = '**日常事务**：本周日常事务平稳，无违纪、无重要家校沟通、无宿舍走访记录。'
        kpis = []
        if fc: kpis.append(('📞','家校沟通',len(fc)))
        if dc: kpis.append(('⚠️','违纪',len(dc)))
        if vs: kpis.append(('🏠','宿舍走访',len(vs)))

        sections.append(_render({
            'title': '## 📖 日常事务',
            'header': f'本周日常事务合计 **{len(fc)+len(dc)+len(vs)}** 项：',
            'narrative': narrative,
            'bullets': bullets, 'kpis': kpis,
        }, fmt))

    # ---------- 活动（含班会） ----------
    if 'activity' in dims:
        acts = [a for a in db.query(Activity).all() if _in_week(a.activity_date)]
        meets = [m for m in db.query(ClassMeeting).all() if _in_week(m.meeting_date)]

        bullets = []
        for a in acts:
            bullets.append(f'- {_fmt_date(a.activity_date)} · **{a.title}**' +
                           (f' · 地点：{a.location}' if a.location else '') +
                           (f' · 类型：{a.activity_type}' if a.activity_type else '') +
                           (f' · 状态：{a.status}' if a.status else ''))
        for m in meets:
            cls = db.query(ClassModel).get(m.class_id) if m.class_id else None
            cn = cls.class_name if cls else '(未指定班级)'
            bullets.append(f'- {_fmt_date(m.meeting_date)} · {cn} · 主题：{m.topic or "常规班会"} · 出勤 {m.attendance_count or 0} 人' +
                           (f' · 结论：{(m.resolution or "").strip()[:40]}' if m.resolution else ''))

        parts = []
        if acts: parts.append(f'组织学院/学生活动 {len(acts)} 场（{"、".join([a.title for a in acts[:5]])}）')
        if meets: parts.append(f'开展班会 {len(meets)} 次')
        if parts:
            narrative = f'**活动 & 班会**：本周' + '，'.join(parts) + '。'
        else:
            narrative = '**活动 & 班会**：本周无组织的学院活动或班会，可结合校历安排下周事项。'
        kpis = []
        if acts: kpis.append(('🎨','活动',len(acts)))
        if meets: kpis.append(('🏫','班会',len(meets)))

        sections.append(_render({
            'title': '## 🎨 活动 & 班会',
            'header': f'本周活动 **{len(acts)}** 场 · 班会 **{len(meets)}** 次：',
            'narrative': narrative,
            'bullets': bullets, 'kpis': kpis,
        }, fmt))

    # ---------- 本周日程回顾（结合日程本：Note done + Countdown + Project 进度） ----------
    notes_done_week = [n for n in db.query(Note).all()
                       if n.status == 'done' and (_in_week(n.due_date) or _in_week(str(n.updated_at)))]
    countdowns_week = [c for c in db.query(Countdown).all() if _in_week(c.target_date)]
    projects_active = db.query(Project).filter(Project.status == 'active').all()
    projects_touched_week = [p for p in projects_active
                             if _in_week(p.start_date) or _in_week(p.end_date)]

    bullets_done = []
    for n in notes_done_week[:MAX_PER_DIM]:
        bullets_done.append(f'- ✅ {_fmt_date(n.due_date or str(n.updated_at)[:10])} · {n.title or "(无标题)"}' +
                            (f' · {(n.content or "").strip()[:30]}' if n.content else ''))
    for c in countdowns_week[:MAX_PER_DIM]:
        bullets_done.append(f'- 📅 {_fmt_date(c.target_date)} · **{c.title}**（{c.category or "校历"}）')
    for p in projects_touched_week[:MAX_PER_DIM]:
        bullets_done.append(f'- 🎯 项目 **{p.name}** · 进度 {p.progress}%' +
                            (f' · 起止 {p.start_date} ~ {p.end_date}' if p.start_date else ''))

    if bullets_done:
        narrative_done = (
            f'**本周日程回顾**：完成待办 {len(notes_done_week)} 项，'
            f'触达校历节点 {len(countdowns_week)} 个，推进中的专项工作 {len(projects_touched_week)} 项。'
        )
    else:
        narrative_done = '**本周日程回顾**：本周日程本无已完成待办或校历节点，可按计划稳步推进。'
    sections.append(_render({
        'title': '## 🗓️ 本周日程回顾',
        'header': f'本周完成 {len(notes_done_week)} 项待办 · 校历节点 {len(countdowns_week)} 个 · 项目触达 {len(projects_touched_week)} 项',
        'narrative': narrative_done,
        'bullets': bullets_done,
        'kpis': [('✅','已完成待办',len(notes_done_week)),
                 ('📅','校历节点',len(countdowns_week)),
                 ('🎯','项目触达',len(projects_touched_week))],
    }, fmt))

    # ---------- 下周计划提醒 ----------
    notes_todo_next = [n for n in db.query(Note).all()
                       if n.category == 'todo' and n.status != 'done' and _in_next_week(n.due_date)]
    countdowns_next = [c for c in db.query(Countdown).all() if _in_next_week(c.target_date)]
    acts_next = [a for a in db.query(Activity).all() if _in_next_week(a.activity_date)]
    meets_next = [m for m in db.query(ClassMeeting).all() if _in_next_week(m.meeting_date)]

    bullets_next = []
    for n in notes_todo_next[:MAX_PER_DIM]:
        prio = ['低','中','高'][n.priority or 0] if (n.priority or 0) <= 2 else '高'
        bullets_next.append(f'- ☑️ {_fmt_date(n.due_date)} · [{prio}] {n.title or "(无标题)"}')
    for c in countdowns_next[:MAX_PER_DIM]:
        bullets_next.append(f'- 📅 {_fmt_date(c.target_date)} · **{c.title}**（{c.category or "校历"}）')
    for a in acts_next[:MAX_PER_DIM]:
        bullets_next.append(f'- 🎨 {_fmt_date(a.activity_date)} · {a.title}' + (f' · {a.location}' if a.location else ''))
    for m in meets_next[:MAX_PER_DIM]:
        cls = db.query(ClassModel).get(m.class_id) if m.class_id else None
        cn = cls.class_name if cls else '(未指定班级)'
        bullets_next.append(f'- 🏫 {_fmt_date(m.meeting_date)} · {cn} · {m.topic or "班会"}')

    total_next = len(notes_todo_next) + len(countdowns_next) + len(acts_next) + len(meets_next)
    if total_next:
        narrative_next = (
            f'**下周计划提醒**（{nws} ~ {nwe}）：待办 {len(notes_todo_next)} 项、校历节点 {len(countdowns_next)} 个、'
            f'活动 {len(acts_next)} 场、班会 {len(meets_next)} 次，请提前安排时间与资源。'
        )
    else:
        narrative_next = f'**下周计划提醒**（{nws} ~ {nwe}）：日程本暂无预设事项，可尽早规划下周重点工作。'
    sections.append(_render({
        'title': '## 📌 下周计划提醒',
        'header': f'下周共 {total_next} 项预设事项：',
        'narrative': narrative_next,
        'bullets': bullets_next,
        'kpis': [('☑️','待办',len(notes_todo_next)),
                 ('📅','校历',len(countdowns_next)),
                 ('🎨','活动',len(acts_next)),
                 ('🏫','班会',len(meets_next))],
    }, fmt))

    # ---------- 收尾 ----------
    sections.append('---\n')
    sections.append('*本汇总由系统按数据库真实记录自动汇编 · 三种模式（要点列表 / 叙事段落 / 图文混合）根据 format 参数切换 · 结尾已联动日程本给出本周回顾与下周计划。*')

    content = '\n'.join(sections)

    summary = WS(week_start=ws, week_end=we, content=content, summary_type='auto',
                 title=f'第{today.isocalendar()[1]}周工作汇总（{ws}~{we}）')
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return {'id': summary.id, 'content': content, 'dimensions': dims, 'format': fmt}


@router.put('/weekly-summaries/{sid}')
def update_weekly_summary(sid: int, data: dict, db: Session = Depends(get_db)):
    from models import WeeklySummary as WS
    s = db.query(WS).get(sid)
    if not s:
        raise HTTPException(404)
    for k, v in data.items():
        if hasattr(s, k):
            setattr(s, k, v)
    db.commit()
    return {'ok': True}


@router.delete('/weekly-summaries/{sid}')
def delete_weekly_summary(sid: int, db: Session = Depends(get_db)):
    from models import WeeklySummary as WS
    s = db.query(WS).get(sid)
    if s:
        db.delete(s)
        db.commit()
    return {'ok': True}


# ===== AI 智能导入 =====
@router.post('/smart-import/preview')
def smart_import_preview(data: dict, db: Session = Depends(get_db)):
    """AI智能导入预览 - 解析列名并映射"""
    import re
    rows = data.get('rows', [])
    headers = data.get('headers', [])

    if not headers or not rows:
        return {'error': '无数据'}

    # 同义词映射表
    synonym_map = {
        'student_no': ['学号', '学生编号', '学生号', '编号', 'student_no', 'student_id'],
        'name': ['姓名', '学生姓名', '名字', '名', 'name'],
        'gender': ['性别', '男女', 'sex', 'gender'],
        'class_name': ['班级', '所在班级', '班级号', 'class', 'class_name'],
        'major': ['专业', '所学专业', '专业名称', 'major'],
        'political_status': ['政治面貌', '政治身份', 'political_status'],
        'phone': ['联系电话', '手机号', '电话', 'phone', 'tel'],
        'parent_phone': ['家长电话', '紧急联系电话', '家庭联系方式', 'parent_phone'],
        'birth_date': ['出生日期', '出生年月', 'birthday', 'birth_date'],
        'birth_source': ['生源地', '籍贯', '生源省份', 'birth_source'],
        'email': ['邮箱', '电子邮件', 'email'],
        'family_situation': ['家庭情况', '家庭状况', 'family_situation'],
    }

    # 自动映射
    mapping = {}
    for i, h in enumerate(headers):
        h_clean = h.strip()
        for field, synonyms in synonym_map.items():
            if h_clean in synonyms or any(s in h_clean for s in synonyms):
                mapping[i] = {'header': h_clean, 'field': field}
                break
        if i not in mapping:
            mapping[i] = {'header': h_clean, 'field': ''}

    # 前5行预览
    preview_rows = []
    for row in rows[:5]:
        preview_rows.append([str(cell) if cell is not None else '' for cell in row])

    return {'mapping': mapping, 'preview_rows': preview_rows, 'total_rows': len(rows)}


@router.post('/smart-import/execute')
def smart_import_execute(data: dict, db: Session = Depends(get_db)):
    """执行智能导入"""
    from models import Student
    rows = data.get('rows', [])
    mapping = data.get('mapping', {})
    conflict_action = data.get('conflict_action', 'skip')  # skip/overwrite

    # 反转映射: field -> column_index
    field_to_col = {}
    for col_idx_str, m in mapping.items():
        col_idx = int(col_idx_str)
        field = m.get('field', '')
        if field:
            field_to_col[field] = col_idx

    imported = 0
    skipped = 0
    for row in rows:
        student_data = {}
        for field, col_idx in field_to_col.items():
            if col_idx < len(row):
                val = row[col_idx]
                student_data[field] = str(val).strip() if val is not None else ''

        student_no = student_data.get('student_no', '')
        if not student_no:
            skipped += 1
            continue

        existing = db.query(Student).filter(Student.student_no == student_no).first()
        if existing:
            if conflict_action == 'skip':
                skipped += 1
                continue
            elif conflict_action == 'overwrite':
                for k, v in student_data.items():
                    if k != 'student_no':
                        setattr(existing, k, v)
                imported += 1
            else:  # keep_both
                s = Student(**student_data)
                db.add(s)
                imported += 1
        else:
            s = Student(**student_data)
            db.add(s)
            imported += 1

    db.commit()
    return {'imported': imported, 'skipped': skipped, 'total': len(rows)}
