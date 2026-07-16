"""
V3-A 全域大 seed
生成 300+ 学生 + 覆盖 10 大模块 + 校区/宿舍/身份证 完整测试数据
"""
import random
import logging
from database import SessionLocal, engine, Base
from models import (
    Grade, Major, ClassModel, Student, Tag, GradeRecord, WarningRecord,
    PartyProgress, PsychologyRecord, FamilyContact, StudentCadreRecord,
    Activity, ActivitySignup, EmploymentRecord,
    StudentHardship, StudentGrant, StudentScholarship, StudentLoan,
    StudentWorkStudy, StudentHonor, StudentDormVisit, StudentLeave,
    StudentDiscipline, StudentDormChat, StudentAttendanceException,
    StudentStatusChange, Project, ProjectStudent, Setting, PartyStudy,
    ClassMeeting, ClassTeacher, KnowledgeDoc, FAQ, WeeklySummary,
    DocumentTemplate,
)

logger = logging.getLogger(__name__)
random.seed(20260716)

SURNAMES = list('王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范石金廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龚史陶黎贺顾毛郝龙邵万钱严武戴莫孔向汤')
GIVEN_1 = list('伟芳娜英敏静丽强磊军洋勇艳杰娟涛明超兰霞平刚桂建国建华志强志明志刚国强国庆晓明晓东晓峰晓丽晓红晓燕晓芳晓娟晓玲梓涵梓萱梓豪子涵子轩子墨子昂')
GIVEN_2 = list('嘉浩宇轩豪泽然俊博文瑞晨昊天萱雨欣悦妍雅琪思远晨曦欣然晗睿智')

PY_MAP = {
    '王':'w','李':'l','张':'z','刘':'l','陈':'c','杨':'y','黄':'h','赵':'z',
    '吴':'w','周':'z','徐':'x','孙':'s','马':'m','朱':'z','胡':'h','郭':'g',
    '何':'h','高':'g','林':'l','罗':'l','郑':'z','梁':'l','谢':'x','宋':'s',
    '唐':'t','许':'x','韩':'h','冯':'f','邓':'d','曹':'c','彭':'p','曾':'z',
    '肖':'x','田':'t','董':'d','袁':'y','潘':'p','蒋':'j','蔡':'c','余':'y',
    '杜':'d','叶':'y','程':'c','苏':'s','魏':'w','吕':'l','丁':'d','任':'r',
    '沈':'s','姚':'y','卢':'l','姜':'j','崔':'c','钟':'z','谭':'t','陆':'l',
    '汪':'w','范':'f','石':'s','金':'j','廖':'l','贾':'j','夏':'x','韦':'w',
    '付':'f','方':'f','白':'b','邹':'z','孟':'m','熊':'x','秦':'q','邱':'q',
    '江':'j','尹':'y','薛':'x','闫':'y','段':'d','雷':'l','侯':'h','龚':'g',
    '史':'s','陶':'t','黎':'l','贺':'h','顾':'g','毛':'m','郝':'h','龙':'l',
    '邵':'s','万':'w','钱':'q','严':'y','武':'w','戴':'d','莫':'m',
    '孔':'k','向':'x','汤':'t',
}

PROVINCES = [
    ('福建省', ['福州市·鼓楼区','福州市·仓山区','厦门市·思明区','泉州市·丰泽区','漳州市·芗城区','莆田市·城厢区','宁德市·蕉城区','龙岩市·新罗区','南平市·延平区','三明市·梅列区']),
    ('江苏省', ['苏州市·工业园区','南京市·鼓楼区','无锡市·梁溪区','常州市·天宁区','徐州市·云龙区','南通市·崇川区']),
    ('浙江省', ['杭州市·西湖区','宁波市·海曙区','温州市·鹿城区','绍兴市·越城区','嘉兴市·南湖区','金华市·婺城区']),
    ('广东省', ['广州市·天河区','深圳市·南山区','东莞市·南城街道','佛山市·禅城区','珠海市·香洲区','中山市·东区']),
    ('湖北省', ['武汉市·武昌区','武汉市·洪山区','宜昌市·西陵区','襄阳市·襄城区']),
    ('湖南省', ['长沙市·岳麓区','长沙市·芙蓉区','株洲市·天元区','衡阳市·雁峰区']),
    ('河南省', ['郑州市·金水区','洛阳市·涧西区','开封市·龙亭区','南阳市·卧龙区']),
    ('四川省', ['成都市·武侯区','成都市·锦江区','绵阳市·涪城区','德阳市·旌阳区']),
    ('江西省', ['南昌市·东湖区','赣州市·章贡区','九江市·浔阳区']),
    ('安徽省', ['合肥市·蜀山区','芜湖市·镜湖区','马鞍山市·雨山区']),
    ('山东省', ['济南市·历下区','青岛市·市南区','烟台市·芝罘区']),
    ('河北省', ['石家庄市·长安区','唐山市·路南区','保定市·莲池区']),
]

