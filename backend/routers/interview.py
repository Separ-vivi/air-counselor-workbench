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


@router.get('/coverage')
def get_coverage(db: Session = Depends(get_db)):
    """获取访谈覆盖率数据：总学生数"""
    total_students = db.query(Student).count()
    covered_students = db.query(StudentInterview.student_id).distinct().count()
    coverage_rate = round((covered_students / total_students * 100), 1) if total_students > 0 else 0
    return {
        'total_students': total_students,
        'covered_students': covered_students,
        'coverage_rate': coverage_rate
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


# ===== V6.10: AI 摘要接口 =====

@router.post('/{interview_id}/ai-summary')
def ai_summary(interview_id: int, db: Session = Depends(get_db)):
    """V6.10: 调用 LLM 生成访谈 AI 摘要，结果缓存到数据库"""
    import json as _json

    item = db.query(StudentInterview).filter(StudentInterview.id == interview_id).first()
    if not item:
        raise HTTPException(404, '记录不存在')

    # 如果已有缓存，直接返回
    if item.ai_summary:
        try:
            cached = _json.loads(item.ai_summary)
            if isinstance(cached, dict) and cached.get('summary'):
                return {'cached': True, **cached}
        except Exception:
            pass

    # 拼接谈话内容
    content_parts = []
    if item.topic:
        content_parts.append(f'访谈主题：{item.topic}')
    if item.content:
        content_parts.append(f'访谈内容：{item.content}')
    if item.feedback:
        content_parts.append(f'学生反馈：{item.feedback}')
    if item.follow_up:
        content_parts.append(f'后续跟进：{item.follow_up}')

    talk_content = '\n'.join(content_parts) if content_parts else '（无内容）'

    # 调用 LLM
    try:
        from services.llm_adapter import LLMAdapter
        llm = LLMAdapter()
        if not llm.is_configured:
            return {'error': 'AI功能未配置', 'message': '请在系统设置中配置 LLM API Key'}

        student = item.student
        prompt = f"""你是一位高校辅导员工作助手。请分析以下辅导员与学生的谈心记录，提取关键信息。

学生姓名：{student.name if student else '未知'}
访谈类型：{item.interview_type}
访谈日期：{item.interview_date}

{talk_content}

请严格返回以下JSON格式（不要包含markdown代码块标记）：
{{
  "emotion": "学生情绪状态，从以下选择：平静/焦虑/低落/激动/积极/紧张/迷茫",
  "issue_type": "问题类型，从以下选择：学业/生活/心理/人际/就业/经济/家庭/其他",
  "follow_up": "后续跟进建议，一句话概括",
  "summary": "100字以内的谈话摘要"
}}"""

        messages = [
            {"role": "system", "content": "你是高校辅导员工作助手，擅长分析学生谈心记录。请始终返回有效的JSON格式。"},
            {"role": "user", "content": prompt}
        ]
        result_text = llm.chat(messages)

        # 清理可能的 markdown 代码块标记
        cleaned = result_text.strip()
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            # 去掉首行 ```json 和末行 ```
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            cleaned = '\n'.join(lines)

        parsed = _json.loads(cleaned)
        result = {
            'emotion': parsed.get('emotion', '未知'),
            'issue_type': parsed.get('issue_type', '其他'),
            'follow_up': parsed.get('follow_up', ''),
            'summary': parsed.get('summary', ''),
        }

        # 缓存到数据库
        item.ai_summary = _json.dumps(result, ensure_ascii=False)
        db.commit()

        return {'cached': False, **result}

    except _json.JSONDecodeError as e:
        logger.error(f"AI 摘要解析失败: {e}")
        return {'error': 'AI返回格式异常', 'message': '请重试'}
    except RuntimeError as e:
        logger.error(f"AI 摘要调用失败: {e}")
        return {'error': str(e)}
    except Exception as e:
        logger.error(f"AI 摘要未知错误: {e}")
        return {'error': f'AI摘要生成失败：{e}'}


# ===== V6.13: AI 谈心分析接口（原始文本 → 结构化数据） =====

class AiAnalyzeRequest(BaseModel):
    text: str

@router.post('/ai-analyze')
def ai_analyze_text(data: AiAnalyzeRequest, db: Session = Depends(get_db)):
    """V6.13: 接收访谈原始文本，AI 分析后返回结构化 JSON，用于自动填充表单"""
    import json as _json

    if not data.text or not data.text.strip():
        raise HTTPException(400, '请输入访谈内容')

    try:
        from services.llm_adapter import LLMAdapter
        llm = LLMAdapter()
        if not llm.is_configured:
            return {'error': True, 'message': '请在系统设置中配置 LLM API Key'}

        prompt = f"""你是一位高校辅导员工作助手。请分析以下辅导员与学生的谈心谈话原始记录，提取关键信息并填充到表单中。

以下是谈话原文：
---
{data.text.strip()}
---

请严格返回以下JSON格式（不要包含markdown代码块标记）：
{{
  "emotion": "学生情绪状态，从以下选择：平静/焦虑/低落/激动/积极/紧张/迷茫",
  "issue_type": "问题类型，从以下选择：学业/生活/心理/人际/就业/经济/家庭/其他",
  "topic": "谈话主题，简短概括（15字以内）",
  "content_summary": "谈话内容摘要（80字以内）",
  "key_info": "关键信息提取（学生表达的核心诉求或问题，60字以内）",
  "follow_up": "后续跟进建议（一句话，具体可操作）",
  "suggested_status": "建议状态，从以下选择：已完成/需跟进/待进行",
  "suggested_type": "建议访谈类型，从以下选择：常规访谈/预警访谈/心理访谈/学业访谈/就业访谈/其他",
  "risk_level": "风险等级，从以下选择：无/低/中/高"
}}"""

        messages = [
            {"role": "system", "content": "你是高校辅导员工作助手，擅长分析学生谈心谈话记录。请始终返回有效的JSON格式，不要包含任何多余文字。"},
            {"role": "user", "content": prompt}
        ]
        result_text = llm.chat(messages)

        # 清理 markdown 代码块标记
        cleaned = result_text.strip()
        if cleaned.startswith('```'):
            lines = cleaned.split('
')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            cleaned = '
'.join(lines)

        parsed = _json.loads(cleaned)
        return {
            'error': False,
            'emotion': parsed.get('emotion', '平静'),
            'issue_type': parsed.get('issue_type', '其他'),
            'topic': parsed.get('topic', ''),
            'content_summary': parsed.get('content_summary', ''),
            'key_info': parsed.get('key_info', ''),
            'follow_up': parsed.get('follow_up', ''),
            'suggested_status': parsed.get('suggested_status', '已完成'),
            'suggested_type': parsed.get('suggested_type', '常规访谈'),
            'risk_level': parsed.get('risk_level', '无')
        }

    except _json.JSONDecodeError as e:
        logger.error(f'AI 分析解析失败: {e}')
        return {'error': True, 'message': 'AI 返回格式异常，请重试'}
    except RuntimeError as e:
        logger.error(f'AI 分析调用失败: {e}')
        return {'error': True, 'message': str(e)}
    except Exception as e:
        logger.error(f'AI 分析未知错误: {e}')
        return {'error': True, 'message': f'AI 分析失败：{e}'}
