"""知识库 + FAQ + 文书生成 + 周汇总 路由"""
import json
from fastapi import APIRouter, Depends, HTTPException
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


# ===== 文书生成 =====
@router.get('/document-templates')
def list_templates(db: Session = Depends(get_db)):
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


@router.post('/documents/generate')
def generate_document(data: dict, db: Session = Depends(get_db)):
    """基于模板和学生数据生成文书"""
    student_id = data.get('student_id')
    template_id = data.get('template_id')
    doc_type = data.get('doc_type', '')
    title = data.get('title', '')

    content = ''
    if template_id:
        tpl = db.query(DocumentTemplate).get(template_id)
        if tpl:
            content = tpl.content

    if student_id:
        stu = db.query(Student).get(student_id)
        if stu:
            cls_name = stu.class_obj.class_name if stu.class_obj else ''
            major_name = ''
            if stu.class_obj and stu.class_obj.major:
                major_name = stu.class_obj.major.major_name
            content = content.replace('{{姓名}}', stu.name or '')
            content = content.replace('{{学号}}', stu.student_no or '')
            content = content.replace('{{性别}}', stu.gender or '')
            content = content.replace('{{专业}}', major_name)
            content = content.replace('{{班级}}', cls_name)
            content = content.replace('{{政治面貌}}', stu.political_status or '群众')

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
    """自动生成周汇总（叙事型：具体时间、地点、事件、当事人）
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
        StudentDiscipline, StudentDormVisit, Student, ClassModel
    )

    payload = payload or {}
    dims = payload.get('dimensions') or ['academic','party','psychology','aid','employment','daily','activity']
    fmt  = payload.get('format') or 'bullet'
    week_offset = int(payload.get('week_offset') or 0)

    today = datetime.now() + timedelta(weeks=week_offset)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    ws = week_start.strftime('%Y-%m-%d')
    we = week_end.strftime('%Y-%m-%d')

    # 学生 id → (姓名, 班级) 查询缓存
    _stu_cache = {}
    def _stu(sid):
        if sid in _stu_cache:
            return _stu_cache[sid]
        s = db.query(Student).get(sid) if sid else None
        if s:
            cn = s.class_obj.class_name if s.class_obj else ''
            _stu_cache[sid] = (s.name or '未命名', cn)
        else:
            _stu_cache[sid] = ('未知学生', '')
        return _stu_cache[sid]

    def _fmt_date(d):
        """YYYY-MM-DD -> MM-DD 周X"""
        if not d:
            return '日期未记录'
        try:
            dt = datetime.strptime(d[:10], '%Y-%m-%d')
            wk = ['一','二','三','四','五','六','日'][dt.weekday()]
            return f'{dt.strftime("%m-%d")}（周{wk}）'
        except Exception:
            return d

    def _in_week(d):
        if not d:
            return False
        try:
            return ws <= d[:10] <= we
        except Exception:
            return False

    MAX_PER_DIM = 20
    sections = [f'# 第 {today.isocalendar()[1]} 周工作汇总  ·  {ws} ~ {we}\n',
                f'> 本周共 7 天，以下按业务维度回顾具体开展的工作。\n']

    # ---------- 学业 ----------
    if 'academic' in dims:
        warns_all = db.query(WarningRecord).order_by(WarningRecord.created_at.desc()).all()
        warns_week = [w for w in warns_all if _in_week(str(w.created_at))]
        lines = []
        if warns_week:
            lines.append(f'本周新增学业预警 **{len(warns_week)}** 条：')
            for w in warns_week[:MAX_PER_DIM]:
                name, cn = _stu(w.student_id)
                tag = '🔴红牌' if w.warning_type == 'red' else '🟡黄牌'
                lines.append(f'- {_fmt_date(str(w.created_at)[:10])} · {tag} · {name}（{cn}） · {w.description or "详见预警记录"}')
        else:
            lines.append('本周未新增学业预警，学业风险总体平稳。')
        # 挂科增量
        fail_this = db.query(GradeRecord).filter(GradeRecord.score < 60).count()
        lines.append(f'\n**学业总览**：累计挂科记录 {fail_this} 条，历史预警 {len(warns_all)} 条。')
        sections.append('## 📚 学业跟踪\n' + '\n'.join(lines) + '\n')

    # ---------- 谈心谈话 ----------
    if 'psychology' in dims:
        recs = db.query(PsychologyRecord).all()
        week_recs = [r for r in recs if _in_week(r.record_date)]
        lines = []
        if week_recs:
            lines.append(f'本周开展谈心谈话 **{len(week_recs)}** 次：')
            for r in week_recs[:MAX_PER_DIM]:
                name, cn = _stu(r.student_id)
                loc = r.location or '未记录地点'
                topic = r.topic or '常规谈话'
                summary = (r.summary or '').replace('\n',' ').strip()[:60]
                follow = f'（后续 {r.next_follow_date} 再跟进）' if r.next_follow_date else ''
                lines.append(f'- {_fmt_date(r.record_date)} · 与 **{name}**（{cn}）在 {loc} 谈心 · 主题：{topic}' +
                             (f' · 要点：{summary}' if summary else '') + follow)
        else:
            lines.append('本周未记录谈心谈话，可关注情绪波动学生主动约谈。')
        sections.append('## 💚 谈心谈话\n' + '\n'.join(lines) + '\n')

    # ---------- 党团 ----------
    if 'party' in dims:
        recs = db.query(PartyProgress).all()
        week_recs = [r for r in recs if _in_week(r.stage_date) or _in_week(str(r.created_at))]
        lines = []
        if week_recs:
            lines.append(f'本周党团发展节点 **{len(week_recs)}** 项：')
            for r in week_recs[:MAX_PER_DIM]:
                name, cn = _stu(r.student_id)
                notes = (r.notes or '').strip()[:40]
                lines.append(f'- {_fmt_date(r.stage_date or str(r.created_at)[:10])} · {name}（{cn}）· 进入「**{r.stage}**」阶段' +
                             (f' · 联系人：{r.contact_person}' if r.contact_person else '') +
                             (f' · {notes}' if notes else ''))
        else:
            lines.append('本周无党团发展节点变动。')
        sections.append('## 🚩 党团建设\n' + '\n'.join(lines) + '\n')

    # ---------- 资助 ----------
    if 'aid' in dims:
        recs = db.query(StudentGrant).all()
        week_recs = [r for r in recs if _in_week(str(r.created_at))]
        lines = []
        if week_recs:
            lines.append(f'本周资助/助学金动态 **{len(week_recs)}** 条：')
            for r in week_recs[:MAX_PER_DIM]:
                name, cn = _stu(r.student_id)
                lines.append(f'- {_fmt_date(str(r.created_at)[:10])} · {name}（{cn}） · {r.grant_type or "资助"} ¥{r.amount:.0f}' +
                             (f' · {r.notes}' if r.notes else ''))
        else:
            lines.append('本周资助无变动，如临学期节点可发起复核。')
        sections.append('## 💰 资助帮扶\n' + '\n'.join(lines) + '\n')

    # ---------- 就业 ----------
    if 'employment' in dims:
        recs = db.query(EmploymentRecord).all()
        week_recs = [r for r in recs if _in_week(r.offer_date) or _in_week(str(r.created_at))]
        lines = []
        if week_recs:
            lines.append(f'本周就业进展 **{len(week_recs)}** 条：')
            for r in week_recs[:MAX_PER_DIM]:
                name, cn = _stu(r.student_id)
                bits = []
                if r.status: bits.append(r.status)
                if r.target_industry: bits.append(r.target_industry)
                if r.target_position: bits.append(r.target_position)
                if r.internship_company: bits.append(f'实习→{r.internship_company}')
                if r.salary_range: bits.append(f'薪资 {r.salary_range}')
                lines.append(f'- {_fmt_date(r.offer_date or str(r.created_at)[:10])} · {name}（{cn}）· ' + ' / '.join(bits))
        else:
            lines.append('本周就业无进展，可推送校招信息或组织宣讲会。')
        sections.append('## 🎯 就业跟踪\n' + '\n'.join(lines) + '\n')

    # ---------- 日常（家校+违纪+走访） ----------
    if 'daily' in dims:
        lines = []
        fc = [r for r in db.query(FamilyContact).all() if _in_week(r.contact_date)]
        dc = [r for r in db.query(StudentDiscipline).all() if _in_week(r.discipline_date)]
        vs = [r for r in db.query(StudentDormVisit).all() if _in_week(r.visit_date)]
        if fc:
            lines.append(f'**家校沟通** {len(fc)} 次：')
            for r in fc[:MAX_PER_DIM]:
                name, cn = _stu(r.student_id)
                lines.append(f'- {_fmt_date(r.contact_date)} · 联系 {name}（{cn}）家长 {r.parent_name or ""} · 方式：{r.contact_method or "电话"} · 主题：{r.topic or "常规沟通"}')
        if dc:
            lines.append(f'\n**违纪处理** {len(dc)} 次：')
            for r in dc[:MAX_PER_DIM]:
                name, cn = _stu(r.student_id)
                lines.append(f'- {_fmt_date(r.discipline_date)} · {name}（{cn}）· {r.level or ""}{r.discipline_type or "处分"} · 原因：{(r.reason or "").strip()[:40]}')
        if vs:
            lines.append(f'\n**宿舍走访** {len(vs)} 次：')
            for r in vs[:MAX_PER_DIM]:
                name, cn = _stu(r.student_id)
                sit = (r.situation or '').strip()[:40]
                lines.append(f'- {_fmt_date(r.visit_date)} · 走访 {name}（{cn}）· 寝室 {r.dorm_room or "?"} · 走访人：{r.visitor or "本人"}' + (f' · {sit}' if sit else ''))
        if not (fc or dc or vs):
            lines.append('本周日常事务平稳，无违纪、无重要家校沟通、无宿舍走访记录。')
        sections.append('## 📖 日常事务\n' + '\n'.join(lines) + '\n')

    # ---------- 活动（含班会） ----------
    if 'activity' in dims:
        acts = [a for a in db.query(Activity).all() if _in_week(a.activity_date)]
        meets = [m for m in db.query(ClassMeeting).all() if _in_week(m.meeting_date)]
        lines = []
        if acts:
            lines.append(f'**学院/学生活动** {len(acts)} 场：')
            for a in acts[:MAX_PER_DIM]:
                lines.append(f'- {_fmt_date(a.activity_date)} · **{a.title}**' +
                             (f' · 地点：{a.location}' if a.location else '') +
                             (f' · 类型：{a.activity_type}' if a.activity_type else '') +
                             (f' · 状态：{a.status}' if a.status else ''))
        if meets:
            lines.append(f'\n**班会** {len(meets)} 次：')
            for m in meets[:MAX_PER_DIM]:
                cls = db.query(ClassModel).get(m.class_id) if m.class_id else None
                cn = cls.class_name if cls else '(未指定班级)'
                lines.append(f'- {_fmt_date(m.meeting_date)} · {cn} · 主题：{m.topic or "常规班会"} · 出勤 {m.attendance_count or 0} 人' +
                             (f' · 结论：{(m.resolution or "").strip()[:40]}' if m.resolution else ''))
        if not (acts or meets):
            lines.append('本周无组织的学院活动或班会，可结合校历安排下周事项。')
        sections.append('## 🎨 活动 & 班会\n' + '\n'.join(lines) + '\n')

    # ---------- 收尾：本周关键词 ----------
    sections.append('---\n')
    sections.append('*本汇总由系统按数据库真实记录自动汇编，可点击"手写补充"添加更多定性描述。*')

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