CAMPUSES = ['铜盘校区', '旗山校区']
DORM_BUILDINGS = {
    '铜盘校区': ['1号楼','2号楼','3号楼','5号楼','7号楼','东区A栋','东区B栋'],
    '旗山校区': ['学生公寓1号楼','学生公寓2号楼','学生公寓3号楼','学生公寓4号楼','紫金苑1栋','紫金苑2栋','明德园A栋'],
}
OFF_CAMPUS_STREETS = ['学院路12号','大学城东街56号','紫荆里3幢','红光社区7栋','建新北路88号']

POLITICAL_STATUS = ['群众','共青团员','入党积极分子','党员发展对象','预备党员','中共党员']
COURSE_POOL = [
    ('高等数学 A（上）',4),('高等数学 A（下）',4),('线性代数',3),('概率论与数理统计',3),
    ('大学物理（上）',4),('大学物理（下）',4),('大学英语（一）',3),('大学英语（二）',3),
    ('C 语言程序设计',3),('Python 程序设计',3),('数据结构',4),('操作系统',4),
    ('计算机网络',3),('数据库原理',3),('软件工程',3),('编译原理',3),
    ('算法设计与分析',3),('人工智能导论',3),('机器学习',3),('深度学习',3),
    ('毛泽东思想概论',2),('马克思主义基本原理',2),('中国近现代史纲要',2),
    ('大学物理实验',1),('体育（一）',1),('体育（二）',1),('军事理论',2),
]


def gen_id_card(birth_year):
    area_code = random.choice(['350102','350111','320505','330106','440106','420106','430102','410103','510107','460100','510104'])
    month = random.randint(1,12); day = random.randint(1,28); seq = random.randint(100, 999)
    body = f'{area_code}{birth_year:04d}{month:02d}{day:02d}{seq:03d}'
    weights = [7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2]
    check_map = '10X98765432'
    s = sum(int(body[i]) * weights[i] for i in range(17))
    return body + check_map[s % 11]


def gen_phone():
    prefix = random.choice(['135','136','137','138','139','150','151','152','158','159','188','189','178','170'])
    return prefix + f'{random.randint(0, 99999999):08d}'


def pinyin_initial(name):
    if not name:
        return ''
    return PY_MAP.get(name[0], 'x')


def gen_chinese_name():
    s = random.choice(SURNAMES)
    if random.random() < 0.4:
        return s + random.choice(GIVEN_1)
    return s + random.choice(GIVEN_1) + random.choice(GIVEN_2)


