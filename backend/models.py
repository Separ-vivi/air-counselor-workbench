"""SQLAlchemy 数据模型定义 - V3-A 架构重构
核心原则：学生=原子单位，班级=二级聚合，禁止冗余字段，单一数据源
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Date, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# ===== 关联表 =====

student_tags = Table(
    'student_tags', Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

party_study_students = Table(
    'party_study_students', Base.metadata,
    Column('study_id', Integer, ForeignKey('party_study.id', ondelete='CASCADE'), primary_key=True),
    Column('student_id', Integer, ForeignKey('students.id', ondelete='CASCADE'), primary_key=True)
)

# ===== 三级组织架构 =====

class Grade(Base):
    """年级"""
    __tablename__ = 'grades_org'
    id = Column(Integer, primary_key=True, index=True)
    grade_name = Column(String(50), nullable=False)  # e.g. "2024级"
    start_year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    majors = relationship('Major', back_populates='grade', cascade='all, delete-orphan')


class Major(Base):
    """专业"""
    __tablename__ = 'majors'
    id = Column(Integer, primary_key=True, index=True)
    major_name = Column(String(100), nullable=False)
    grade_id = Column(Integer, ForeignKey('grades_org.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    grade = relationship('Grade', back_populates='majors')
    classes = relationship('ClassModel', back_populates='major', cascade='all, delete-orphan')


class ClassModel(Base):
    """班级"""
    __tablename__ = 'classes'
    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(100), nullable=False, unique=True)
    major_id = Column(Integer, ForeignKey('majors.id', ondelete='CASCADE'), nullable=False)
    class_teacher = Column(String(100), default='')  # 班主任姓名
    monitor = Column(String(100), default='')  # 班长姓名
    league_secretary = Column(String(100), default='')  # 团支书姓名
    # v3j-D · D3: 班级档案
    slogan = Column(String(200), default='')  # 班级口号
    features = Column(Text, default='')  # 班级特色（自由文本，多条用换行）
    office_location = Column(String(200), default='')  # 办公地点
    created_at = Column(DateTime, default=datetime.now)
    major = relationship('Major', back_populates='classes')
    students = relationship('Student', back_populates='class_obj')


# ===== 核心：学生主表 =====

class Student(Base):
    """学生主表 - 单一数据源"""
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, index=True)
    student_no = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    pinyin_initial = Column(String(10), default='', index=True)  # 拼音首字母，用于搜索
    gender = Column(String(10), default='')
    class_id = Column(Integer, ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    birth_date = Column(String(20), default='')
    political_status = Column(String(50), default='')
    join_league_date = Column(String(20), default='')  # 入团时间（团员及以上）
    join_party_date = Column(String(20), default='')  # 入党时间（正式党员/预备党员）
    phone = Column(String(50), default='')
    email = Column(String(100), default='')
    parent_phone = Column(String(50), default='')
    birth_source = Column(String(150), default='')  # 生源地：省·市·县
    id_card = Column(String(30), default='', index=True)  # 身份证号
    # 宿舍信息
    campus = Column(String(50), default='')  # 校区（铜盘/旗山/其他）
    dorm_building = Column(String(50), default='')  # 宿舍楼
    dorm_room = Column(String(50), default='')  # 房间号
    is_off_campus = Column(Boolean, default=False)  # 是否外宿
    off_campus_address = Column(String(200), default='')  # 外宿地址（选填）
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 组织架构关系
    class_obj = relationship('ClassModel', back_populates='students')

    # 标签
    tags = relationship('Tag', secondary=student_tags, back_populates='students', lazy='dynamic')

    # 业务关系 (12类)
    grade_records = relationship('GradeRecord', back_populates='student', cascade='all, delete-orphan')
    warnings = relationship('WarningRecord', back_populates='student', cascade='all, delete-orphan')
    party_progress = relationship('PartyProgress', back_populates='student', cascade='all, delete-orphan')
    psychology_records = relationship('PsychologyRecord', back_populates='student', cascade='all, delete-orphan')
    family_contacts = relationship('FamilyContact', back_populates='student', cascade='all, delete-orphan')
    employment_records = relationship('EmploymentRecord', back_populates='student', cascade='all, delete-orphan')
    cadre_records = relationship('StudentCadreRecord', back_populates='student', cascade='all, delete-orphan')
    activity_signups = relationship('ActivitySignup', back_populates='student', cascade='all, delete-orphan')

    # V3-A 新增业务关系
    hardship_records = relationship('StudentHardship', back_populates='student', cascade='all, delete-orphan')
    grant_records = relationship('StudentGrant', back_populates='student', cascade='all, delete-orphan')
    scholarship_records = relationship('StudentScholarship', back_populates='student', cascade='all, delete-orphan')
    loan_records = relationship('StudentLoan', back_populates='student', cascade='all, delete-orphan')
    work_study_records = relationship('StudentWorkStudy', back_populates='student', cascade='all, delete-orphan')
    honor_records = relationship('StudentHonor', back_populates='student', cascade='all, delete-orphan')
    dorm_visits = relationship('StudentDormVisit', back_populates='student', cascade='all, delete-orphan')
    leave_records = relationship('StudentLeave', back_populates='student', cascade='all, delete-orphan')
    discipline_records = relationship('StudentDiscipline', back_populates='student', cascade='all, delete-orphan')
    dorm_chats = relationship('StudentDormChat', back_populates='student', cascade='all, delete-orphan')
    attendance_exceptions = relationship('StudentAttendanceException', back_populates='student', cascade='all, delete-orphan')
    status_changes = relationship('StudentStatusChange', back_populates='student', cascade='all, delete-orphan')
    project_students = relationship('ProjectStudent', back_populates='student', cascade='all, delete-orphan')

    @property
    def class_name(self):
        """通过 class_id 获取班级名称，兼容旧代码"""
        if self.class_obj:
            return self.class_obj.class_name
        return ''


# ===== 标签 =====

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    group_name = Column(String(100), nullable=False)
    color = Column(String(20), default='#409EFF')
    created_at = Column(DateTime, default=datetime.now)
    students = relationship('Student', secondary=student_tags, back_populates='tags')


# ===== Tab2: 学业情况 =====

class GradeRecord(Base):
    """成绩记录 - 只保留 student_id"""
    __tablename__ = 'grade_records'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    semester = Column(String(50), nullable=False)
    course_name = Column(String(200), nullable=False)
    score = Column(Float, nullable=True)
    gpa = Column(Float, nullable=True)
    credit = Column(Float, nullable=True)
    is_repair = Column(Boolean, default=False)  # 是否补修
    course_code = Column(String(50), default='')     # 课程代码
    grade_level = Column(String(10), default='')     # 成绩等级 A/A-/B+/B/C+/C/D/F
    is_makeup = Column(Boolean, default=False)       # 是否重修（与 is_repair 同步）
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='grade_records')


class WarningRecord(Base):
    """预警记录"""
    __tablename__ = 'warning_records'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    warning_type = Column(String(10), nullable=False)  # red/yellow
    description = Column(Text, default='')
    semester = Column(String(50), default='')
    created_at = Column(DateTime, default=datetime.now)
    # v3j-D · D1: 已提醒标记
    reminded = Column(Boolean, default=False)
    reminded_at = Column(DateTime, nullable=True)
    student = relationship('Student', back_populates='warnings')


# ===== Tab3: 党团发展 =====

class PartyProgress(Base):
    """党团发展阶段"""
    __tablename__ = 'party_progress'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    stage = Column(String(50), nullable=False)
    stage_date = Column(String(20), default='')
    contact_person = Column(String(100), default='')
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='party_progress')


# ===== Tab4: 心理档案 =====

class PsychologyRecord(Base):
    """心理关怀记录"""
    __tablename__ = 'psychology_records'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    record_date = Column(String(20), default='')
    location = Column(String(200), default='')
    topic = Column(String(200), default='')
    summary = Column(Text, default='')
    emotion_tags = Column(Text, default='')  # JSON array
    follow_up_plan = Column(Text, default='')
    next_follow_date = Column(String(20), default='')
    attention_level = Column(String(20), default='')   # 关注等级：一级关注/二级关注/三级关注/普通
    counseling_count = Column(Integer, default=0)       # 累计咨询次数
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='psychology_records')


# ===== Tab5: 家庭联络 =====

class FamilyContact(Base):
    """家校沟通记录"""
    __tablename__ = 'family_contacts'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    contact_date = Column(String(20), default='')
    parent_name = Column(String(100), default='')
    contact_method = Column(String(20), default='')
    topic = Column(String(200), default='')
    conclusion = Column(Text, default='')
    attachment = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='family_contacts')


# ===== Tab6: 学生工作 (干部) =====

class StudentCadreRecord(Base):
    """学生干部记录"""
    __tablename__ = 'student_cadre_records'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    position = Column(String(100), nullable=False)
    term = Column(String(50), default='')
    level = Column(String(20), default='')          # 级别：校级/院级/班级
    organization = Column(String(200), default='')  # 组织：学生会/团委/班委等
    start_date = Column(String(20), default='')     # 任职起始
    end_date = Column(String(20), default='')       # 任职结束
    email = Column(String(120), default='')          # 邮箱
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='cadre_records')


# ===== Tab7: 活动参与 =====

class Activity(Base):
    """活动"""
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    activity_date = Column(String(20), default='')
    end_date = Column(String(20), default='')
    location = Column(String(200), default='')
    description = Column(Text, default='')
    activity_type = Column(String(50), default='')
    status = Column(String(20), default='draft')
    max_participants = Column(Integer, default=0)
    organizer = Column(String(120), default='')     # 主办方/组织者
    created_at = Column(DateTime, default=datetime.now)


class ActivitySignup(Base):
    """活动报名/签到"""
    __tablename__ = 'activity_signups'
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey('activities.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    signed_up = Column(Boolean, default=True)
    checked_in = Column(Boolean, default=False)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    activity = relationship('Activity')
    student = relationship('Student', back_populates='activity_signups')


# ===== Tab8: 就业信息 =====

class EmploymentRecord(Base):
    """就业升学台账"""
    __tablename__ = 'employment_records'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    intention_type = Column(String(50), default='')
    target_industry = Column(String(200), default='')
    target_position = Column(String(200), default='')
    internship_company = Column(String(200), default='')
    status = Column(String(50), default='')
    offer_date = Column(String(20), default='')
    salary_range = Column(String(50), default='')
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='employment_records')


# ===== Tab9: 资助与荣誉 (6子模块) =====

class StudentHardship(Base):
    """困难认定"""
    __tablename__ = 'student_hardship'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    hardship_level = Column(String(20), default='')  # 特别困难/困难/一般困难
    academic_year = Column(String(20), default='')
    evidence = Column(Text, default='')  # 佐证材料
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='hardship_records')


class StudentGrant(Base):
    """助学金"""
    __tablename__ = 'student_grants'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    grant_type = Column(String(50), default='')  # 国家助学金/校级助学金等
    amount = Column(Float, default=0)
    academic_year = Column(String(20), default='')
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='grant_records')


class StudentScholarship(Base):
    """奖学金"""
    __tablename__ = 'student_scholarships'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    scholarship_type = Column(String(100), default='')  # 国家奖学金/国家励志/校级等
    amount = Column(Float, default=0)
    academic_year = Column(String(20), default='')
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='scholarship_records')


class StudentLoan(Base):
    """助学贷款"""
    __tablename__ = 'student_loans'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    loan_type = Column(String(50), default='')  # 生源地/校园地
    amount = Column(Float, default=0)
    duration = Column(String(50), default='')  # 贷款期限
    status = Column(String(20), default='')  # 在读/已毕业/已还清
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='loan_records')


class StudentWorkStudy(Base):
    """勤工助学"""
    __tablename__ = 'student_work_study'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    position = Column(String(100), default='')  # 岗位
    hours = Column(Float, default=0)  # 时长
    compensation = Column(Float, default=0)  # 报酬
    academic_year = Column(String(20), default='')
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='work_study_records')


class StudentHonor(Base):
    """评优评先"""
    __tablename__ = 'student_honors'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    honor_name = Column(String(200), default='')  # 奖项名称
    academic_year = Column(String(20), default='')
    level = Column(String(50), default='')  # 国家级/省级/校级/院级
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='honor_records')


# ===== Tab10: 日常管理 (5子模块) =====

class StudentDormVisit(Base):
    """宿舍走访"""
    __tablename__ = 'student_dorm_visits'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    visit_date = Column(String(20), default='')
    dorm_room = Column(String(50), default='')  # 寝室号
    visitor = Column(String(100), default='')  # 走访人
    situation = Column(Text, default='')  # 走访情况
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='dorm_visits')


class StudentLeave(Base):
    """请假记录"""
    __tablename__ = 'student_leaves'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    leave_type = Column(String(20), default='')  # 事假/病假/其他
    start_date = Column(String(20), default='')
    end_date = Column(String(20), default='')
    destination = Column(String(200), default='')  # 去向
    approval_status = Column(String(20), default='pending')  # pending/approved/rejected
    approver = Column(String(100), default='')
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='leave_records')


class StudentDiscipline(Base):
    """违纪处分"""
    __tablename__ = 'student_disciplines'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    discipline_date = Column(String(20), default='')
    discipline_type = Column(String(50), default='')  # 警告/严重警告/记过/留校察看/开除
    level = Column(String(20), default='')  # 院级/校级
    reason = Column(Text, default='')
    attachment = Column(Text, default='')
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='discipline_records')


class StudentDormChat(Base):
    """寝谈记录"""
    __tablename__ = 'student_dorm_chats'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    chat_date = Column(String(20), default='')
    topic = Column(String(200), default='')
    key_points = Column(Text, default='')
    follow_up = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='dorm_chats')


class StudentAttendanceException(Base):
    """考勤异常"""
    __tablename__ = 'student_attendance_exceptions'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    exception_date = Column(String(20), default='')
    course_name = Column(String(200), default='')
    exception_type = Column(String(20), default='')  # 迟到/早退/旷课
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='attendance_exceptions')


# ===== Tab1(子分区): 学籍异动 =====

class StudentStatusChange(Base):
    """学籍异动"""
    __tablename__ = 'student_status_changes'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    change_type = Column(String(50), nullable=False)  # 转专业/休学/复学/参军/退学/退役复学
    start_date = Column(String(20), default='')
    end_date = Column(String(20), default='')
    reason = Column(Text, default='')
    original_info = Column(String(200), default='')  # 原专业/原班级等
    target_info = Column(String(200), default='')  # 新专业/新班级等
    attachment = Column(Text, default='')
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student', back_populates='status_changes')


# ===== Tab11: 专项工作 =====

class Project(Base):
    """专项工作项目"""
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    start_date = Column(String(20), default='')
    end_date = Column(String(20), default='')
    status = Column(String(20), default='active')  # active/completed/archived
    progress = Column(Integer, default=0)  # 0-100
    description = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    project_students = relationship('ProjectStudent', back_populates='project', cascade='all, delete-orphan')


class ProjectStudent(Base):
    """学生-项目关联"""
    __tablename__ = 'project_students'
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    progress = Column(Integer, default=0)  # 学生个人进度
    material_status = Column(String(20), default='pending')  # pending/submitted/approved
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    project = relationship('Project', back_populates='project_students')
    student = relationship('Student', back_populates='project_students')


# ===== 保留的旧表 =====

class Setting(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, default='')


class PartyStudy(Base):
    """党团学习记录"""
    __tablename__ = 'party_study'
    id = Column(Integer, primary_key=True, index=True)
    study_type = Column(String(50), default='')
    study_date = Column(String(20), default='')
    topic = Column(String(200), default='')
    content_summary = Column(Text, default='')
    report_points = Column(Text, default='')
    photo = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    students = relationship('Student', secondary=party_study_students)


class ClassMeeting(Base):
    """班会记录"""
    __tablename__ = 'class_meetings'
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    meeting_date = Column(String(20), default='')
    topic = Column(String(200), default='')
    attendance_count = Column(Integer, default=0)
    absent_students = Column(Text, default='')
    content_summary = Column(Text, default='')
    resolution = Column(Text, default='')
    photo = Column(Text, default='')
    host = Column(String(80), default='')       # 主持人
    recorder = Column(String(80), default='')   # 记录人
    notes = Column(Text, default='')             # 备注
    # v3j-D · D2: 班主任出席
    teacher_attended = Column(Boolean, default=False)  # 班主任是否出席
    teacher_names = Column(String(200), default='')    # 出席老师姓名(逗号分隔)
    created_at = Column(DateTime, default=datetime.now)


class ClassTeacher(Base):
    """班主任"""
    __tablename__ = 'class_teachers'
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    name = Column(String(100), nullable=False)
    staff_no = Column(String(50), default='')
    department = Column(String(200), default='')
    phone = Column(String(50), default='')
    office = Column(String(100), default='')
    research_direction = Column(String(200), default='')
    title = Column(String(50), default='')     # 职称（教授/副教授/讲师）
    email = Column(String(120), default='')     # 邮箱
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)


class KnowledgeDoc(Base):
    __tablename__ = 'knowledge_docs'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, default='')
    doc_type = Column(String(50), default='')
    file_path = Column(String(500), default='')
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class FAQ(Base):
    __tablename__ = 'faqs'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, default='')
    category = Column(String(100), default='')
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class WeeklySummary(Base):
    __tablename__ = 'weekly_summaries'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), default='')
    week_start = Column(String(20), default='')
    week_end = Column(String(20), default='')
    content = Column(Text, default='')
    summary_type = Column(String(20), default='auto')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DocumentTemplate(Base):
    __tablename__ = 'document_templates'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    template_type = Column(String(50), default='')
    content = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)


class GeneratedDocument(Base):
    __tablename__ = 'generated_documents'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='SET NULL'), nullable=True)
    template_id = Column(Integer, ForeignKey('document_templates.id', ondelete='SET NULL'), nullable=True)
    title = Column(String(200), default='')
    content = Column(Text, default='')
    doc_type = Column(String(50), default='')
    created_at = Column(DateTime, default=datetime.now)
    student = relationship('Student')
    template = relationship('DocumentTemplate')


# ===== V3-B 效率中心 =====

class Note(Base):
    """记事本 · 待办 & 备忘 · 想法"""
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, default='')
    content = Column(Text, default='')
    category = Column(String(20), default='memo', index=True)  # memo/todo/idea
    status = Column(String(20), default='active', index=True)  # active/done/archived
    priority = Column(Integer, default=0)  # 0-低 1-中 2-高
    due_date = Column(String(20), default='')  # YYYY-MM-DD (todo 用)
    tags = Column(String(200), default='')  # 逗号分隔
    pinned = Column(Boolean, default=False)
    color = Column(String(20), default='yellow')  # 便签色 yellow/pink/blue/green/purple/orange
    student_id = Column(Integer, ForeignKey('students.id', ondelete='SET NULL'), nullable=True)
    class_id = Column(Integer, ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Countdown(Base):
    """倒计时 · 校历事件"""
    __tablename__ = 'countdowns'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, default='')
    target_date = Column(String(20), nullable=False, default='')  # YYYY-MM-DD
    category = Column(String(30), default='general', index=True)  # exam/deadline/event/holiday/general
    color = Column(String(20), default='blue')  # 马卡龙色
    description = Column(Text, default='')
    pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
