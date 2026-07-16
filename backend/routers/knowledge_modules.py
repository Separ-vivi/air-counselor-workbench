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
            content = content.replace('{{姓名}}', stu.name)
            content = content.replace('{{学号}}', stu.student_no)
            content = content.replace('{{性别}}', stu.gender)
            content = content.replace('{{专业}}', stu.major)
            content = content.replace('{{班级}}', stu.class_name)
            content = content.replace('{{政治面貌}}', stu.political_status)

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
def generate_weekly_summary(db: Session = Depends(get_db)):
    """自动生成周汇总"""
    from datetime import datetime, timedelta
    from models import PsychologyRecord, FamilyContact, PartyProgress, WarningRecord, ClassMeeting, WeeklySummary as WS

    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    ws = week_start.strftime('%Y-%m-%d')
    we = week_end.strftime('%Y-%m-%d')

    sections = []
    sections.append(f'# 第{today.isocalendar()[1]}周工作汇总 ({ws} ~ {we})\n')

    # 心理关怀
    psych_count = db.query(PsychologyRecord).count()
    sections.append(f'## 心理关怀\n- 累计谈心记录: {psych_count}条\n')

    # 家校沟通
    family_count = db.query(FamilyContact).count()
    sections.append(f'## 家校沟通\n- 累计沟通记录: {family_count}条\n')

    # 预警
    warning_count = db.query(WarningRecord).count()
    sections.append(f'## 学业预警\n- 累计预警: {warning_count}条\n')

    # 党团
    party_count = db.query(PartyProgress).count()
    sections.append(f'## 党团发展\n- 累计进度记录: {party_count}条\n')

    # 班会
    meeting_count = db.query(ClassMeeting).count()
    sections.append(f'## 班会记录\n- 累计班会: {meeting_count}次\n')

    content = '\n'.join(sections)

    summary = WS(week_start=ws, week_end=we, content=content, summary_type='auto')
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return {'id': summary.id, 'content': content}


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