def seed_large_dataset():
    db = SessionLocal()
    stats = {}
    try:
        if db.query(Student).count() >= 200:
            return {'skipped': True, 'reason': 'Student 数量>=200，跳过大 seed'}

        # 年级
        year_names = ['2022 级', '2023 级', '2024 级', '2025 级']
        year_prefix = {'2022 级':2022, '2023 级':2023, '2024 级':2024, '2025 级':2025}
        grades = {}
        for yn in year_names:
            g = db.query(Grade).filter(Grade.grade_name == yn).first()
            if not g:
                g = Grade(grade_name=yn, start_year=year_prefix[yn]); db.add(g); db.flush()
            grades[yn] = g
        stats['grades'] = len(grades)

        # 专业
        major_defs = [('计算机科学与技术','CS'),('软件工程','SE'),('网络空间安全','NS'),('人工智能','AI')]
        majors = {}
        for gn, gobj in grades.items():
            year_short = gn[:4]
            for mn, mcode in major_defs:
                m = db.query(Major).filter(Major.major_name == mn, Major.grade_id == gobj.id).first()
                if not m:
                    m = Major(major_name=mn, grade_id=gobj.id)
                    db.add(m); db.flush()
                majors[(gn, mn)] = m
        stats['majors'] = len(majors)

        # 班级：每年级每专业 3 班 = 48 班
        classes = []
        for (gn, mn), mobj in majors.items():
            year_short = gn[:2]
            major_code = {'计算机科学与技术':'计科','软件工程':'软工','网络空间安全':'网安','人工智能':'智能'}[mn]
            for ci in range(1, 4):
                cname = f'{major_code}{year_short}0{ci}班'
                c = db.query(ClassModel).filter(ClassModel.class_name == cname).first()
                if not c:
                    c = ClassModel(
                        class_name=cname, major_id=mobj.id,
                        class_teacher=random.choice(['陈教授','周副教授','林副教授','刘讲师','张教授','李副教授','王副教授','赵讲师']),
                        monitor='', league_secretary='',
                    )
                    db.add(c); db.flush()
                classes.append(c)
        db.commit()
        stats['classes'] = len(classes)

        # 学生 每班 7~8 = 336~384
        all_students = []
        for cobj in classes:
            mobj = db.query(Major).get(cobj.major_id)
            gobj = db.query(Grade).get(mobj.grade_id)
            grade_year = year_prefix[gobj.grade_name]
            n_students = random.randint(7, 8)
            for si in range(n_students):
                sno = f'{grade_year}{cobj.id:03d}{si+1:02d}'
                name = gen_chinese_name()
                gender = random.choices(['男','女'], weights=[55,45])[0]
                birth_year = grade_year - 18 - random.randint(0, 1)
                campus = random.choices(CAMPUSES, weights=[30,70])[0] if grade_year >= 2024 else random.choices(CAMPUSES, weights=[60,40])[0]
                is_off = random.random() < 0.08
                if is_off:
                    building = ''; room = ''
                    off_addr = f'{random.choice(OFF_CAMPUS_STREETS)}·{random.randint(1,20)}号楼{random.randint(101,808)}'
                else:
                    building = random.choice(DORM_BUILDINGS[campus])
                    room = f'{random.randint(1,10)}0{random.randint(1,8)}'
                    off_addr = ''
                province, cities = random.choice(PROVINCES)
                city = random.choice(cities)
                stu = Student(
                    student_no=sno, name=name, pinyin_initial=pinyin_initial(name),
                    gender=gender, class_id=cobj.id,
                    birth_date=f'{birth_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                    political_status=random.choices(POLITICAL_STATUS, weights=[10,55,15,8,8,4])[0],
                    phone=gen_phone(), email=f'stu{sno}@fzu.edu.cn',
                    parent_phone=gen_phone(),
                    birth_source=f'{province}·{city}',
                    id_card=gen_id_card(birth_year),
                    campus=campus, dorm_building=building, dorm_room=room,
                    is_off_campus=is_off, off_campus_address=off_addr,
                    notes='',
                )
                db.add(stu); all_students.append(stu)
            db.flush()
        db.commit()
        stats['students'] = len(all_students)

        # 干部 & 回填班长/团支书
        cadre_positions = ['班长','团支书','学习委员','生活委员','文艺委员','体育委员','宣传委员','心理委员','组织委员','纪律委员']
        stats['cadres'] = 0
        for cobj in classes:
            cls_students = [s for s in all_students if s.class_id == cobj.id]
            if len(cls_students) < 3: continue
            picks = random.sample(cls_students, min(6, len(cls_students)))
            cobj.monitor = picks[0].name
            cobj.league_secretary = picks[1].name
            for i, stu in enumerate(picks):
                pos = cadre_positions[i] if i < len(cadre_positions) else '委员'
                db.add(StudentCadreRecord(student_id=stu.id, position=pos, term=f'{2022+i%3}-{2024+i%3}', notes=''))
                stats['cadres'] += 1
        db.commit()

        # 班主任
        teacher_pool = [
            ('陈教授','T2019001','计算机学院','人工智能'),
            ('周副教授','T2020002','软件工程系','软件工程'),
            ('林副教授','T2018003','网络空间安全学院','网络安全'),
            ('刘讲师','T2021004','计算机学院','分布式系统'),
            ('张教授','T2015005','人工智能学院','机器学习'),
            ('李副教授','T2017006','计算机学院','数据库'),
            ('王副教授','T2019007','软件工程系','软件测试'),
            ('赵讲师','T2022008','网络空间安全学院','密码学'),
        ]
        stats['class_teachers'] = 0
        for cobj in classes:
            tp = next((x for x in teacher_pool if x[0] == cobj.class_teacher), teacher_pool[0])
            db.add(ClassTeacher(
                class_id=cobj.id, name=tp[0], staff_no=tp[1], department=tp[2],
                phone=gen_phone(), office=f'信息楼{random.randint(3,6)}0{random.randint(1,9)}',
                research_direction=tp[3],
            ))
            stats['class_teachers'] += 1
        db.commit()

        # 成绩 + 预警
        semesters = ['2023-1','2023-2','2024-1','2024-2','2025-1']
        bulk_grades = []
        stats['warnings'] = 0
        for stu in all_students:
            cls = db.query(ClassModel).get(stu.class_id)
            mj = db.query(Major).get(cls.major_id)
            gr = db.query(Grade).get(mj.grade_id)
            year = year_prefix[gr.grade_name]
            n_sem = min(len(semesters), 2026 - year)
            student_semesters = semesters[:max(1, n_sem)]
            fail_courses = 0
            for sem in student_semesters:
                courses = random.sample(COURSE_POOL, random.randint(4,6))
                for cname, credit in courses:
                    score = max(0, min(100, int(random.gauss(78, 12))))
                    is_repair = random.random() < 0.03
                    if score >= 90: gpa = 4.0
                    elif score >= 85: gpa = 3.7
                    elif score >= 80: gpa = 3.3
                    elif score >= 75: gpa = 3.0
                    elif score >= 70: gpa = 2.7
                    elif score >= 65: gpa = 2.3
                    elif score >= 60: gpa = 2.0
                    else:
                        gpa = 0.0; fail_courses += 1
                    bulk_grades.append(GradeRecord(
                        student_id=stu.id, semester=sem, course_name=cname,
                        score=score, gpa=gpa, credit=credit, is_repair=is_repair,
                    ))
            if fail_courses >= 2:
                db.add(WarningRecord(student_id=stu.id, warning_type='red', description=f'累计挂科 {fail_courses} 门', semester=student_semesters[-1]))
                stats['warnings'] += 1
            elif fail_courses == 1 and random.random() < 0.7:
                db.add(WarningRecord(student_id=stu.id, warning_type='yellow', description='挂科 1 门，进入学业观察', semester=student_semesters[-1]))
                stats['warnings'] += 1
        db.bulk_save_objects(bulk_grades)
        stats['grades'] = len(bulk_grades)
        db.commit()

        # 党团发展
        stats['party_progress'] = 0
        for stu in all_students:
            ps = stu.political_status
            if ps == '中共党员': stages = ['申请入党','入党积极分子','发展对象','预备党员','正式党员']
            elif ps == '预备党员': stages = ['申请入党','入党积极分子','发展对象','预备党员']
            elif ps == '党员发展对象': stages = ['申请入党','入党积极分子','发展对象']
            elif ps == '入党积极分子': stages = ['申请入党','入党积极分子']
            elif ps == '共青团员' and random.random() < 0.15: stages = ['申请入党']
            else: continue
            for i, s in enumerate(stages):
                db.add(PartyProgress(
                    student_id=stu.id, stage=s,
                    stage_date=f'{2022+i//2}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                    contact_person=random.choice(['陈教授','周副教授','林副教授']), notes='',
                ))
                stats['party_progress'] += 1
        db.commit()

        # 心理关怀
        stats['psychology'] = 0
        for stu in random.sample(all_students, k=int(len(all_students) * 0.12)):
            for _ in range(random.randint(1,3)):
                db.add(PsychologyRecord(
                    student_id=stu.id,
                    record_date=f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                    location=random.choice(['心理咨询室','辅导员办公室','宿舍走访','线上会议']),
                    topic=random.choice(['学业焦虑','人际关系','情感问题','家庭困扰','职业迷茫','宿舍矛盾']),
                    summary='详谈约 40 分钟，情绪稳定后达成初步共识',
                    emotion_tags=random.choice(['["焦虑","低落"]','["焦虑"]','["紧张","失眠"]','["低落"]','["迷茫"]']),
                    follow_up_plan='下周再谈一次', next_follow_date=f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                ))
                stats['psychology'] += 1
        db.commit()

        # 家校
        stats['family'] = 0
        for stu in random.sample(all_students, k=int(len(all_students) * 0.4)):
            for _ in range(random.randint(1,2)):
                db.add(FamilyContact(
                    student_id=stu.id, contact_date=f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                    parent_name=random.choice(['父亲','母亲']) + stu.name[0],
                    contact_method=random.choice(['电话','微信','家访','短信']),
                    topic=random.choice(['学业情况反馈','假期返家安排','心理状况沟通','学费缴纳','奖学金告知']),
                    conclusion='家长表示理解并配合', attachment='',
                ))
                stats['family'] += 1
        db.commit()

        # 活动 + 报名
        activity_defs = [
            ('2024 春季运动会','2024-04-15','体育场','校春季田径运动会','体育'),
            ('AI 前沿技术讲座','2024-03-20','报告厅A','人工智能前沿','学术'),
            ('宿舍文化节','2024-05-10','东区广场','宿舍装饰评比','文体'),
            ('毕业生就业双选会','2024-11-08','体育馆','校招双选','就业'),
            ('迎新晚会','2024-09-20','大剧场','迎接新生','文体'),
            ('党史学习月','2024-06-01','党建活动室','党史教育','党建'),
            ('数学建模培训','2024-07-01','实验楼','建模选拔','学科'),
            ('心理健康周','2024-10-10','心理咨询中心','心理疏导','心理'),
            ('志愿服务日','2024-12-05','社区','敬老院服务','志愿'),
            ('程序设计大赛','2024-11-20','机房','ACM 选拔','学科'),
        ]
        activities = []
        for title, adate, loc, desc, atype in activity_defs:
            a = Activity(title=title, activity_date=adate, end_date=adate, location=loc, description=desc, activity_type=atype, status='completed', max_participants=100)
            db.add(a); activities.append(a)
        db.flush()
        stats['activities'] = len(activities)
        stats['signups'] = 0
        for stu in all_students:
            for a in random.sample(activities, k=random.randint(0, 4)):
                db.add(ActivitySignup(activity_id=a.id, student_id=stu.id, signed_up=True, checked_in=random.random()<0.85, points=random.choice([1,2,3,5])))
                stats['signups'] += 1
        db.commit()

        # 就业
        stats['employment'] = 0
        for stu in all_students:
            cls = db.query(ClassModel).get(stu.class_id)
            mj = db.query(Major).get(cls.major_id)
            gr = db.query(Grade).get(mj.grade_id)
            year = year_prefix[gr.grade_name]
            if year <= 2023 and random.random() < 0.7:
                it = random.choice(['考研','就业','考公','留学','创业','待定'])
                status = {'考研':'备考中','就业':random.choice(['求职中','已签约','实习中']),'考公':'备考中','留学':'申请中','创业':'启动中','待定':'规划中'}[it]
                db.add(EmploymentRecord(
                    student_id=stu.id, intention_type=it,
                    target_industry=random.choice(['互联网','金融','制造','教育','公务员','事业单位']),
                    target_position=random.choice(['软件工程师','算法工程师','产品经理','数据分析师','运维工程师','研究生']),
                    internship_company=random.choice(['','某科技公司','某金融公司','某互联网大厂']),
                    status=status, offer_date='2024-05-15' if status=='已签约' else '',
                    salary_range=random.choice(['','8-12K','12-18K','15-25K','20-30K']),
                    notes='',
                ))
                stats['employment'] += 1
        db.commit()

        # 资助
        stats['hardship']=0; stats['grants']=0; stats['loans']=0; stats['scholarships']=0; stats['workstudy']=0; stats['honors']=0
        for stu in random.sample(all_students, k=int(len(all_students)*0.15)):
            db.add(StudentHardship(student_id=stu.id, hardship_level=random.choice(['特别困难','困难','一般困难']), academic_year='2024-2025', evidence='贫困证明', notes=''))
            stats['hardship'] += 1
            if random.random() < 0.7:
                db.add(StudentGrant(student_id=stu.id, grant_type=random.choice(['国家助学金','校级助学金','企业资助']), amount=random.choice([3000,4000,5000,6000]), academic_year='2024-2025', notes=''))
                stats['grants'] += 1
            if random.random() < 0.5:
                db.add(StudentLoan(student_id=stu.id, loan_type=random.choice(['生源地信用助学贷款','校园地助学贷款']), amount=random.choice([8000,12000]), duration='2024-2025', status='还款中', notes=''))
                stats['loans'] += 1
        for stu in random.sample(all_students, k=int(len(all_students)*0.25)):
            db.add(StudentScholarship(student_id=stu.id, scholarship_type=random.choice(['国家奖学金','国家励志奖学金','校一等奖学金','校二等奖学金','校三等奖学金']), amount=random.choice([8000,5000,3000,2000,1000]), academic_year='2024-2025', notes=''))
            stats['scholarships'] += 1
        for stu in random.sample(all_students, k=int(len(all_students)*0.1)):
            db.add(StudentWorkStudy(student_id=stu.id, position=random.choice(['图书馆助管','实验室助理','食堂值日','教学秘书']), hours=random.choice([6,8,10,12]), compensation=random.choice([300,400,500,600]), academic_year='2024-2025', notes=''))
            stats['workstudy'] += 1
        for stu in random.sample(all_students, k=int(len(all_students)*0.3)):
            for _ in range(random.randint(1,2)):
                db.add(StudentHonor(student_id=stu.id, honor_name=random.choice(['三好学生','优秀学生干部','校园之星','优秀共青团员','优秀志愿者']), academic_year='2024-2025', level=random.choice(['院级','校级','省级']), notes=''))
                stats['honors'] += 1
        db.commit()

        # 日常管理
        stats['dorm_visits']=0; stats['leaves']=0; stats['disciplines']=0; stats['dorm_chats']=0; stats['attendance']=0
        for stu in random.sample(all_students, k=int(len(all_students)*0.4)):
            for _ in range(random.randint(1,2)):
                db.add(StudentDormVisit(student_id=stu.id, visit_date=f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}', dorm_room=stu.dorm_room, visitor=random.choice(['辅导员','班主任','学工老师']), situation='宿舍卫生整洁', notes=''))
                stats['dorm_visits'] += 1
        for stu in random.sample(all_students, k=int(len(all_students)*0.3)):
            for _ in range(random.randint(1,2)):
                m = random.randint(1,12); d = random.randint(1,20)
                db.add(StudentLeave(student_id=stu.id, leave_type=random.choice(['事假','病假','其他']), start_date=f'2024-{m:02d}-{d:02d}', end_date=f'2024-{m:02d}-{min(28,d+random.randint(1,3)):02d}', destination=random.choice(['家中','医院','校外','其他']), approval_status=random.choice(['approved','approved','pending']), approver='辅导员', notes=''))
                stats['leaves'] += 1
        for stu in random.sample(all_students, k=int(len(all_students)*0.05)):
            db.add(StudentDiscipline(student_id=stu.id, discipline_date=f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}', discipline_type=random.choice(['警告','严重警告','记过']), level=random.choice(['院级','校级']), reason=random.choice(['宿舍违规大功率','上课旷课','考试违纪']), attachment='', notes=''))
            stats['disciplines'] += 1
        for stu in random.sample(all_students, k=int(len(all_students)*0.3)):
            db.add(StudentDormChat(student_id=stu.id, chat_date=f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}', topic=random.choice(['学习规划','职业发展','宿舍关系','假期安排']), key_points='深入沟通', follow_up='后续跟进'))
            stats['dorm_chats'] += 1
        for stu in random.sample(all_students, k=int(len(all_students)*0.25)):
            for _ in range(random.randint(1,3)):
                db.add(StudentAttendanceException(student_id=stu.id, exception_date=f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}', course_name=random.choice(COURSE_POOL)[0], exception_type=random.choice(['迟到','早退','旷课']), notes=''))
                stats['attendance'] += 1
        db.commit()

        # 学籍异动
        stats['status_changes'] = 0
        for stu in random.sample(all_students, k=int(len(all_students)*0.03)):
            db.add(StudentStatusChange(student_id=stu.id, change_type=random.choice(['休学','复学','转专业','参军']), start_date='2024-03-01', end_date='2024-09-01', reason='个人原因', original_info='原班级', target_info='新班级', attachment='', notes=''))
            stats['status_changes'] += 1
        db.commit()

        # 班会
        stats['meetings'] = 0
        topics_pool = ['期末考试动员','新学期规划','安全教育','宿舍卫生检查','诚信考试','职业规划','心理健康','奖学金评定','党团学习','假期安全']
        for cobj in classes:
            for i in range(random.randint(3,5)):
                db.add(ClassMeeting(class_id=cobj.id, meeting_date=f'2024-{i*2+1:02d}-{random.randint(5,25):02d}', topic=random.choice(topics_pool), attendance_count=random.randint(25,35), absent_students='', content_summary='本次班会内容涉及学期重点工作', resolution='已布置任务'))
                stats['meetings'] += 1
        db.commit()

        # 党团学习
        stats['party_study'] = 0
        for i in range(15):
            ps = PartyStudy(study_type=random.choice(['主题党日','团日活动','党课学习','支部会议']), study_date=f'2024-{i%12+1:02d}-{random.randint(5,25):02d}', topic=random.choice(['学习二十大精神','党史学习教育','青年责任担当','雷锋精神传承']), content_summary='集体学习并展开研讨', report_points='')
            ps.students = random.sample(all_students, k=random.randint(5,10))
            db.add(ps); stats['party_study'] += 1
        db.commit()

        # Setting
        for k, v in [('fail_course_threshold','2'),('gpa_drop_threshold','0.5')]:
            if not db.query(Setting).filter(Setting.key == k).first():
                db.add(Setting(key=k, value=v))

        # Tags
        for group, names in {'政治面貌':['群众','共青团员','积极分子','党员'],'学业状态':['优秀','良好','观察','预警'],'资助类别':['特困','困难','一般','无'],'学生干部':['班长','团支书','学习委员','其他委员']}.items():
            for n in names:
                if not db.query(Tag).filter(Tag.name == n, Tag.group_name == group).first():
                    db.add(Tag(name=n, group_name=group, color='#4A7A8C'))
        db.commit()
        stats['tags'] = db.query(Tag).count()

        # 知识库/FAQ/模板
        if db.query(KnowledgeDoc).count() < 3:
            db.add_all([
                KnowledgeDoc(title='学生手册（2024版）', doc_type='markdown', content='# 学生手册\n\n## 第一章 总则\n本手册适用于全体在校学生。'),
                KnowledgeDoc(title='奖学金评定办法', doc_type='markdown', content='# 奖学金评定办法\n按学习成绩和综合表现评定。'),
                KnowledgeDoc(title='学生行为规范', doc_type='markdown', content='# 学生行为规范\n遵守校规校纪。'),
            ])
        if db.query(FAQ).count() < 3:
            db.add_all([
                FAQ(question='如何申请奖学金？', answer='每年 10 月登录学工系统申请。', category='资助'),
                FAQ(question='挂科了怎么办？', answer='联系任课老师和辅导员安排补考或重修。', category='学业'),
                FAQ(question='想转专业需要什么条件？', answer='大一学年平均分排名专业前 20%。', category='学籍'),
            ])
        if db.query(DocumentTemplate).count() < 2:
            db.add_all([
                DocumentTemplate(name='学生评语模板', template_type='评语', content='{{name}}同学在本学期...'),
                DocumentTemplate(name='家长告知书模板', template_type='家校', content='尊敬的{{parent_name}}...'),
            ])
        db.commit()

        # Project
        if db.query(Project).count() < 1:
            proj = Project(name='2024 毕业生就业帮扶专项', start_date='2024-03-01', end_date='2024-07-15', status='active', progress=60, description='精准对接就业困难学生')
            db.add(proj); db.flush()
            grad_2022 = [s for s in all_students if year_prefix[db.query(Grade).get(db.query(Major).get(db.query(ClassModel).get(s.class_id).major_id).grade_id).grade_name] == 2022]
            for stu in random.sample(grad_2022, k=min(20, len(grad_2022))):
                db.add(ProjectStudent(project_id=proj.id, student_id=stu.id, notes=''))
            db.commit()

        logger.info(f'[seed_large] 完成 {stats}')
        return stats
    except Exception as e:
        db.rollback()
        logger.exception(f'[seed_large] 失败: {e}')
        raise
    finally:
        db.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    Base.metadata.create_all(bind=engine)
    print(seed_large_dataset())
