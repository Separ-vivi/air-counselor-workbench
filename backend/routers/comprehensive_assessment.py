"""综测成绩管理 API"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from database import get_db
from models import Student, ClassModel, ComprehensiveAssessment
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/comprehensive', tags=['综测成绩'])


class AssessmentCreate(BaseModel):
    student_id: int
    semester: str
    moral_score: float = 0
    academic_score: float = 0
    physical_score: float = 0
    aesthetic_score: float = 0
    labor_score: float = 0
    notes: str = ''


class AssessmentUpdate(BaseModel):
    moral_score: Optional[float] = None
    academic_score: Optional[float] = None
    physical_score: Optional[float] = None
    aesthetic_score: Optional[float] = None
    labor_score: Optional[float] = None
    notes: Optional[str] = None


@router.get('/')
def list_assessments(
    semester: str = Query(None),
    class_id: int = Query(None),
    student_id: int = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取综测成绩列表"""
    query = db.query(ComprehensiveAssessment).join(Student)
    
    if semester:
        query = query.filter(ComprehensiveAssessment.semester == semester)
    if class_id:
        query = query.filter(Student.class_id == class_id)
    if student_id:
        query = query.filter(ComprehensiveAssessment.student_id == student_id)
    
    total = query.count()
    items = query.order_by(desc(ComprehensiveAssessment.total_score)).offset((page - 1) * size).limit(size).all()
    
    result = []
    for item in items:
        student = item.student
        result.append({
            'id': item.id,
            'student_id': item.student_id,
            'student_no': student.student_no,
            'student_name': student.name,
            'class_name': student.class_name,
            'semester': item.semester,
            'moral_score': item.moral_score,
            'academic_score': item.academic_score,
            'physical_score': item.physical_score,
            'aesthetic_score': item.aesthetic_score,
            'labor_score': item.labor_score,
            'total_score': item.total_score,
            'class_rank': item.class_rank,
            'notes': item.notes,
            'created_at': item.created_at.isoformat() if item.created_at else None
        })
    
    return {'total': total, 'items': result}


@router.get('/semesters')
def list_semesters(db: Session = Depends(get_db)):
    """获取已有学期列表"""
    semesters = db.query(ComprehensiveAssessment.semester).distinct().all()
    return sorted([s[0] for s in semesters if s[0]], reverse=True)


@router.get('/statistics')
def get_statistics(
    semester: str = Query(None),
    class_id: int = Query(None),
    db: Session = Depends(get_db)
):
    """获取综测统计数据"""
    query = db.query(ComprehensiveAssessment).join(Student)
    
    if semester:
        query = query.filter(ComprehensiveAssessment.semester == semester)
    if class_id:
        query = query.filter(Student.class_id == class_id)
    
    records = query.all()
    
    if not records:
        return {
            'count': 0,
            'avg_total': 0,
            'avg_moral': 0,
            'avg_academic': 0,
            'avg_physical': 0,
            'avg_aesthetic': 0,
            'avg_labor': 0,
            'top_score': 0,
            'min_score': 0
        }
    
    scores = [r.total_score for r in records]
    moral_scores = [r.moral_score for r in records]
    academic_scores = [r.academic_score for r in records]
    physical_scores = [r.physical_score for r in records]
    aesthetic_scores = [r.aesthetic_score for r in records]
    labor_scores = [r.labor_score for r in records]
    
    return {
        'count': len(records),
        'avg_total': round(sum(scores) / len(scores), 2),
        'avg_moral': round(sum(moral_scores) / len(moral_scores), 2),
        'avg_academic': round(sum(academic_scores) / len(academic_scores), 2),
        'avg_physical': round(sum(physical_scores) / len(physical_scores), 2),
        'avg_aesthetic': round(sum(aesthetic_scores) / len(aesthetic_scores), 2),
        'avg_labor': round(sum(labor_scores) / len(labor_scores), 2),
        'top_score': max(scores),
        'min_score': min(scores)
    }


@router.get('/{assessment_id}')
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """获取单条综测记录"""
    item = db.query(ComprehensiveAssessment).filter(ComprehensiveAssessment.id == assessment_id).first()
    if not item:
        raise HTTPException(404, '记录不存在')
    
    student = item.student
    return {
        'id': item.id,
        'student_id': item.student_id,
        'student_no': student.student_no,
        'student_name': student.name,
        'class_name': student.class_name,
        'semester': item.semester,
        'moral_score': item.moral_score,
        'academic_score': item.academic_score,
        'physical_score': item.physical_score,
        'aesthetic_score': item.aesthetic_score,
        'labor_score': item.labor_score,
        'total_score': item.total_score,
        'class_rank': item.class_rank,
        'notes': item.notes,
        'created_at': item.created_at.isoformat() if item.created_at else None
    }


@router.post('/')
def create_assessment(data: AssessmentCreate, db: Session = Depends(get_db)):
    """创建综测记录"""
    # 计算总分（默认等权重）
    total = (data.moral_score + data.academic_score + data.physical_score + 
             data.aesthetic_score + data.labor_score) / 5
    
    item = ComprehensiveAssessment(
        student_id=data.student_id,
        semester=data.semester,
        moral_score=data.moral_score,
        academic_score=data.academic_score,
        physical_score=data.physical_score,
        aesthetic_score=data.aesthetic_score,
        labor_score=data.labor_score,
        total_score=round(total, 2),
        notes=data.notes
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # 更新班级排名
    _update_class_rank(db, item.student_id, item.semester)
    
    return {'id': item.id, 'message': '创建成功'}


@router.put('/{assessment_id}')
def update_assessment(assessment_id: int, data: AssessmentUpdate, db: Session = Depends(get_db)):
    """更新综测记录"""
    item = db.query(ComprehensiveAssessment).filter(ComprehensiveAssessment.id == assessment_id).first()
    if not item:
        raise HTTPException(404, '记录不存在')
    
    if data.moral_score is not None:
        item.moral_score = data.moral_score
    if data.academic_score is not None:
        item.academic_score = data.academic_score
    if data.physical_score is not None:
        item.physical_score = data.physical_score
    if data.aesthetic_score is not None:
        item.aesthetic_score = data.aesthetic_score
    if data.labor_score is not None:
        item.labor_score = data.labor_score
    if data.notes is not None:
        item.notes = data.notes
    
    # 重新计算总分
    item.total_score = round((item.moral_score + item.academic_score + item.physical_score + 
                              item.aesthetic_score + item.labor_score) / 5, 2)
    
    db.commit()
    
    # 更新班级排名
    _update_class_rank(db, item.student_id, item.semester)
    
    return {'message': '更新成功'}


@router.delete('/{assessment_id}')
def delete_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """删除综测记录"""
    item = db.query(ComprehensiveAssessment).filter(ComprehensiveAssessment.id == assessment_id).first()
    if not item:
        raise HTTPException(404, '记录不存在')
    
    student_id = item.student_id
    semester = item.semester
    
    db.delete(item)
    db.commit()
    
    # 更新班级排名
    _update_class_rank(db, student_id, semester)
    
    return {'message': '删除成功'}


def _update_class_rank(db: Session, student_id: int, semester: str):
    """更新班级排名"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student or not student.class_id:
        return
    
    # 获取同班级同学期的所有记录
    records = db.query(ComprehensiveAssessment).join(Student).filter(
        Student.class_id == student.class_id,
        ComprehensiveAssessment.semester == semester
    ).order_by(desc(ComprehensiveAssessment.total_score)).all()
    
    for rank, record in enumerate(records, 1):
        record.class_rank = rank
    
    db.commit()
