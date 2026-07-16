"""党团发展 + 心理关怀 + 家校沟通 路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import PartyProgress, PsychologyRecord, FamilyContact, Student, ClassModel

router = APIRouter(prefix='/api')


# ===== 党团发展 =====
@router.get('/party-progress')
def list_party_progress(db: Session = Depends(get_db)):
    progress_list = db.query(PartyProgress).all()
    class_map = {c.id: c.class_name for c in db.query(ClassModel).all()}
    result = []
    for p in progress_list:
        stu = db.query(Student).get(p.student_id)
        result.append({
            'id': p.id, 'student_id': p.student_id, 'stage': p.stage,
            'stage_date': p.stage_date, 'contact_person': p.contact_person,
            'notes': p.notes, 'student_name': stu.name if stu else '',
            'student_no': stu.student_no if stu else '',
            'class_name': class_map.get(stu.class_id, '') if stu else '',
        })
    return result


@router.post('/party-progress')
def create_party_progress(data: dict, db: Session = Depends(get_db)):
    p = PartyProgress(**data)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {'id': p.id}


@router.put('/party-progress/{pid}')
def update_party_progress(pid: int, data: dict, db: Session = Depends(get_db)):
    p = db.query(PartyProgress).get(pid)
    if not p:
        raise HTTPException(404, '记录不存在')
    for k, v in data.items():
        if hasattr(p, k):
            setattr(p, k, v)
    db.commit()
    return {'ok': True}


@router.delete('/party-progress/{pid}')
def delete_party_progress(pid: int, db: Session = Depends(get_db)):
    p = db.query(PartyProgress).get(pid)
    if p:
        db.delete(p)
        db.commit()
    return {'ok': True}


@router.get('/party-progress/overview')
def party_progress_overview(
    class_id: Optional[int] = None,
    class_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """党团发展全景表 - 支持按 class_id 或 class_name 筛选（含'群众'状态）"""
    stages = ['群众', '递交入党申请书', '团员', '积极分子', '发展对象', '预备党员', '正式党员']
    q = db.query(Student)
    if class_id is not None:
        q = q.filter(Student.class_id == class_id)
    elif class_name:
        # 兼容旧调用：class_name → class_id 转换
        target = db.query(ClassModel).filter(ClassModel.class_name == class_name).first()
        if target:
            q = q.filter(Student.class_id == target.id)
        else:
            return {'stages': stages, 'students': []}
    students = q.all()

    # 预加载班级映射，避免 N+1
    class_map = {c.id: c for c in db.query(ClassModel).all()}

    result = []
    for s in students:
        progress_list = db.query(PartyProgress).filter(
            PartyProgress.student_id == s.id
        ).order_by(PartyProgress.created_at.desc()).all()
        # 默认阶段：政治面貌里含"党员/团员/群众"就用该值，否则未记录
        if progress_list:
            current_stage = progress_list[0].stage
        elif s.political_status:
            current_stage = s.political_status
        else:
            current_stage = '群众'
        cls = class_map.get(s.class_id)
        result.append({
            'student_id': s.id, 'name': s.name, 'student_no': s.student_no,
            'class_id': s.class_id,
            'class_name': cls.class_name if cls else '',
            'current_stage': current_stage,
            'political_status': s.political_status or '群众',
            'progress_count': len(progress_list),
        })
    return {'stages': stages, 'students': result}


@router.get('/party-progress/detail/{student_id}')
def party_progress_detail(student_id: int, db: Session = Depends(get_db)):
    """党团发展详情 - 时间线视图"""
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(404, '学生不存在')
    
    progress_list = db.query(PartyProgress).filter(
        PartyProgress.student_id == student_id
    ).order_by(PartyProgress.stage_date.asc()).all()
    
    # 6大阶段定义
    stage_definitions = [
        {'key': '递交入党申请书', 'label': '递交入党申请书', 'description': '提交书面入党申请'},
        {'key': '积极分子', 'label': '确定为入党积极分子', 'description': '经团组织推优确定'},
        {'key': '发展对象', 'label': '确定为发展对象', 'description': '经过一年以上培养考察'},
        {'key': '预备党员', 'label': '接收为预备党员', 'description': '支部大会讨论通过'},
        {'key': '转正', 'label': '预备党员转正', 'description': '预备期满一年转正'},
        {'key': '正式党员', 'label': '正式党员', 'description': '完成全部发展流程'},
    ]
    
    # 构建时间线
    timeline = []
    progress_map = {p.stage: p for p in progress_list}
    current_stage_index = -1
    
    for i, stage_def in enumerate(stage_definitions):
        progress = progress_map.get(stage_def['key'])
        stage_info = {
            'stage': stage_def['key'],
            'label': stage_def['label'],
            'description': stage_def['description'],
            'completed': progress is not None,
            'date': progress.stage_date if progress else None,
            'contact_person': progress.contact_person if progress else None,
            'notes': progress.notes if progress else None,
            'is_current': False,
        }
        if progress:
            current_stage_index = i
        timeline.append(stage_info)
    
    # 标记当前阶段
    if current_stage_index >= 0 and current_stage_index < len(timeline):
        timeline[current_stage_index]['is_current'] = True
    
    # 获取班级/专业名（Student 没有 class_name/major 字段，需通过 relationship）
    cls_obj = db.query(ClassModel).get(student.class_id) if student.class_id else None
    major_obj = cls_obj.major if cls_obj else None
    return {
        'student': {
            'id': student.id,
            'name': student.name,
            'student_no': student.student_no,
            'class_name': cls_obj.class_name if cls_obj else '',
            'major': major_obj.major_name if major_obj else '',
        },
        'current_stage': progress_list[-1].stage if progress_list else '未记录',
        'timeline': timeline,
        'records': [
            {
                'id': p.id,
                'stage': p.stage,
                'stage_date': p.stage_date,
                'contact_person': p.contact_person,
                'notes': p.notes,
            }
            for p in progress_list
        ],
    }


@router.get('/party-progress/export')
def export_party_progress(
    stage: str = None,
    class_id: int = None,
    class_name: str = None,
    db: Session = Depends(get_db)
):
    """导出党团发展 Excel（支持按 class_id 或 class_name 筛选）"""
    from openpyxl import Workbook
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    from datetime import datetime
    
    query = db.query(PartyProgress, Student).join(Student, PartyProgress.student_id == Student.id)
    if stage:
        query = query.filter(PartyProgress.stage == stage)
    if class_id is not None:
        query = query.filter(Student.class_id == class_id)
    elif class_name:
        target = db.query(ClassModel).filter(ClassModel.class_name == class_name).first()
        if target:
            query = query.filter(Student.class_id == target.id)
    
    results = query.order_by(PartyProgress.stage_date.desc()).all()
    # 预加载班级名映射
    class_map = {c.id: c.class_name for c in db.query(ClassModel).all()}
    
    wb = Workbook()
    ws = wb.active
    ws.title = '党团发展'
    
    # 写入表头
    headers = ['学号', '姓名', '班级', '当前阶段', '阶段日期', '联系人', '备注']
    ws.append(headers)
    
    # 写入数据
    stage_map = {
        'application': '递交入党申请书',
        'activist': '入党积极分子',
        'development': '发展对象',
        'probation': '预备党员',
        'regularization': '预备党员转正',
        'full_member': '正式党员'
    }
    for progress, student in results:
        stage_date_str = progress.stage_date
        if hasattr(progress.stage_date, 'strftime'):
            stage_date_str = progress.stage_date.strftime('%Y-%m-%d')
        ws.append([
            student.student_no,
            student.name,
            class_map.get(student.class_id, ''),
            stage_map.get(progress.stage, progress.stage),
            stage_date_str or '',
            progress.contact_person or '',
            progress.notes or ''
        ])
    
    # 保存到内存
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f'party_progress_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# ===== 心理关怀 =====
def _psy_dict(r, db):
    from models import ClassModel
    stu = db.query(Student).get(r.student_id)
    cls_name = ''
    if stu and stu.class_id:
        cls = db.query(ClassModel).get(stu.class_id)
        cls_name = cls.class_name if cls else ''
    return {
        'id': r.id, 'student_id': r.student_id,
        'student_name': stu.name if stu else '',
        'student_no': stu.student_no if stu else '',
        'class_name': cls_name,
        'record_date': r.record_date, 'assessment_date': r.record_date,   # alias for frontend
        'location': r.location, 'topic': r.topic, 'summary': r.summary,
        'notes': r.summary,                                                 # alias
        'emotion_tags': r.emotion_tags, 'follow_up_plan': r.follow_up_plan,
        'next_follow_date': r.next_follow_date, 'next_follow_up': r.next_follow_date,  # alias
        'attention_level': getattr(r, 'attention_level', '') or '',
        'counseling_count': getattr(r, 'counseling_count', 0) or 0,
    }


def _psy_normalize_input(data: dict) -> dict:
    """接收前端字段 -> 转成 model 字段"""
    d = dict(data)
    if 'assessment_date' in d and 'record_date' not in d:
        d['record_date'] = d.pop('assessment_date')
    if 'next_follow_up' in d and 'next_follow_date' not in d:
        d['next_follow_date'] = d.pop('next_follow_up')
    if 'notes' in d and 'summary' not in d:
        d['summary'] = d.pop('notes')
    # 只保留 model 有的字段
    allowed = {'student_id','record_date','location','topic','summary','emotion_tags','follow_up_plan','next_follow_date','attention_level','counseling_count'}
    return {k: v for k, v in d.items() if k in allowed}


@router.get('/psychology')
def list_psychology(student_id: Optional[int] = None, attention_level: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(PsychologyRecord)
    if student_id:
        q = q.filter(PsychologyRecord.student_id == student_id)
    if attention_level:
        q = q.filter(PsychologyRecord.attention_level == attention_level)
    items = q.order_by(PsychologyRecord.created_at.desc()).all()
    return [_psy_dict(r, db) for r in items]


@router.get('/psychology/reminders')
def psychology_reminders(db: Session = Depends(get_db)):
    """下次跟进到期提醒"""
    from datetime import datetime, timedelta
    today = datetime.now().strftime('%Y-%m-%d')
    items = db.query(PsychologyRecord).filter(
        PsychologyRecord.next_follow_date != '',
        PsychologyRecord.next_follow_date <= today
    ).all()
    result = []
    for r in items:
        stu = db.query(Student).get(r.student_id)
        result.append({
            'id': r.id, 'student_name': stu.name if stu else '',
            'topic': r.topic, 'next_follow_date': r.next_follow_date,
        })
    return result



@router.get('/psychology/{record_id}')
def get_psychology(record_id: int, db: Session = Depends(get_db)):
    r = db.query(PsychologyRecord).get(record_id)
    if not r:
        raise HTTPException(404, '记录不存在')
    return _psy_dict(r, db)


@router.post('/psychology')
def create_psychology(data: dict, db: Session = Depends(get_db)):
    r = PsychologyRecord(**_psy_normalize_input(data))
    db.add(r)
    db.commit()
    db.refresh(r)
    return {'id': r.id}


@router.put('/psychology/{rid}')
def update_psychology(rid: int, data: dict, db: Session = Depends(get_db)):
    r = db.query(PsychologyRecord).get(rid)
    if not r:
        raise HTTPException(404, '记录不存在')
    for k, v in _psy_normalize_input(data).items():
        if hasattr(r, k):
            setattr(r, k, v)
    db.commit()
    return {'ok': True}


@router.delete('/psychology/{rid}')
def delete_psychology(rid: int, db: Session = Depends(get_db)):
    r = db.query(PsychologyRecord).get(rid)
    if r:
        db.delete(r)
        db.commit()
    return {'ok': True}


# ===== 家校沟通 =====
def _fam_dict(c, db):
    from models import ClassModel
    stu = db.query(Student).get(c.student_id)
    cls_name = ''
    if stu and stu.class_id:
        cls = db.query(ClassModel).get(stu.class_id)
        cls_name = cls.class_name if cls else ''
    # 从 parent_name '父亲XX' / '母亲XX' 抽出关系
    _rel = ''
    for k in ('父亲','母亲','监护人','祖父','祖母','外祖父','外祖母','兄弟','姐妹'):
        if c.parent_name and c.parent_name.startswith(k):
            _rel = k
            break
    return {
        'id': c.id, 'student_id': c.student_id,
        'student_name': stu.name if stu else '',
        'student_no': stu.student_no if stu else '',
        'class_name': cls_name,
        'contact_date': c.contact_date,
        'parent_name': c.parent_name, 'contact_name': c.parent_name,   # alias
        'contact_method': c.contact_method, 'contact_type': c.contact_method,  # alias
        'relationship': _rel,
        'topic': c.topic,
        'conclusion': c.conclusion, 'content': c.conclusion,   # alias
        'attachment': c.attachment,
    }


def _fam_normalize_input(data: dict) -> dict:
    d = dict(data)
    if 'contact_name' in d and 'parent_name' not in d:
        d['parent_name'] = d.pop('contact_name')
    if 'contact_type' in d and 'contact_method' not in d:
        d['contact_method'] = d.pop('contact_type')
    if 'content' in d and 'conclusion' not in d:
        d['conclusion'] = d.pop('content')
    # 如果传了 relationship 但 parent_name 没前缀，拼进去
    rel = d.pop('relationship', None)
    if rel and d.get('parent_name') and not any(d['parent_name'].startswith(k) for k in ('父亲','母亲','监护人','祖父','祖母','外祖父','外祖母','兄弟','姐妹')):
        d['parent_name'] = f"{rel}{d['parent_name']}"
    allowed = {'student_id','contact_date','parent_name','contact_method','topic','conclusion','attachment'}
    return {k: v for k, v in d.items() if k in allowed}


@router.get('/family-contacts')
def list_family_contacts(student_id: Optional[int] = None, contact_type: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FamilyContact)
    if student_id:
        q = q.filter(FamilyContact.student_id == student_id)
    if contact_type:
        q = q.filter(FamilyContact.contact_method == contact_type)
    items = q.order_by(FamilyContact.created_at.desc()).all()
    return [_fam_dict(c, db) for c in items]


@router.get('/family-contacts/{contact_id}')
def get_family_contact(contact_id: int, db: Session = Depends(get_db)):
    c = db.query(FamilyContact).get(contact_id)
    if not c:
        raise HTTPException(404, '记录不存在')
    return _fam_dict(c, db)


@router.post('/family-contacts')
def create_family_contact(data: dict, db: Session = Depends(get_db)):
    c = FamilyContact(**_fam_normalize_input(data))
    db.add(c)
    db.commit()
    db.refresh(c)
    return {'id': c.id}


@router.put('/family-contacts/{cid}')
def update_family_contact(cid: int, data: dict, db: Session = Depends(get_db)):
    c = db.query(FamilyContact).get(cid)
    if not c:
        raise HTTPException(404, '记录不存在')
    for k, v in _fam_normalize_input(data).items():
        if hasattr(c, k):
            setattr(c, k, v)
    db.commit()
    return {'ok': True}


@router.delete('/family-contacts/{cid}')
def delete_family_contact(cid: int, db: Session = Depends(get_db)):
    c = db.query(FamilyContact).get(cid)
    if c:
        db.delete(c)
        db.commit()
    return {'ok': True}
