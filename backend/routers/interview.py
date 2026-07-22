"""学生访谈管理 API"""
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session
from database import get_db
from models import Student, StudentInterview
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/interview', tags=['学生访谈'])


class InterviewCreate(BaseModel):
    student_id: int
    interview_date: str
    interview_type: str = '常规访谈'
    interviewer: str = ''
    location: str = ''
    topic: str = ''
    content: str = ''
    feedback: str = ''
    follow_up: str = ''
    status: str = '已完成'
    remind_date: str = ''


class InterviewUpdate(BaseModel):
    interview_date: Optional[str] = None
    interview_type: Optional[str] = None
    interviewer: Optional[str] = None
    location: Optional[str] = None
    topic: Optional[str] = None
    content: Optional[str] = None
    feedback: Optional[str] = None
    follow_up: Optional[str] = None
    status: Optional[str] = None
    remind_date: Optional[str] = None


@router.get('/')
def list_interviews(
    student_id: int = Query(None),
    status: str = Query(None),
    interview_type: str = Query(None),
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取访谈记录列表"""
    query = db.query(StudentInterview).join(Student)
    
    if student_id:
        query = query.filter(StudentInterview.student_id == student_id)
    if status:
        query = query.filter(StudentInterview.status == status)
    if interview_type:
        query = query.filter(StudentInterview.interview_type == interview_type)
    if keyword:
        query = query.filter(or_(
            Student.name.contains(keyword),
            Student.student_no.contains(keyword),
            StudentInterview.topic.contains(keyword),
            StudentInterview.content.contains(keyword)
        ))
    
    total = query.count()
    items = query.order_by(desc(StudentInterview.interview_date)).offset((page - 1) * size).limit(size).all()
    
    result = []
    for item in items:
        student = item.student
        result.append({
            'id': item.id,
            'student_id': item.student_id,
            'student_no': student.student_no,
            'student_name': student.name,
            'class_name': student.class_name,
            'interview_date': item.interview_date,
            'interview_type': item.interview_type,
            'interviewer': item.interviewer,
            'location': item.location,
            'topic': item.topic,
            'content': item.content,
            'feedback': item.feedback,
            'follow_up': item.follow_up,
            'status': item.status,
            'remind_date': item.remind_date,
            'created_at': item.created_at.isoformat() if item.created_at else None
        })
    
    return {'total': total, 'items': result}


@router.get('/types')
def get_types():
    """获取访谈类型列表"""
    return ['常规访谈', '预警访谈', '心理访谈', '学业访谈', '就业访谈', '其他']


@router.get('/chart-data')
def get_chart_data(db: Session = Depends(get_db)):
    """获取访谈图表数据：类型分布、月度趋势、TOP10学生"""
    # 1. 关注级别分布 - 按访谈类型统计
    type_rows = db.query(
        StudentInterview.interview_type,
        func.count(StudentInterview.id)
    ).group_by(StudentInterview.interview_type).all()
    type_distribution = {}
    for itype, count in type_rows:
        type_distribution[itype or '未知'] = count

    # 2. 月度趋势 - 最近12个月
    monthly_trend = []
    now = datetime.now()
    for i in range(11, -1, -1):
        m = now - relativedelta(months=i)
        month_str = m.strftime('%Y-%m')
        count = db.query(func.count(StudentInterview.id)).filter(
            func.substr(StudentInterview.interview_date, 1, 7) == month_str
        ).scalar()
        monthly_trend.append({'month': month_str, 'count': count})

    # 3. 访谈次数TOP10学生
    top_rows = db.query(
        StudentInterview.student_id,
        func.count(StudentInterview.id).label('cnt')
    ).group_by(StudentInterview.student_id).order_by(desc('cnt')).limit(10).all()

    top_students = []
    for student_id, count in top_rows:
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            top_students.append({
                'student_name': student.name,
                'student_no': student.student_no,
                'count': count
            })

    return {
        'type_distribution': type_distribution,
        'monthly_trend': monthly_trend,
        'top_students': top_students
    }


@router.get('/statistics')
def get_statistics(db: Session = Depends(get_db)):
    """获取访谈统计数据"""
    total = db.query(StudentInterview).count()
    by_status = {}
    by_type = {}
    
    # 按状态统计
    status_rows = db.query(StudentInterview.status, func.count(StudentInterview.id)).group_by(StudentInterview.status).all()
    for status, count in status_rows:
        by_status[status or '未知'] = count
    
    # 按类型统计
    type_rows = db.query(StudentInterview.interview_type, func.count(StudentInterview.id)).group_by(StudentInterview.interview_type).all()
    for itype, count in type_rows:
        by_type[itype or '未知'] = count
    
    # 待跟进数量
    pending = db.query(StudentInterview).filter(StudentInterview.status == '待进行').count()
    
    return {
        'total': total,
        'by_status': by_status,
        'by_type': by_type,
        'pending': pending
    }


@router.get('/{interview_id}')
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    """获取单条访谈记录"""
    item = db.query(StudentInterview).filter(StudentInterview.id == interview_id).first()
    if not item:
        raise HTTPException(404, '记录不存在')
    
    student = item.student
    return {
        'id': item.id,
        'student_id': item.student_id,
        'student_no': student.student_no,
        'student_name': student.name,
        'class_name': student.class_name,
        'interview_date': item.interview_date,
        'interview_type': item.interview_type,
        'interviewer': item.interviewer,
        'location': item.location,
        'topic': item.topic,
        'content': item.content,
        'feedback': item.feedback,
        'follow_up': item.follow_up,
        'status': item.status,
        'remind_date': item.remind_date,
        'created_at': item.created_at.isoformat() if item.created_at else None
    }


@router.post('/')
def create_interview(data: InterviewCreate, db: Session = Depends(get_db)):
    """创建访谈记录"""
    item = StudentInterview(
        student_id=data.student_id,
        interview_date=data.interview_date,
        interview_type=data.interview_type,
        interviewer=data.interviewer,
        location=data.location,
        topic=data.topic,
        content=data.content,
        feedback=data.feedback,
        follow_up=data.follow_up,
        status=data.status,
        remind_date=data.remind_date
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return {'id': item.id, 'message': '创建成功'}


@router.put('/{interview_id}')
def update_interview(interview_id: int, data: InterviewUpdate, db: Session = Depends(get_db)):
    """更新访谈记录"""
    item = db.query(StudentInterview).filter(StudentInterview.id == interview_id).first()
    if not item:
        raise HTTPException(404, '记录不存在')
    
    if data.interview_date is not None:
        item.interview_date = data.interview_date
    if data.interview_type is not None:
        item.interview_type = data.interview_type
    if data.interviewer is not None:
        item.interviewer = data.interviewer
    if data.location is not None:
        item.location = data.location
    if data.topic is not None:
        item.topic = data.topic
    if data.content is not None:
        item.content = data.content
    if data.feedback is not None:
        item.feedback = data.feedback
    if data.follow_up is not None:
        item.follow_up = data.follow_up
    if data.status is not None:
        item.status = data.status
    if data.remind_date is not None:
        item.remind_date = data.remind_date
    
    db.commit()
    
    return {'message': '更新成功'}


@router.delete('/{interview_id}')
def delete_interview(interview_id: int, db: Session = Depends(get_db)):
    """删除访谈记录"""
    item = db.query(StudentInterview).filter(StudentInterview.id == interview_id).first()
    if not item:
        raise HTTPException(404, '记录不存在')
    
    db.delete(item)
    db.commit()
    
    return {'message': '删除成功'}
