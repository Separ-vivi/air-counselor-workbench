"""V3-B 效率中心 · 记事本 + 倒计时 + 项目追踪
路由前缀 /api，与其他 modules 一致
"""
from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func
from database import get_db
from models import Note, Countdown, Project, ProjectStudent, Student, ClassModel

router = APIRouter(prefix='/api', tags=['V3-B 效率中心'])


# ========================================================================
# 记事本 Notes
# ========================================================================

def _note_dict(n: Note) -> dict:
    return {
        'id': n.id,
        'title': n.title or '',
        'content': n.content or '',
        'category': n.category or 'memo',
        'status': n.status or 'active',
        'priority': int(n.priority or 0),
        'due_date': n.due_date or '',
        'remind_at': (n.remind_at or '') if hasattr(n, 'remind_at') else '',
        'tags': n.tags or '',
        'pinned': bool(n.pinned),
        'color': n.color or 'yellow',
        'student_id': n.student_id,
        'class_id': n.class_id,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S') if n.created_at else '',
        'updated_at': n.updated_at.strftime('%Y-%m-%d %H:%M:%S') if n.updated_at else '',
    }


@router.get('/notes')
def list_notes(
    category: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Note)
    if category:
        q = q.filter(Note.category == category)
    if status:
        q = q.filter(Note.status == status)
    if keyword:
        k = f'%{keyword}%'
        q = q.filter(or_(Note.title.like(k), Note.content.like(k), Note.tags.like(k)))
    # 置顶优先 → 优先级降序 → 更新时间倒序
    q = q.order_by(desc(Note.pinned), desc(Note.priority), desc(Note.updated_at))
    return [_note_dict(n) for n in q.all()]


@router.get('/notes/{nid}')
def get_note(nid: int, db: Session = Depends(get_db)):
    n = db.query(Note).get(nid)
    if not n:
        raise HTTPException(404, '记事不存在')
    return _note_dict(n)


