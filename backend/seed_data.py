"""示例数据初始化 - 首次启动时自动导入"""
from datetime import datetime
from models import (
    Student, Tag, GradeRecord, WarningRecord, Setting, student_tags,
    PartyProgress, PsychologyRecord, FamilyContact, StudentCadreRecord,
    ClassTeacher, EmploymentRecord, Activity, PartyStudy, ClassMeeting,
    KnowledgeDoc, FAQ, DocumentTemplate, WeeklySummary,
    Grade, Major, ClassModel,
)
from database import SessionLocal


def seed_if_empty():
    """如果数据库为空，则导入示例数据"""
    db = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(Student).count() > 0:
            return

        print('[Seed] 数据库为空，正在导入示例数据...')

        # ===== 创建标签 =====
        tags_data = [
            # 学业类
            ('学霸', '学业', '#67C23A'),
            ('学业困难', '学业', '#F56C6C'),
            ('专业前10%', '学业', '#409EFF'),
            ('进步明显', '学业', '#67C23A'),
            # 心理类
            ('重点关注', '心理', '#E6A23C'),
            ('需关怀', '心理', '#E6A23C'),
            ('心理稳定', '心理', '#67C23A'),
            # 经济类
            ('家庭困难', '经济', '#909399'),
            ('已获助学金', '经济', '#409EFF'),
            # 政治面貌
            ('党员', '政治面貌', '#F56C6C'),
            ('团员', '政治面貌', '#409EFF'),
            ('群众', '政治面貌', '#909399'),
            ('入党积极分子', '政治面貌', '#E6A23C'),
            # 其它
            ('学生干部', '其它', '#409EFF'),
            ('社团活跃', '其它', '#67C23A'),
        ]
        tags = {}
        for name, group, color in tags_data:
            tag = Tag(name=name, group_name=group, color=color)
            db.add(tag)
            db.flush()
            tags[name] = tag

        db.commit()
        print(f'[Seed] 已初始化 {len(tags)} 个基础标签，跳过示例学生/班级数据（如需演示数据请点"生成测试数据"）')
        return

        # ===== 创建组织架构 =====
        grade_2024 = Grade(grade_name='2024级', start_year=2024)
        grade_2022 = Grade(grade_name='2022级', start_year=2022)
        db.add_all([grade_2024, grade_2022])
        db.flush()

        majors_data = [
            ('计算机科学与技术', grade_2022.id),
            ('软件工程', grade_2022.id),
            ('物联网工程', grade_2022.id),
            ('计算机科学与技术', grade_2024.id),
        ]
        majors_map = {}
        for mname, gid in majors_data:
            m = Major(major_name=mname, grade_id=gid)
            db.add(m); db.flush()
            majors_map[(mname, gid)] = m

        classes_data = [
            ('计科2201班', '计算机科学与技术', grade_2022.id),
            ('计科2202班', '计算机科学与技术', grade_2022.id),
            ('软工2201班', '软件工程',       grade_2022.id),
            ('物联2201班', '物联网工程',     grade_2022.id),
            ('计科2401班', '计算机科学与技术', grade_2024.id),
        ]
        classes_map = {}
        for cname, mname, gid in classes_data:
            c = ClassModel(class_name=cname, major_id=majors_map[(mname, gid)].id)
            db.add(c); db.flush()
            classes_map[cname] = c

        # ===== 创建学生 =====
        # 允许写入 Student 的字段白名单（其余字段自动过滤或合并到 notes）
        STUDENT_FIELDS = {
            'student_no', 'name', 'gender', 'class_id', 'birth_date',
            'political_status', 'phone', 'email', 'parent_phone',
            'birth_source', 'notes', 'pinyin_initial'
        }
        students_data = [
            {
                'student_no': '2022010101', 'name': '张明', 'gender': '男',
                'major': '计算机科学与技术', 'class_name': '计科2201班',
                'birth_date': '2003-05-15', 'political_status': '团员',
                'family_situation': '城市家庭，父母均为教师',
                'phone': '13800001001', 'email': 'zhangming@example.com',
                'tag_names': ['学霸', '专业前10%', '团员', '学生干部'],
            },
            {
                'student_no': '2022010102', 'name': '李华', 'gender': '男',
                'major': '计算机科学与技术', 'class_name': '计科2201班',
                'birth_date': '2003-08-22', 'political_status': '团员',
                'family_situation': '农村家庭，父亲外出务工',
                'phone': '13800001002', 'email': 'lihua@example.com',
                'tag_names': ['学业困难', '家庭困难', '需关怀', '团员'],
            },
            {
                'student_no': '2022010201', 'name': '王芳', 'gender': '女',
                'major': '软件工程', 'class_name': '软工2201班',
                'birth_date': '2004-01-10', 'political_status': '入党积极分子',
                'family_situation': '城市家庭，独生女',
                'phone': '13800002001', 'email': 'wangfang@example.com',
                'tag_names': ['重点关注', '入党积极分子', '社团活跃'],
            },
            {
                'student_no': '2022010202', 'name': '赵强', 'gender': '男',
                'major': '软件工程', 'class_name': '软工2201班',
                'birth_date': '2003-11-03', 'political_status': '党员',
                'family_situation': '城市家庭，父母为公务员',
                'phone': '13800002002', 'email': 'zhaoqiang@example.com',
                'tag_names': ['党员', '学生干部', '进步明显'],
            },
            {
                'student_no': '2022010103', 'name': '刘婷', 'gender': '女',
                'major': '计算机科学与技术', 'class_name': '计科2201班',
                'birth_date': '2003-07-28', 'political_status': '共青团员',
                'family_situation': '单亲家庭，母亲打零工，已获助学金',
                'phone': '13800001003', 'email': 'liuting@example.com',
                'tag_names': ['家庭困难', '已获助学金', '团员', '心理稳定'],
            },
            # === 追加：覆盖群众/预备党员/2024级新生 ===
            {
                'student_no': '2022010104', 'name': '陈涛', 'gender': '男',
                'class_name': '计科2202班', 'birth_date': '2003-09-12',
                'political_status': '群众',
                'family_situation': '普通家庭，未提交入团申请',
                'phone': '13800001004', 'email': 'chentao@example.com',
                'tag_names': ['群众'],
            },
            {
                'student_no': '2022010105', 'name': '林雪', 'gender': '女',
                'class_name': '计科2202班', 'birth_date': '2003-12-01',
                'political_status': '群众',
                'family_situation': '普通家庭',
                'phone': '13800001005', 'email': 'linxue@example.com',
                'tag_names': ['群众', '社团活跃'],
            },
            {
                'student_no': '2022020101', 'name': '孙浩', 'gender': '男',
                'class_name': '物联2201班', 'birth_date': '2003-04-18',
                'political_status': '中共预备党员',
                'family_situation': '城市家庭',
                'phone': '13800003001', 'email': 'sunhao@example.com',
                'tag_names': ['学生干部', '进步明显'],
            },
            {
                'student_no': '2022020102', 'name': '周琳', 'gender': '女',
                'class_name': '物联2201班', 'birth_date': '2004-02-25',
                'political_status': '共青团员',
                'family_situation': '农村家庭',
                'phone': '13800003002', 'email': 'zhoulin@example.com',
                'tag_names': ['团员', '专业前10%'],
            },
            {
                'student_no': '2022030101', 'name': '吴磊', 'gender': '男',
                'class_name': '软工2201班', 'birth_date': '2003-06-30',
                'political_status': '共青团员',
                'family_situation': '城市家庭',
                'phone': '13800004001', 'email': 'wulei@example.com',
                'tag_names': ['团员', '社团活跃'],
            },
            {
                'student_no': '2024010101', 'name': '郑亚', 'gender': '男',
                'class_name': '计科2401班', 'birth_date': '2006-03-14',
                'political_status': '共青团员',
                'family_situation': '普通家庭，2024级新生',
                'phone': '13800005001', 'email': 'zhengya@example.com',
                'tag_names': ['团员'],
            },
            {
                'student_no': '2024010102', 'name': '黄敏', 'gender': '女',
                'class_name': '计科2401班', 'birth_date': '2006-08-20',
                'political_status': '群众',
                'family_situation': '普通家庭，2024级新生',
                'phone': '13800005002', 'email': 'huangmin@example.com',
                'tag_names': ['群众', '需关怀'],
            },
            {
                'student_no': '2024010103', 'name': '许强', 'gender': '男',
                'class_name': '计科2401班', 'birth_date': '2006-11-05',
                'political_status': '共青团员',
                'family_situation': '家庭困难，2024级新生',
                'phone': '13800005003', 'email': 'xuqiang@example.com',
                'tag_names': ['团员', '家庭困难', '需关怀'],
            },
        ]

        students = {}
        for sdata in students_data:
            tag_names = sdata.pop('tag_names', [])
            # 把 class_name 映射到 class_id
            cname = sdata.pop('class_name', None)
            if cname and cname in classes_map:
                sdata['class_id'] = classes_map[cname].id
            # 把不属于 Student 的字段（如 major/family_situation）合并到 notes
            sdata.pop('major', None)
            extras = []
            fs = sdata.pop('family_situation', '')
            if fs:
                extras.append(f'家庭情况: {fs}')
            for k in list(sdata.keys()):
                if k not in STUDENT_FIELDS:
                    extras.append(f'{k}: {sdata.pop(k)}')
            if extras:
                sdata['notes'] = (sdata.get('notes', '') + '\n' + ' | '.join(extras)).strip()
            student = Student(**sdata)
            db.add(student)
            db.flush()
            students[student.student_no] = student
            for tname in tag_names:
                if tname in tags:
                    db.execute(
                        student_tags.insert().values(
                            student_id=student.id, tag_id=tags[tname].id
                        )
                    )

        # ===== 创建成绩 =====
        grades_data = [
            # 张明 - 成绩优秀
            ('2022010101', '2022-2023-1', '高等数学', 92, 3.9, 5),
            ('2022010101', '2022-2023-1', '大学英语', 88, 3.7, 4),
            ('2022010101', '2022-2023-1', '程序设计基础', 95, 4.0, 3),
            ('2022010101', '2022-2023-1', '线性代数', 90, 3.8, 3),
            ('2022010101', '2022-2023-2', '数据结构', 91, 3.9, 4),
            ('2022010101', '2022-2023-2', '离散数学', 88, 3.7, 3),
            ('2022010101', '2022-2023-2', '面向对象编程', 93, 4.0, 3),
            ('2022010101', '2023-2024-1', '操作系统', 89, 3.8, 4),
            ('2022010101', '2023-2024-1', '计算机网络', 91, 3.9, 3),
            # 李华 - 多门挂科（红灯）
            ('2022010102', '2022-2023-1', '高等数学', 45, 1.0, 5),
            ('2022010102', '2022-2023-1', '大学英语', 58, 1.5, 4),
            ('2022010102', '2022-2023-1', '程序设计基础', 52, 1.2, 3),
            ('2022010102', '2022-2023-1', '线性代数', 70, 2.5, 3),
            ('2022010102', '2022-2023-2', '高等数学(补)', 62, 2.0, 5),
            ('2022010102', '2022-2023-2', '数据结构', 48, 1.0, 4),
            ('2022010102', '2022-2023-2', '离散数学', 55, 1.5, 3),
            ('2022010102', '2022-2023-2', '大学英语', 60, 1.8, 4),
            ('2022010102', '2023-2024-1', '操作系统', 42, 0.8, 4),
            ('2022010102', '2023-2024-1', '计算机网络', 50, 1.2, 3),
            ('2022010102', '2023-2024-1', '数据库原理', 55, 1.5, 3),
            # 王芳 - 绩点下降（黄灯）
            ('2022010201', '2022-2023-1', '高等数学', 85, 3.5, 5),
            ('2022010201', '2022-2023-1', '大学英语', 90, 3.8, 4),
            ('2022010201', '2022-2023-1', '程序设计基础', 88, 3.7, 3),
            ('2022010201', '2022-2023-2', '数据结构', 72, 2.8, 4),
            ('2022010201', '2022-2023-2', '离散数学', 68, 2.5, 3),
            ('2022010201', '2022-2023-2', '面向对象编程', 75, 3.0, 3),
            ('2022010201', '2023-2024-1', '操作系统', 65, 2.2, 4),
            ('2022010201', '2023-2024-1', '计算机网络', 70, 2.6, 3),
            ('2022010201', '2023-2024-1', '软件工程导论', 78, 3.2, 3),
            # 赵强 - 成绩中等偏上
            ('2022010202', '2022-2023-1', '高等数学', 78, 3.2, 5),
            ('2022010202', '2022-2023-1', '大学英语', 82, 3.4, 4),
            ('2022010202', '2022-2023-1', '程序设计基础', 80, 3.3, 3),
            ('2022010202', '2022-2023-2', '数据结构', 82, 3.4, 4),
            ('2022010202', '2022-2023-2', '离散数学', 76, 3.0, 3),
            ('2022010202', '2022-2023-2', '面向对象编程', 85, 3.6, 3),
            ('2022010202', '2023-2024-1', '操作系统', 80, 3.3, 4),
            ('2022010202', '2023-2024-1', '计算机网络', 83, 3.5, 3),
            # 刘婷 - 成绩良好
            ('2022010103', '2022-2023-1', '高等数学', 80, 3.3, 5),
            ('2022010103', '2022-2023-1', '大学英语', 85, 3.5, 4),
            ('2022010103', '2022-2023-1', '程序设计基础', 78, 3.2, 3),
            ('2022010103', '2022-2023-1', '线性代数', 82, 3.4, 3),
            ('2022010103', '2022-2023-2', '数据结构', 83, 3.5, 4),
            ('2022010103', '2022-2023-2', '离散数学', 79, 3.2, 3),
            ('2022010103', '2022-2023-2', '面向对象编程', 86, 3.6, 3),
            ('2022010103', '2023-2024-1', '操作系统', 81, 3.4, 4),
            ('2022010103', '2023-2024-1', '计算机网络', 84, 3.5, 3),
        ]

        for sno, sem, course, score, gpa, credit in grades_data:
            student = students.get(sno)
            if student:
                grade = GradeRecord(
                    student_id=student.id, semester=sem,
                    course_name=course, score=score, gpa=gpa, credit=credit
                )
                db.add(grade)

        db.flush()

        # ===== 创建预警记录 =====
        # 李华 - 红灯 (2022-2023-1 挂科3门, 2022-2023-2 挂科2门, 2023-2024-1 挂科3门)
        lihua = students['2022010102']
        db.add(WarningRecord(
            student_id=lihua.id, warning_type='red',
            description='挂科3门: 高等数学, 大学英语, 程序设计基础',
            semester='2022-2023-1'
        ))
        db.add(WarningRecord(
            student_id=lihua.id, warning_type='red',
            description='挂科2门: 数据结构, 离散数学',
            semester='2022-2023-2'
        ))
        db.add(WarningRecord(
            student_id=lihua.id, warning_type='red',
            description='挂科3门: 操作系统, 计算机网络, 数据库原理',
            semester='2023-2024-1'
        ))

        # 王芳 - 黄灯 (绩点下降)
        wangfang = students['2022010201']
        db.add(WarningRecord(
            student_id=wangfang.id, warning_type='yellow',
            description='绩点从3.67下降至2.78 (下降0.89)',
            semester='2022-2023-2'
        ))
        db.add(WarningRecord(
            student_id=wangfang.id, warning_type='yellow',
            description='绩点从2.78下降至2.60 (下降0.18)',
            semester='2023-2024-1'
        ))

        # ===== 默认设置 =====
        db.add(Setting(key='fail_course_threshold', value='2'))
        db.add(Setting(key='gpa_drop_threshold', value='0.5'))

        # ===== V2 示例数据 =====
        zhangming = students['2022010101']
        lihua = students['2022010102']
        wangfang = students['2022010201']
        zhaoqiang = students['2022010202']
        liuting = students['2022010103']

        # 党团发展
        db.add(PartyProgress(student_id=zhangming.id, stage='团员', stage_date='2020-05-04', contact_person='李老师'))
        db.add(PartyProgress(student_id=zhangming.id, stage='递交入党申请书', stage_date='2022-09-15', contact_person='王老师'))
        db.add(PartyProgress(student_id=zhaoqiang.id, stage='正式党员', stage_date='2023-12-01', contact_person='张老师'))
        db.add(PartyProgress(student_id=zhaoqiang.id, stage='预备党员', stage_date='2022-12-01', contact_person='张老师'))
        db.add(PartyProgress(student_id=wangfang.id, stage='积极分子', stage_date='2023-03-15', contact_person='李老师'))
        db.add(PartyProgress(student_id=liuting.id, stage='团员', stage_date='2020-05-04', contact_person='李老师'))

        # 心理关怀
        db.add(PsychologyRecord(
            student_id=lihua.id, record_date='2024-01-10', location='辅导员办公室',
            topic='学业压力疏导', summary='因多门挂科产生焦虑情绪，进行心理疏导',
            emotion_tags='["焦虑","挂科压力"]', follow_up_plan='每周约谈一次',
            next_follow_date='2024-01-17'
        ))
        db.add(PsychologyRecord(
            student_id=wangfang.id, record_date='2024-01-08', location='心理咨询室',
            topic='绩点下降情绪低落', summary='绩点持续下降导致自信心受挫',
            emotion_tags='["焦虑","自信心不足"]', follow_up_plan='推荐参加学习互助小组',
            next_follow_date='2024-01-22'
        ))

        # 家校沟通
        db.add(FamilyContact(
            student_id=lihua.id, contact_date='2024-01-05', parent_name='李华父亲',
            contact_method='电话', topic='通报学业预警情况',
            conclusion='家长表示配合督促学习'
        ))
        db.add(FamilyContact(
            student_id=liuting.id, contact_date='2023-12-20', parent_name='刘婷母亲',
            contact_method='微信', topic='助学金发放确认',
            conclusion='已确认收到本学期助学金'
        ))

        # 学生干部
        db.add(StudentCadreRecord(student_id=zhangming.id, position='班长', term='2022-2024'))
        db.add(StudentCadreRecord(student_id=liuting.id, position='学习委员', term='2022-2024'))
        db.add(StudentCadreRecord(student_id=zhaoqiang.id, position='团支书', term='2022-2024'))
        db.add(StudentCadreRecord(student_id=wangfang.id, position='文艺委员', term='2022-2024'))

        # 班主任
        db.add(ClassTeacher(
            class_id=classes_map['计科2201班'].id, name='陈教授', staff_no='T2019001',
            department='计算机学院', phone='13900001001', office='信息楼305',
            research_direction='人工智能'
        ))
        db.add(ClassTeacher(
            class_id=classes_map['软工2201班'].id, name='周副教授', staff_no='T2020002',
            department='软件工程系', phone='13900001002', office='信息楼408',
            research_direction='软件工程'
        ))

        # 就业升学
        db.add(EmploymentRecord(
            student_id=zhangming.id, intention_type='考研', target_industry='计算机',
            target_position='研究生', status='备考中', notes='目标：本校计算机硕士'
        ))
        db.add(EmploymentRecord(
            student_id=zhaoqiang.id, intention_type='就业', target_industry='互联网',
            target_position='后端开发工程师', internship_company='某科技公司',
            status='已签约', offer_date='2024-03-15', salary_range='15-20K'
        ))
        db.add(EmploymentRecord(
            student_id=wangfang.id, intention_type='考公', target_position='公务员',
            status='备考中', notes='目标：省级机关'
        ))

        # 活动日程
        db.add(Activity(
            title='春季运动会', activity_date='2024-04-15', location='学校操场',
            description='校春季田径运动会', activity_type='体育', status='published'
        ))
        db.add(Activity(
            title='学术讲座：AI前沿', activity_date='2024-03-20', location='报告厅A',
            description='人工智能前沿技术讲座', activity_type='学术', status='completed'
        ))

        # 党团学习
        db.add(PartyStudy(
            study_type='主题党日', study_date='2024-01-15',
            topic='学习党的二十大精神', content_summary='集体学习二十大报告要点'
        ))
        db.add(PartyStudy(
            study_type='团日活动', study_date='2024-02-28',
            topic='雷锋月志愿服务', content_summary='组织社区志愿服务活动'
        ))

        # 班会记录
        db.add(ClassMeeting(
            class_id=classes_map['计科2201班'].id, meeting_date='2024-01-08',
            topic='期末考试动员', attendance_count=28,
            content_summary='强调考风考纪，安排复习计划'
        ))
        db.add(ClassMeeting(
            class_id=classes_map['软工2201班'].id, meeting_date='2024-01-10',
            topic='新学期规划', attendance_count=25,
            content_summary='分享新学期学习目标和计划'
        ))

        # 知识库
        db.add(KnowledgeDoc(
            title='学生手册（2024版）', doc_type='markdown',
            content='# 学生手册\n## 第一章 总则\n本手册适用于全体在校学生...\n## 第二章 学籍管理\n### 第一节 入学与注册\n新生须在规定时间内完成注册...',
            chunk_count=5
        ))
        db.add(KnowledgeDoc(
            title='奖学金评定办法', doc_type='markdown',
            content='# 奖学金评定办法\n## 国家奖学金\n条件：成绩排名前10%，无挂科记录...\n## 校级奖学金\n条件：成绩排名前30%...',
            chunk_count=3
        ))

        # FAQ
        db.add(FAQ(question='如何申请助学金？', answer='学生可向辅导员提交助学金申请表，需附家庭经济困难证明材料。', category='资助', is_published=True))
        db.add(FAQ(question='挂科后如何补考？', answer='挂科学生可在下学期开学初参加补考，具体时间安排见教务处通知。', category='学业', is_published=True))
        db.add(FAQ(question='如何办理休学？', answer='需提交休学申请表，经学院审批后到教务处办理。休学期限一般为一年。', category='学籍', is_published=True))

        # 文书模板
        db.add(DocumentTemplate(
            name='学生评语', template_type='评语',
            content='{{姓名}}同学，{{性别}}，{{专业}}{{班级}}学生。该生政治面貌为{{政治面貌}}，在校期间表现良好，学习认真，团结同学。'
        ))
        db.add(DocumentTemplate(
            name='综合素质鉴定', template_type='综合素质鉴定',
            content='{{姓名}}同学（学号：{{学号}}），就读于{{专业}}{{班级}}。该生在校期间综合素质表现如下：\n一、思想政治方面：{{政治面貌}}\n二、学习方面：\n三、生活方面：'
        ))

        db.commit()
        print(f'[Seed] 示例数据导入完成: 5名学生, {len(tags_data)}个标签, {len(grades_data)}条成绩 + V2数据')

    except Exception as e:
        db.rollback()
        print(f'[Seed] 示例数据导入失败: {e}')
    finally:
        db.close()
