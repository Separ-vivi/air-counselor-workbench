"""系统设置路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import (
    Setting, Student, GradeRecord, WarningRecord, Tag,
    PartyProgress, PsychologyRecord, FamilyContact,
    StudentCadreRecord, ClassTeacher, EmploymentRecord,
    Activity, ActivitySignup, PartyStudy, ClassMeeting,
    KnowledgeDoc, FAQ, WeeklySummary, DocumentTemplate, GeneratedDocument,
)
from schemas import SettingsUpdate

router = APIRouter(prefix='/api/settings', tags=['系统设置'])


@router.get('')
def get_settings(db: Session = Depends(get_db)):
    """获取预警阈值设置"""
    settings = {s.key: s.value for s in db.query(Setting).all()}
    return {
        'fail_course_threshold': int(settings.get('fail_course_threshold', '2')),
        'gpa_drop_threshold': float(settings.get('gpa_drop_threshold', '0.5')),
    }


@router.put('')
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    """更新预警阈值设置"""
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            db.add(Setting(key=key, value=str(value)))
    db.commit()
    return {'message': '设置已保存'}


@router.delete('/reset')
def reset_data(db: Session = Depends(get_db)):
    """清空所有业务数据（保留设置和文书模板）"""
    # V2 模块表（先删依赖表）
    db.query(GeneratedDocument).delete()
    db.query(ActivitySignup).delete()
    db.query(PartyProgress).delete()
    db.query(PsychologyRecord).delete()
    db.query(FamilyContact).delete()
    db.query(StudentCadreRecord).delete()
    db.query(ClassTeacher).delete()
    db.query(EmploymentRecord).delete()
    db.query(Activity).delete()
    db.query(PartyStudy).delete()
    db.query(ClassMeeting).delete()
    db.query(KnowledgeDoc).delete()
    db.query(FAQ).delete()
    db.query(WeeklySummary).delete()
    # V1 核心表
    db.query(WarningRecord).delete()
    db.query(GradeRecord).delete()
    # 清除学生-标签关联
    db.execute(text("DELETE FROM student_tags"))
    db.query(Student).delete()
    db.query(Tag).delete()
    db.commit()
    return {'message': '所有业务数据已清空（设置和模板保留）'}