@router.post('/notes')
def create_note(payload: dict, db: Session = Depends(get_db)):
    n = Note(
        title=payload.get('title', '') or '未命名',
        content=payload.get('content', '') or '',
        category=payload.get('category', 'memo'),
        status=payload.get('status', 'active'),
        priority=int(payload.get('priority', 0) or 0),
        due_date=payload.get('due_date', '') or '',
        remind_at=payload.get('remind_at', '') or '',
        tags=payload.get('tags', '') or '',
        pinned=bool(payload.get('pinned', False)),
        color=payload.get('color', 'yellow') or 'yellow',
        student_id=payload.get('student_id'),
        class_id=payload.get('class_id'),
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return _note_dict(n)


@router.put('/notes/{nid}')
def update_note(nid: int, payload: dict, db: Session = Depends(get_db)):
    n = db.query(Note).get(nid)
    if not n:
        raise HTTPException(404, '记事不存在')
    for k in ['title', 'content', 'category', 'status', 'due_date', 'remind_at', 'tags', 'color']:
        if k in payload:
            setattr(n, k, payload.get(k) or '')
    if 'priority' in payload:
        n.priority = int(payload.get('priority', 0) or 0)
    if 'pinned' in payload:
        n.pinned = bool(payload.get('pinned', False))
    if 'student_id' in payload:
        n.student_id = payload.get('student_id')
    if 'class_id' in payload:
        n.class_id = payload.get('class_id')
    db.commit()
    db.refresh(n)
    return _note_dict(n)


@router.post('/notes/{nid}/toggle')
def toggle_note_status(nid: int, db: Session = Depends(get_db)):
    """一键切换 todo 状态 active ↔ done"""
    n = db.query(Note).get(nid)
    if not n:
        raise HTTPException(404, '记事不存在')
    n.status = 'active' if n.status == 'done' else 'done'
    db.commit()
    return {'ok': True, 'status': n.status}


@router.delete('/notes/{nid}')
def delete_note(nid: int, db: Session = Depends(get_db)):
    n = db.query(Note).get(nid)
    if not n:
        raise HTTPException(404, '记事不存在')
    db.delete(n)
    db.commit()
    return {'ok': True}


# ========================================================================
# 倒计时 Countdowns
# ========================================================================

def _cd_dict(c: Countdown) -> dict:
    days_left = None
    try:
        if c.target_date:
            td = datetime.strptime(c.target_date, '%Y-%m-%d').date()
            days_left = (td - date.today()).days
    except Exception:
        days_left = None
    return {
        'id': c.id,
        'title': c.title or '',
        'target_date': c.target_date or '',
        'category': c.category or 'general',
        'color': c.color or 'blue',
        'description': c.description or '',
        'pinned': bool(c.pinned),
        'days_left': days_left,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S') if c.created_at else '',
    }


@router.get('/countdowns')
def list_countdowns(
    category: Optional[str] = None,
    include_past: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(Countdown)
    if category:
        q = q.filter(Countdown.category == category)
    if not include_past:
        today_str = date.today().strftime('%Y-%m-%d')
        q = q.filter(Countdown.target_date >= today_str)
    q = q.order_by(desc(Countdown.pinned), Countdown.target_date.asc())
    return [_cd_dict(c) for c in q.all()]


@router.post('/countdowns')
def create_countdown(payload: dict, db: Session = Depends(get_db)):
    if not payload.get('title') or not payload.get('target_date'):
        raise HTTPException(400, '标题和目标日期不能为空')
    c = Countdown(
        title=payload.get('title'),
        target_date=payload.get('target_date'),
        category=payload.get('category', 'general'),
        color=payload.get('color', 'blue') or 'blue',
        description=payload.get('description', '') or '',
        pinned=bool(payload.get('pinned', False)),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _cd_dict(c)


@router.put('/countdowns/{cid}')
def update_countdown(cid: int, payload: dict, db: Session = Depends(get_db)):
    c = db.query(Countdown).get(cid)
    if not c:
        raise HTTPException(404, '倒计时不存在')
    for k in ['title', 'target_date', 'category', 'color', 'description']:
        if k in payload:
            setattr(c, k, payload.get(k) or '')
    if 'pinned' in payload:
        c.pinned = bool(payload.get('pinned', False))
    db.commit()
    db.refresh(c)
    return _cd_dict(c)


@router.delete('/countdowns/{cid}')
def delete_countdown(cid: int, db: Session = Depends(get_db)):
    c = db.query(Countdown).get(cid)
    if not c:
        raise HTTPException(404, '倒计时不存在')
    db.delete(c)
    db.commit()
    return {'ok': True}


# ========================================================================
# 项目追踪 Projects
# ========================================================================

def _project_dict(p: Project, db: Optional[Session] = None) -> dict:
    student_count = 0
    if db is not None:
        student_count = db.query(ProjectStudent).filter(ProjectStudent.project_id == p.id).count()
    return {
        'id': p.id,
        'name': p.name or '',
        'start_date': p.start_date or '',
        'end_date': p.end_date or '',
        'status': p.status or 'active',
        'progress': int(p.progress or 0),
        'description': p.description or '',
        'student_count': student_count,
        'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else '',
    }


@router.get('/projects')
def list_projects(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Project)
    if status:
        q = q.filter(Project.status == status)
    if keyword:
        q = q.filter(Project.name.like(f'%{keyword}%'))
    q = q.order_by(desc(Project.created_at))
    return [_project_dict(p, db) for p in q.all()]


@router.get('/projects/{pid}')
def get_project(pid: int, db: Session = Depends(get_db)):
    p = db.query(Project).get(pid)
    if not p:
        raise HTTPException(404, '项目不存在')
    d = _project_dict(p, db)
    # 附学生列表
    members = []
    for ps in db.query(ProjectStudent).filter(ProjectStudent.project_id == pid).all():
        s = db.query(Student).get(ps.student_id)
        cls = db.query(ClassModel).get(s.class_id) if s and s.class_id else None
        members.append({
            'ps_id': ps.id,
            'student_id': ps.student_id,
            'student_name': s.name if s else '(已删除)',
            'student_no': s.student_no if s else '',
            'class_name': cls.class_name if cls else '',
            'progress': int(ps.progress or 0),
            'material_status': ps.material_status or 'pending',
            'notes': ps.notes or '',
        })
    d['members'] = members
    return d


@router.post('/projects')
def create_project(payload: dict, db: Session = Depends(get_db)):
    if not payload.get('name'):
        raise HTTPException(400, '项目名称不能为空')
    p = Project(
        name=payload.get('name'),
        start_date=payload.get('start_date', '') or '',
        end_date=payload.get('end_date', '') or '',
        status=payload.get('status', 'active'),
        progress=int(payload.get('progress', 0) or 0),
        description=payload.get('description', '') or '',
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _project_dict(p, db)


@router.put('/projects/{pid}')
def update_project(pid: int, payload: dict, db: Session = Depends(get_db)):
    p = db.query(Project).get(pid)
    if not p:
        raise HTTPException(404, '项目不存在')
    for k in ['name', 'start_date', 'end_date', 'status', 'description']:
        if k in payload:
            setattr(p, k, payload.get(k) or '')
    if 'progress' in payload:
        p.progress = int(payload.get('progress', 0) or 0)
    db.commit()
    db.refresh(p)
    return _project_dict(p, db)


@router.delete('/projects/{pid}')
def delete_project(pid: int, db: Session = Depends(get_db)):
    p = db.query(Project).get(pid)
    if not p:
        raise HTTPException(404, '项目不存在')
    db.delete(p)
    db.commit()
    return {'ok': True}


@router.post('/projects/{pid}/members')
def add_project_member(pid: int, payload: dict, db: Session = Depends(get_db)):
    """给项目追加学生"""
    if not db.query(Project).get(pid):
        raise HTTPException(404, '项目不存在')
    sid = payload.get('student_id')
    if not sid:
        raise HTTPException(400, '学生 ID 不能为空')
    # 去重
    exist = db.query(ProjectStudent).filter(
        ProjectStudent.project_id == pid, ProjectStudent.student_id == sid
    ).first()
    if exist:
        return {'ok': True, 'ps_id': exist.id, 'note': '已存在'}
    ps = ProjectStudent(
        project_id=pid,
        student_id=sid,
        progress=int(payload.get('progress', 0) or 0),
        material_status=payload.get('material_status', 'pending'),
        notes=payload.get('notes', '') or '',
    )
    db.add(ps)
    db.commit()
    db.refresh(ps)
    return {'ok': True, 'ps_id': ps.id}


@router.put('/projects/{pid}/members/{ps_id}')
def update_project_member(pid: int, ps_id: int, payload: dict, db: Session = Depends(get_db)):
    ps = db.query(ProjectStudent).get(ps_id)
    if not ps or ps.project_id != pid:
        raise HTTPException(404, '成员不存在')
    if 'progress' in payload:
        ps.progress = int(payload.get('progress', 0) or 0)
    if 'material_status' in payload:
        ps.material_status = payload.get('material_status', 'pending')
    if 'notes' in payload:
        ps.notes = payload.get('notes', '') or ''
    db.commit()
    return {'ok': True}


@router.delete('/projects/{pid}/members/{ps_id}')
def delete_project_member(pid: int, ps_id: int, db: Session = Depends(get_db)):
    ps = db.query(ProjectStudent).get(ps_id)
    if not ps or ps.project_id != pid:
        raise HTTPException(404, '成员不存在')
    db.delete(ps)
    db.commit()
    return {'ok': True}


# ========================================================================
# 效率中心汇总（驾驶舱用）
# ========================================================================

@router.get('/productivity/dashboard')
def productivity_dashboard(db: Session = Depends(get_db)):
    """给驾驶舱用的效率中心快照"""
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    week_later = (today + timedelta(days=7)).strftime('%Y-%m-%d')

    # 待办
    todo_active = db.query(Note).filter(
        Note.category == 'todo', Note.status == 'active'
    ).count()
    todo_urgent = db.query(Note).filter(
        Note.category == 'todo', Note.status == 'active',
        Note.due_date >= today_str, Note.due_date <= week_later,
    ).count()

    # 倒计时 top 3
    cds = db.query(Countdown).filter(
        Countdown.target_date >= today_str
    ).order_by(Countdown.target_date.asc()).limit(3).all()

    # 活跃项目
    projects_active = db.query(Project).filter(Project.status == 'active').count()

    return {
        'todo_active': todo_active,
        'todo_urgent_week': todo_urgent,
        'countdowns_top': [_cd_dict(c) for c in cds],
        'projects_active': projects_active,
    }


# ========================================================================
# v3h · /events 聚合接口 & 本周待办中心
# ========================================================================

def _to_dt(s):
    """把 YYYY-MM-DD[ HH:MM] 转成可比较的字符串（保留 10 位日期即可）"""
    return (s or '')[:10]


@router.get('/events')
def list_events(start: str = '', end: str = '', db: Session = Depends(get_db)):
    """v3h · 统一事件聚合：校历/todo/memo提醒/项目节点/活动/班会/家校
    query: start/end (YYYY-MM-DD)；不传则默认前后各 30 天。
    返回按日期分组的事件列表，每项含 { id, date, type, color, title, meta, link }
    """
    from models import (
        Activity, ClassMeeting, FamilyContact, Project
    )
    today = date.today()
    start = start or (today - timedelta(days=30)).strftime('%Y-%m-%d')
    end = end or (today + timedelta(days=60)).strftime('%Y-%m-%d')

    def _in(d):
        d = _to_dt(d)
        return d and start <= d <= end

    events = []

    # 1) 校历倒计时（countdowns 表）
    for c in db.query(Countdown).all():
        if _in(c.target_date):
            events.append({
                'id': f'cd-{c.id}',
                'date': _to_dt(c.target_date),
                'type': 'countdown',
                'color': c.color or 'blue',
                'title': c.title,
                'meta': c.category or 'general',
                'description': c.description or '',
                'link': '/calendar',
            })

    # 2) 待办 Todo（notes.category='todo' 且有 due_date）
    for n in db.query(Note).filter(Note.category == 'todo').all():
        if _in(n.due_date):
            events.append({
                'id': f'todo-{n.id}',
                'date': _to_dt(n.due_date),
                'type': 'todo',
                'color': 'orange',
                'title': n.title,
                'meta': '待办' + (' · 已完成' if n.status == 'done' else ''),
                'description': (n.content or '')[:100],
                'link': '/notes',
                'done': n.status == 'done',
            })

    # 3) 备忘录提醒（notes.remind_at）
    for n in db.query(Note).all():
        r = getattr(n, 'remind_at', '') or ''
        if r and _in(r):
            events.append({
                'id': f'memo-{n.id}',
                'date': _to_dt(r),
                'type': 'memo',
                'color': n.color or 'yellow',
                'title': n.title,
                'meta': '记事本提醒',
                'description': (n.content or '')[:100],
                'link': '/notes',
            })

    # 4) 项目关键节点（start_date / end_date）
    for pr in db.query(Project).all():
        if _in(pr.start_date):
            events.append({
                'id': f'proj-s-{pr.id}',
                'date': _to_dt(pr.start_date),
                'type': 'project',
                'color': 'purple',
                'title': f'📌 {pr.name} · 启动',
                'meta': '项目节点',
                'description': (pr.description or '')[:100],
                'link': f'/projects',
            })
        if _in(pr.end_date):
            events.append({
                'id': f'proj-e-{pr.id}',
                'date': _to_dt(pr.end_date),
                'type': 'project',
                'color': 'purple',
                'title': f'🏁 {pr.name} · 收尾',
                'meta': '项目节点',
                'description': (pr.description or '')[:100],
                'link': f'/projects',
            })

    # 5) 活动
    for a in db.query(Activity).all():
        if _in(a.activity_date):
            events.append({
                'id': f'act-{a.id}',
                'date': _to_dt(a.activity_date),
                'type': 'activity',
                'color': 'pink',
                'title': f'🎨 {a.title or "活动"}',
                'meta': (a.activity_type or '活动') + (f' · 📍{a.location}' if getattr(a, 'location', '') else ''),
                'description': (getattr(a, 'description', '') or '')[:100],
                'link': '/module/activities',
            })

    # 6) 班会
    for m in db.query(ClassMeeting).all():
        if _in(m.meeting_date):
            events.append({
                'id': f'mt-{m.id}',
                'date': _to_dt(m.meeting_date),
                'type': 'meeting',
                'color': 'green',
                'title': f'📢 班会 · {m.topic or "常规班会"}',
                'meta': f'出席 {m.attendance_count or 0} 人',
                'description': (m.resolution or '')[:100],
                'link': '/module/meetings',
            })

    # 7) 家校沟通
    for f in db.query(FamilyContact).all():
        if _in(f.contact_date):
            events.append({
                'id': f'fc-{f.id}',
                'date': _to_dt(f.contact_date),
                'type': 'family',
                'color': 'cyan',
                'title': f'📞 家校 · {f.topic or "常规沟通"}',
                'meta': (f.contact_method or '电话') + (f' · {f.parent_name}' if f.parent_name else ''),
                'description': (getattr(f, 'notes', '') or '')[:100],
                'link': '/module/family',
            })

    events.sort(key=lambda x: (x['date'], x['type']))
    return {'events': events, 'start': start, 'end': end, 'count': len(events)}


@router.get('/events/week')
def list_week_events(offset: int = 0, db: Session = Depends(get_db)):
    """v3h · 本周（Mon-Sun）事件聚合，供 Dashboard 本周待办中心用
    offset: 0=本周，-1=上周，1=下周
    """
    today = date.today() + timedelta(weeks=offset)
    ws = today - timedelta(days=today.weekday())
    we = ws + timedelta(days=6)
    return list_events(start=ws.strftime('%Y-%m-%d'), end=we.strftime('%Y-%m-%d'), db=db)
