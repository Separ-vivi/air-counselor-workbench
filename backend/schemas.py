"""Pydantic 请求/响应模型"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ============ 标签 ============
class TagCreate(BaseModel):
    name: str
    group_name: str
    color: str = '#409EFF'

class TagUpdate(BaseModel):
    name: Optional[str] = None
    group_name: Optional[str] = None
    color: Optional[str] = None

class TagOut(BaseModel):
    id: int
    name: str
    group_name: str
    color: str
    student_count: int = 0

    class Config:
        from_attributes = True


# ============ 学生 ============
class StudentCreate(BaseModel):
    student_no: str
    name: str
    gender: str = ''
    major: str = ''
    class_name: str = ''
    class_id: Optional[int] = None
    birth_date: str = ''
    political_status: str = ''
    family_situation: str = ''
    phone: str = ''
    email: str = ''
    parent_phone: str = ''
    birth_source: str = ''
    id_card: str = ''
    campus: str = ''
    dorm_building: str = ''
    dorm_room: str = ''
    is_off_campus: bool = False
    off_campus_address: str = ''
    notes: str = ''
    tag_ids: List[int] = []

class StudentUpdate(BaseModel):
    student_no: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    major: Optional[str] = None
    class_name: Optional[str] = None
    class_id: Optional[int] = None
    birth_date: Optional[str] = None
    political_status: Optional[str] = None
    family_situation: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    parent_phone: Optional[str] = None
    birth_source: Optional[str] = None
    id_card: Optional[str] = None
    campus: Optional[str] = None
    dorm_building: Optional[str] = None
    dorm_room: Optional[str] = None
    is_off_campus: Optional[bool] = None
    off_campus_address: Optional[str] = None
    notes: Optional[str] = None
    tag_ids: Optional[List[int]] = None

class StudentBase(BaseModel):
    id: int
    student_no: str
    name: str
    gender: str = ''
    major: str = ''
    class_name: str = ''
    birth_date: str = ''
    political_status: str = ''
    family_situation: str = ''
    phone: str = ''
    email: str = ''
    notes: str = ''
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StudentOut(StudentBase):
    tags: List[TagOut] = []
    warning_count: int = 0
    avg_gpa: Optional[float] = None

class StudentDetail(StudentBase):
    tags: List[TagOut] = []
    grades: list = []
    warnings: list = []


# ============ 成绩 ============
class GradeOut(BaseModel):
    id: int
    student_id: int
    semester: str
    course_name: str
    score: Optional[float] = None
    gpa: Optional[float] = None
    credit: Optional[float] = None

    class Config:
        from_attributes = True


# ============ 预警 ============
class WarningOut(BaseModel):
    id: int
    student_id: int
    warning_type: str
    description: str
    semester: str
    student_name: str = ''
    student_no: str = ''
    class_name: str = ''

    class Config:
        from_attributes = True


# ============ 设置 ============
class SettingsOut(BaseModel):
    fail_course_threshold: int = 2      # 挂科 >= N 门 = 红灯
    gpa_drop_threshold: float = 0.5     # 绩点下降 >= N = 黄灯

class SettingsUpdate(BaseModel):
    fail_course_threshold: Optional[int] = None
    gpa_drop_threshold: Optional[float] = None


# ============ 驾驶舱 ============
class DashboardData(BaseModel):
    total_students: int = 0
    total_classes: int = 0
    total_majors: int = 0
    red_warning_count: int = 0
    yellow_warning_count: int = 0
    class_distribution: List[dict] = []
    tag_distribution: List[dict] = []
    recent_students: List[dict] = []
    major_distribution: List[dict] = []
