"""
seed_large.py — 25 级计算机学院全域测试数据
核心约束：
  1. 只有 25 级学生（enrollment_year=2025）
  2. 只有 2 个学期：2025-2026-1 / 2025-2026-2
  3. 所有业务日期在 2025-09-01 ~ 2026-07-31
  4. 所有模块数据与学期挂钩
  5. 党员发展逻辑：学期1 递交申请→积极分子；学期2 积极分子→发展对象→预备党员
  6. 截止 2025-2026-2 末累计党员约 15-25 人
  7. 约 300-400 学生，6-8 个班级，3-4 个专业
"""
import random
import logging
from datetime import date, timedelta
from database import SessionLocal, engine, Base
from models import (
    ComprehensiveAssessment, StudentInterview,
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
random.seed(20260724)

# ──────────────────────── 学期定义 ────────────────────────
SEMESTERS = ['2025-2026-1', '2025-2026-2']
SEM_DATES = {
    '2025-2026-1': (date(2025, 9, 1), date(2026, 1, 31)),
    '2025-2026-2': (date(2026, 2, 1), date(2026, 7, 31)),
}
MIN_DATE = date(2025, 9, 1)
MAX_DATE = date(2026, 7, 31)

# ──────────────────────── 姓名生成 ────────────────────────
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

# ──────────────────────── 生源地 ────────────────────────
PROVINCES = [
    ('福建省', ['福州市·鼓楼区','福州市·仓山区','厦门市·思明区','泉州市·丰泽区','漳州市·芗城区','莆田市·城厢区','宁德市·蕉城区','龙岩市·新罗区','南平市·延平区','三明市·梅列区']),
    ('江苏省', ['苏州市·工业园区','南京市·鼓楼区','无锡市·梁溪区','常州市·天宁区','徐州市·云龙区','南通市·崇川区']),
    ('浙江省', ['杭州市·西湖区','宁波市·海曙区','温州市·鹿城区','绍兴市·越城区','嘉兴市·南湖区','金华市·婺城区']),
    ('广东省', ['广州市·天河区','深圳市·南山区','东莞市·南城街道','佛山市·禅城区','珠海市·香洲区','中山市·东区']),
    ('湖北省', ['武汉市·武昌区','武汉市·洪山区','宜昌市·西陵区','襄阳市·襄城区']),
    ('湖南省', ['长沙市·岳麓区','长沙市·芙蓉区','株洲市·天元区','衡阳市·雁峰区']),
    ('江西省', ['南昌市·东湖区','赣州市·章贡区','九江市·浔阳区']),
    ('安徽省', ['合肥市·蜀山区','芜湖市·镜湖区','马鞍山市·雨山区']),
]

# ──────────────────────── 校区 / 宿舍 ────────────────────────
CAMPUSES = ['铜盘校区', '旗山校区']
DORM_BUILDINGS = {
    '铜盘校区': ['1号楼','2号楼','3号楼','5号楼','7号楼','东区A栋','东区B栋'],
    '旗山校区': ['学生公寓1号楼','学生公寓2号楼','学生公寓3号楼','学生公寓4号楼','紫金苑1栋','紫金苑2栋','明德园A栋'],
}
OFF_CAMPUS_STREETS = ['学院路12号','大学城东街56号','紫荆里3幢','红光社区7栋','建新北路88号']

# ──────────────────────── 专业 & 班级 ────────────────────────
MAJOR_DEFS = [
    ('计算机科学与技术', 'CS', 2),   # 25计算机1班, 25计算机2班
    ('大数据技术',       'BD', 2),   # 25大数据1班, 25大数据2班
    ('人工智能',         'AI', 2),   # 25人工智能1班, 25人工智能2班
    ('软件工程',         'SE', 2),   # 25软件工程1班, 25软件工程2班
]
# 共 8 个班级，每班 ~45 人 ≈ 360 学生

# ──────────────────────── 课程池（计算机学院） ────────────────────────
COURSE_POOL_SEM1 = [
    ('高等数学A（上）', 4), ('线性代数', 3), ('C语言程序设计', 4),
    ('计算机导论', 3), ('大学英语（一）', 3), ('体育（一）', 1),
    ('毛泽东思想概论', 2), ('中国近现代史纲要', 2), ('军事理论', 2),
    ('大学物理（上）', 4), ('大学物理实验', 1),
]

COURSE_POOL_SEM2 = [
    ('高等数学A（下）', 4), ('概率论与数理统计', 3), ('数据结构与算法', 4),
    ('Python程序设计', 3), ('大学英语（二）', 3), ('体育（二）', 1),
    ('马克思主义基本原理', 2), ('大学物理（下）', 4),
    ('离散数学', 3), ('数字逻辑', 3),
]

# ──────────────────────── 工具函数 ────────────────────────

def gen_id_card(birth_year):
    area_code = random.choice(['350102','350111','320505','330106','440106','420106','430102','410103','510107','510104'])
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    seq = random.randint(100, 999)
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


def rand_date_in_semester(sem):
    """在指定学期范围内生成随机日期字符串 YYYY-MM-DD"""
    start, end = SEM_DATES[sem]
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.isoformat()


def rand_date_in_range(start_d, end_d):
    """在指定日期范围内生成随机日期字符串"""
    delta = (end_d - start_d).days
    if delta < 0:
        return start_d.isoformat()
    d = start_d + timedelta(days=random.randint(0, delta))
    return d.isoformat()


# ──────────────────────── 主函数 ────────────────────────

def seed_large_dataset():
    db = SessionLocal()
    stats = {}
    try:
        if db.query(Student).count() >= 300:
            return {'skipped': True, 'reason': 'Student 数量>=300，跳过大 seed'}

        existing_snos = {row[0] for row in db.query(Student.student_no).all()}

        # ═══════════════ 1. 年级 ═══════════════
        grade_obj = db.query(Grade).filter(Grade.grade_name == '2025级').first()
        if not grade_obj:
            grade_obj = Grade(grade_name='2025级', start_year=2025)
            db.add(grade_obj); db.flush()
        stats['grades'] = 1

        # ═══════════════ 2. 专业 ═══════════════
        majors = {}
        for mn, mcode, _ in MAJOR_DEFS:
            m = db.query(Major).filter(Major.major_name == mn, Major.grade_id == grade_obj.id).first()
            if not m:
                m = Major(major_name=mn, grade_id=grade_obj.id)
                db.add(m); db.flush()
            majors[mn] = m
        stats['majors'] = len(majors)

        # ═══════════════ 3. 班级 ═══════════════
        CLASS_NAME_MAP = {
            '计算机科学与技术': '计算机',
            '大数据技术':       '大数据',
            '人工智能':         '人工智能',
            '软件工程':         '软件工程',
        }
        classes = []
        for mn, mcode, n_cls in MAJOR_DEFS:
            short = CLASS_NAME_MAP[mn]
            for ci in range(1, n_cls + 1):
                cname = f'25{short}{ci}班'
                c = db.query(ClassModel).filter(ClassModel.class_name == cname).first()
                if not c:
                    c = ClassModel(
                        class_name=cname, major_id=majors[mn].id,
                        class_teacher='', monitor='', league_secretary='',
                    )
                    db.add(c); db.flush()
                classes.append(c)
        db.commit()
        stats['classes'] = len(classes)

        # ═══════════════ 4. 学生 ═══════════════
        all_students = []
        # 先分配政治面貌：控制党员发展数量
        # 总共约 360 学生，目标：预备党员 18 人，发展对象 22 人，积极分子 45 人
        POLITICAL_WEIGHTS = {
            '群众': 0.08,
            '共青团员': 0.66,
            '入党积极分子': 0.14,
            '党员发展对象': 0.06,
            '中共预备党员': 0.04,
            '中共党员': 0.02,
        }
        POLITICAL_CHOICES = list(POLITICAL_WEIGHTS.keys())
        POLITICAL_W = list(POLITICAL_WEIGHTS.values())

        for cobj in classes:
            n_students = random.randint(40, 50)
            for si in range(n_students):
                sno = f'2025{cobj.id:03d}{si+1:02d}'
                if sno in existing_snos:
                    continue
                existing_snos.add(sno)
                name = gen_chinese_name()
                gender = random.choices(['男','女'], weights=[55,45])[0]
                birth_year = 2025 - 18 - random.randint(0, 1)  # 2006 or 2007
                campus = random.choices(CAMPUSES, weights=[30,70])[0]
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
                _ps = random.choices(POLITICAL_CHOICES, weights=POLITICAL_W)[0]
                _join_league = ''
                _join_party = ''
                if _ps != '群众':
                    # 入团时间：14-16 岁 → 2020-2022 年，在入学前
                    _ly = birth_year + random.randint(14, 16)
                    _join_league = f'{_ly}-{random.randint(1,12):02d}-{random.randint(1,28):02d}'
                if _ps == '中共预备党员':
                    # 预备党员在 2025-2026 学年内入党
                    _join_party = rand_date_in_range(date(2026, 4, 1), date(2026, 7, 1))
                elif _ps == '中共党员':
                    _join_party = rand_date_in_range(date(2026, 5, 1), date(2026, 7, 1))

                stu = Student(
                    student_no=sno, name=name, pinyin_initial=pinyin_initial(name),
                    gender=gender, class_id=cobj.id,
                    birth_date=f'{birth_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                    political_status=_ps,
                    join_league_date=_join_league,
                    join_party_date=_join_party,
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

        # ═══════════════ 5. 班主任 ═══════════════
        _surnames_t = ['陈','周','林','刘','张','李','王','赵','孙','钱','吴','郑','冯','蒋','沈','韩','杨','朱','秦','许']
        _title_pool = ['教授','副教授','讲师']
        _direction_pool = ['计算机视觉','自然语言处理','深度学习','数据挖掘','软件架构','大数据分析','智能系统','网络空间安全','计算机图形学','推荐系统']
        _office_buildings = ['计算机楼','信息楼A','信息楼B','工科楼','软件楼','数据科学楼']
        _used_names = set()
        stats['class_teachers'] = 0
        for i, cobj in enumerate(classes):
            for _try in range(50):
                surname = random.choice(_surnames_t)
                title = random.choice(_title_pool)
                tname = f'{surname}{title}'
                if tname not in _used_names:
                    _used_names.add(tname)
                    break
            else:
                tname = f'{random.choice(_surnames_t)}{random.choice(_title_pool)}{i}'
                _used_names.add(tname)
            staff_no = f'T2025{i+1:03d}'
            email = f'{staff_no.lower()}@example.edu'
            office = f'{random.choice(_office_buildings)}{random.randint(2,6)}0{random.randint(1,9)}'
            direction = random.choice(_direction_pool)
            cobj.class_teacher = tname
            db.add(ClassTeacher(
                class_id=cobj.id, name=tname, staff_no=staff_no, department='计算机学院',
                phone=gen_phone(), office=office,
                research_direction=direction, title=title, email=email,
            ))
            stats['class_teachers'] += 1
        db.commit()

        # ═══════════════ 6. 学生干部 ═══════════════
        cadre_positions = ['班长','团支书','学习委员','生活委员','文艺委员','体育委员','宣传委员','心理委员','组织委员','纪律委员']
        stats['cadres'] = 0
        for cobj in classes:
            cls_students = [s for s in all_students if s.class_id == cobj.id]
            if len(cls_students) < 3:
                continue
            picks = random.sample(cls_students, min(6, len(cls_students)))
            cobj.monitor = picks[0].name
            cobj.league_secretary = picks[1].name
            for i, stu in enumerate(picks):
                pos = cadre_positions[i] if i < len(cadre_positions) else '委员'
                _level = '团支部' if pos == '团支书' else '班级'
                _org = '团支部' if pos == '团支书' else '班委会'
                # 两个学期都有任职
                for sem in SEMESTERS:
                    sem_start, sem_end = SEM_DATES[sem]
                    _email = f'{stu.student_no or stu.id}@stu.example.edu'
                    db.add(StudentCadreRecord(
                        student_id=stu.id, position=pos, term=sem,
                        level=_level, organization=_org,
                        start_date=sem_start.isoformat(),
                        end_date=sem_end.isoformat(),
                        email=_email, notes='',
                    ))
                    stats['cadres'] += 1
        db.commit()

        # 党支部干部
        party_positions = ['党支部书记', '党支部组织委员', '党支部宣传委员', '党支部纪检委员']
        for cobj in classes:
            party_pool = [s for s in all_students
                          if s.class_id == cobj.id
                          and s.political_status in ('中共党员', '中共预备党员', '党员发展对象')]
            if len(party_pool) < 2:
                continue
            picks = random.sample(party_pool, min(4, len(party_pool)))
            for i, stu in enumerate(picks):
                pos = party_positions[i]
                _email = f'{stu.student_no or stu.id}@stu.example.edu'
                db.add(StudentCadreRecord(
                    student_id=stu.id, position=pos, term='2025-2026',
                    level='党支部', organization='党支部',
                    start_date='2025-09-01', end_date='2026-07-31',
                    email=_email, notes='',
                ))
                stats['cadres'] += 1
        db.commit()

        # ═══════════════ 7. 成绩 + 学业预警 ═══════════════
        bulk_grades = []
        stats['warnings'] = 0
        for stu in all_students:
            total_fail = 0
            for sem in SEMESTERS:
                if sem == '2025-2026-1':
                    courses = random.sample(COURSE_POOL_SEM1, random.randint(4, 6))
                else:
                    courses = random.sample(COURSE_POOL_SEM2, random.randint(4, 6))
                sem_fail = 0
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
                        gpa = 0.0; sem_fail += 1
                    _prefix = 'CS' if any(kw in cname for kw in ('程序','算法','数据','计算机','离散','数字')) else 'GEN'
                    _ccode = f'{_prefix}{hash(cname) % 900 + 100:03d}'
                    if score >= 90: _lvl = 'A'
                    elif score >= 85: _lvl = 'A-'
                    elif score >= 80: _lvl = 'B+'
                    elif score >= 75: _lvl = 'B'
                    elif score >= 70: _lvl = 'C+'
                    elif score >= 65: _lvl = 'C'
                    elif score >= 60: _lvl = 'D'
                    else: _lvl = 'F'
                    bulk_grades.append(GradeRecord(
                        student_id=stu.id, semester=sem, course_name=cname,
                        score=score, gpa=gpa, credit=credit, is_repair=is_repair,
                        course_code=_ccode, grade_level=_lvl, is_makeup=is_repair,
                    ))
                total_fail += sem_fail
                # 每学期单独判定预警
                if sem_fail >= 2:
                    db.add(WarningRecord(
                        student_id=stu.id, warning_type='red',
                        description=f'{sem}学期挂科 {sem_fail} 门', semester=sem,
                    ))
                    stats['warnings'] += 1
                elif sem_fail == 1 and random.random() < 0.7:
                    db.add(WarningRecord(
                        student_id=stu.id, warning_type='yellow',
                        description=f'{sem}学期挂科 1 门，进入学业观察', semester=sem,
                    ))
                    stats['warnings'] += 1
        db.bulk_save_objects(bulk_grades)
        stats['scores'] = len(bulk_grades)
        db.commit()

        # ═══════════════ 8. 综合测评 ═══════════════
        stats['comprehensive'] = 0
        bulk_ca = []
        for stu in all_students:
            for sem in SEMESTERS:
                moral = round(max(0, min(100, random.gauss(82, 8))), 1)
                academic = round(max(0, min(100, random.gauss(78, 12))), 1)
                physical = round(max(0, min(100, random.gauss(80, 10))), 1)
                aesthetic = round(max(0, min(100, random.gauss(79, 9))), 1)
                labor_score = round(max(0, min(100, random.gauss(81, 8))), 1)
                total = round(moral * 0.2 + academic * 0.4 + physical * 0.15 + aesthetic * 0.1 + labor_score * 0.15, 1)
                bulk_ca.append(ComprehensiveAssessment(
                    student_id=stu.id, semester=sem,
                    moral_score=moral, academic_score=academic,
                    physical_score=physical, aesthetic_score=aesthetic,
                    labor_score=labor_score, total_score=total, notes='',
                ))
                stats['comprehensive'] += 1
        db.bulk_save_objects(bulk_ca)
        db.commit()

        # ═══════════════ 9. 学生访谈 ═══════════════
        stats['interview'] = 0
        interview_types = ['常规访谈', '学业指导', '心理关怀', '就业规划', '预警访谈', '家校沟通']
        interview_statuses = ['已完成', '待进行', '需跟进']
        for stu in random.sample(all_students, k=min(int(len(all_students) * 0.6), len(all_students))):
            n_interviews = random.randint(1, 3)
            for _ in range(n_interviews):
                sem = random.choice(SEMESTERS)
                idate = rand_date_in_semester(sem)
                follow_sem = '2025-2026-2' if sem == '2025-2026-1' else '2025-2026-2'
                db.add(StudentInterview(
                    student_id=stu.id,
                    interview_date=idate,
                    interview_type=random.choice(interview_types),
                    interviewer=random.choice(['张老师', '李老师', '王老师', '刘老师', '陈老师']),
                    location=random.choice(['辅导员办公室', '教学楼A301', '线上视频', '学生宿舍', '心理咨询室']),
                    topic=random.choice(['期中学习情况', '学业规划', '心理状态', '职业意向', '班级生活', '家庭情况']),
                    content='与学生进行了深入交流，了解了近期的学习和生活情况。',
                    feedback=random.choice(['学生状态良好', '需要持续关注', '已制定改进计划', '建议加强辅导']),
                    follow_up='下个月继续跟踪' if random.random() < 0.4 else '',
                    status=random.choice(interview_statuses),
                    remind_date=rand_date_in_semester(follow_sem) if random.random() < 0.3 else '',
                ))
                stats['interview'] += 1
        db.commit()

        # ═══════════════ 10. 党团发展 ═══════════════
        stats['party_progress'] = 0
        for stu in all_students:
            ps = stu.political_status
            if ps == '中共党员':
                stages = [
                    ('递交入党申请书', '2025-2026-1', date(2025, 9, 15), date(2025, 10, 15)),
                    ('入党积极分子',   '2025-2026-1', date(2025, 11, 1), date(2025, 12, 31)),
                    ('发展对象',       '2025-2026-2', date(2026, 2, 15), date(2026, 3, 31)),
                    ('中共预备党员',   '2025-2026-2', date(2026, 4, 1),  date(2026, 5, 31)),
                    ('中共党员',       '2025-2026-2', date(2026, 6, 1),  date(2026, 7, 15)),
                ]
            elif ps == '中共预备党员':
                stages = [
                    ('递交入党申请书', '2025-2026-1', date(2025, 9, 15), date(2025, 10, 15)),
                    ('入党积极分子',   '2025-2026-1', date(2025, 11, 1), date(2025, 12, 31)),
                    ('发展对象',       '2025-2026-2', date(2026, 2, 15), date(2026, 3, 31)),
                    ('中共预备党员',   '2025-2026-2', date(2026, 4, 15), date(2026, 6, 15)),
                ]
            elif ps == '党员发展对象':
                stages = [
                    ('递交入党申请书', '2025-2026-1', date(2025, 9, 15), date(2025, 10, 31)),
                    ('入党积极分子',   '2025-2026-1', date(2025, 11, 1), date(2026, 1, 15)),
                    ('发展对象',       '2025-2026-2', date(2026, 3, 1),  date(2026, 5, 15)),
                ]
            elif ps == '入党积极分子':
                stages = [
                    ('递交入党申请书', '2025-2026-1', date(2025, 9, 15), date(2025, 11, 15)),
                    ('入党积极分子',   '2025-2026-2', date(2025, 12, 1), date(2026, 2, 28)),
                ]
            elif ps == '共青团员' and random.random() < 0.15:
                stages = [
                    ('递交入党申请书', '2025-2026-1', date(2025, 10, 1), date(2025, 12, 31)),
                ]
            else:
                continue
            for sname, _sem, d_start, d_end in stages:
                sdate = rand_date_in_range(d_start, d_end)
                db.add(PartyProgress(
                    student_id=stu.id, stage=sname,
                    stage_date=sdate,
                    contact_person=random.choice(['陈教授', '周副教授', '林副教授', '刘讲师']),
                    notes='',
                ))
                stats['party_progress'] += 1
        db.commit()

        # ═══════════════ 11. 心理关怀 ═══════════════
        stats['psychology'] = 0
        for stu in random.sample(all_students, k=int(len(all_students) * 0.12)):
            for sem in SEMESTERS:
                _atlvl = random.choices(['一级关注','二级关注','三级关注','普通'], weights=[1,2,3,4])[0]
                _cc = random.randint(1, 5)
                rdate = rand_date_in_semester(sem)
                sem_end = SEM_DATES[sem][1]
                nf_start = sem_end - timedelta(days=random.randint(7, 30))
                if nf_start < SEM_DATES[sem][0]:
                    nf_start = SEM_DATES[sem][0]
                nf_date = rand_date_in_range(nf_start, sem_end)
                db.add(PsychologyRecord(
                    student_id=stu.id,
                    record_date=rdate,
                    location=random.choice(['心理咨询室','辅导员办公室','宿舍走访','线上会议']),
                    topic=random.choice(['学业焦虑','人际关系','情感问题','家庭困扰','职业迷茫','宿舍矛盾']),
                    summary='详谈约 40 分钟，情绪稳定后达成初步共识',
                    emotion_tags=random.choice(['["焦虑","低落"]','["焦虑"]','["紧张","失眠"]','["低落"]','["迷茫"]']),
                    follow_up_plan='下周再谈一次',
                    next_follow_date=nf_date,
                    attention_level=_atlvl, counseling_count=_cc,
                ))
                stats['psychology'] += 1
        db.commit()

        # ═══════════════ 12. 家校沟通 ═══════════════
        stats['family'] = 0
        for stu in random.sample(all_students, k=int(len(all_students) * 0.4)):
            for sem in SEMESTERS:
                for _ in range(random.randint(1, 2)):
                    db.add(FamilyContact(
                        student_id=stu.id,
                        contact_date=rand_date_in_semester(sem),
                        parent_name=random.choice(['父亲','母亲']) + stu.name[0],
                        contact_method=random.choice(['电话','微信','家访','短信']),
                        topic=random.choice(['学业情况反馈','假期返家安排','心理状况沟通','学费缴纳','奖学金告知']),
                        conclusion='家长表示理解并配合', attachment='',
                    ))
                    stats['family'] += 1
        db.commit()

        # ═══════════════ 13. 活动参与 ═══════════════
        activity_defs = [
            # 学期1 活动
            ('2025级新生入学教育',      '2025-2026-1', '2025-09-10', '大礼堂',       '新生入学教育及校规校纪学习',   '教育'),
            ('新生军训总结大会',        '2025-2026-1', '2025-09-30', '体育场',       '军训汇报表演',               '体育'),
            ('2025级程序设计新生赛',    '2025-2026-1', '2025-11-15', '计算机实验室',  'C语言程序设计竞赛',          '学科竞赛'),
            ('秋季运动会',              '2025-2026-1', '2025-11-20', '体育场',       '校秋季田径运动会',            '体育'),
            ('心理健康周',              '2025-2026-1', '2025-10-20', '心理咨询中心',  '心理疏导与讲座',             '心理'),
            ('志愿服务日',              '2025-2026-1', '2025-12-05', '社区',          '敬老院志愿服务',             '志愿'),
            ('元旦迎新晚会',            '2025-2026-1', '2025-12-28', '大剧场',        '迎接新年文艺汇演',           '文体'),
            ('期末诚信考试主题班会',    '2025-2026-1', '2026-01-05', '教学楼',        '诚信考试教育',               '教育'),
            # 学期2 活动
            ('寒假社会实践成果展',      '2025-2026-2', '2026-03-05', '大学生活动中心', '社会实践成果展示',          '志愿'),
            ('ACM程序设计竞赛校选',     '2025-2026-2', '2026-03-20', '计算机实验室',  'ACM-ICPC校队选拔',          '学科竞赛'),
            ('"互联网+"创新创业大赛',   '2025-2026-2', '2026-04-10', '创业孵化中心',  '创新创业项目路演',           '创新创业'),
            ('春季运动会',              '2025-2026-2', '2026-04-25', '体育场',       '校春季田径运动会',            '体育'),
            ('大数据分析大赛',          '2025-2026-2', '2026-05-10', '数据科学实验室', '大数据分析技能竞赛',         '学科竞赛'),
            ('"挑战杯"科技作品竞赛',    '2025-2026-2', '2026-05-15', '大学生活动中心', '学术科技作品竞赛',           '创新创业'),
            ('AI创新应用大赛',          '2025-2026-2', '2026-05-20', 'AI实验室',      '人工智能应用创新赛',         '学科竞赛'),
            ('宿舍文化节',              '2025-2026-2', '2026-05-25', '东区广场',      '宿舍装饰评比',              '文体'),
            ('党史学习月',              '2025-2026-2', '2026-06-01', '党建活动室',    '党史教育主题活动',           '党建'),
            ('暑期社会实践出征仪式',    '2025-2026-2', '2026-07-01', '大礼堂',       '暑期社会实践动员',            '志愿'),
            ('期末总结表彰大会',        '2025-2026-2', '2026-07-10', '报告厅',       '学期总结与评优',             '教育'),
        ]
        activities = []
        for title, sem, adate, loc, desc, atype in activity_defs:
            _org_pool = ['学生会文体部','团委学习部','心理健康中心','学工办','计算机学院','校团委']
            a = Activity(
                title=title, activity_date=adate, end_date=adate,
                location=loc, description=desc, activity_type=atype,
                status='completed', max_participants=100,
                organizer=random.choice(_org_pool),
            )
            db.add(a); activities.append(a)
        db.flush()
        stats['activities'] = len(activities)
        stats['signups'] = 0
        for stu in all_students:
            for a in random.sample(activities, k=random.randint(1, 5)):
                db.add(ActivitySignup(
                    activity_id=a.id, student_id=stu.id,
                    signed_up=True, checked_in=random.random() < 0.85,
                    points=random.choice([1, 2, 3, 5]),
                ))
                stats['signups'] += 1
        db.commit()

        # ═══════════════ 14. 就业意向（大一新生，仅意向规划） ═══════════════
        stats['employment'] = 0
        for stu in random.sample(all_students, k=int(len(all_students) * 0.5)):
            it = random.choice(['考研','就业','考公','留学','待定'])
            status_map = {'考研':'规划中','就业':'规划中','考公':'规划中','留学':'规划中','待定':'规划中'}
            db.add(EmploymentRecord(
                student_id=stu.id, intention_type=it,
                target_industry=random.choice(['互联网','人工智能','金融科技','网络安全','游戏开发','公务员','事业单位']),
                target_position=random.choice(['软件工程师','算法工程师','数据分析师','前端开发','后端开发','研究生','公务员']),
                internship_company='',
                status=status_map[it], offer_date='',
                salary_range='', notes='大一职业规划意向',
            ))
            stats['employment'] += 1
        db.commit()

        # ═══════════════ 15. 奖助贷 ═══════════════
        stats['hardship'] = 0; stats['grants'] = 0; stats['loans'] = 0
        stats['scholarships'] = 0; stats['workstudy'] = 0; stats['honors'] = 0

        hardship_students = random.sample(all_students, k=int(len(all_students) * 0.15))
        for stu in hardship_students:
            db.add(StudentHardship(
                student_id=stu.id,
                hardship_level=random.choice(['特别困难','困难','一般困难']),
                academic_year='2025-2026', evidence='贫困证明', notes='',
            ))
            stats['hardship'] += 1
            # 两个学期都有助学金
            for sem in SEMESTERS:
                if random.random() < 0.7:
                    db.add(StudentGrant(
                        student_id=stu.id,
                        grant_type=random.choice(['国家助学金','校级助学金','企业资助']),
                        amount=random.choice([1500, 2000, 3000, 4000, 5000]),
                        academic_year='2025-2026', notes=f'{sem}学期发放',
                    ))
                    stats['grants'] += 1
            if random.random() < 0.5:
                db.add(StudentLoan(
                    student_id=stu.id,
                    loan_type=random.choice(['生源地信用助学贷款','校园地助学贷款']),
                    amount=random.choice([8000, 12000]),
                    duration='2025-2026', status='在读', notes='',
                ))
                stats['loans'] += 1

        # 奖学金：两个学期都有
        scholarship_students = random.sample(all_students, k=int(len(all_students) * 0.25))
        for stu in scholarship_students:
            for sem in SEMESTERS:
                db.add(StudentScholarship(
                    student_id=stu.id,
                    scholarship_type=random.choice(['国家奖学金','国家励志奖学金','校一等奖学金','校二等奖学金','校三等奖学金']),
                    amount=random.choice([8000, 5000, 3000, 2000, 1000]),
                    academic_year='2025-2026', notes=f'{sem}学期',
                ))
                stats['scholarships'] += 1

        # 勤工助学：两个学期
        workstudy_students = random.sample(all_students, k=int(len(all_students) * 0.1))
        for stu in workstudy_students:
            for sem in SEMESTERS:
                db.add(StudentWorkStudy(
                    student_id=stu.id,
                    position=random.choice(['图书馆助管','实验室助理','网络中心值班','教学秘书助理']),
                    hours=random.choice([6, 8, 10, 12]),
                    compensation=random.choice([300, 400, 500, 600]),
                    academic_year='2025-2026', notes=f'{sem}学期',
                ))
                stats['workstudy'] += 1

        # 综合荣誉（两个学期都有）
        honor_students = random.sample(all_students, k=int(len(all_students) * 0.3))
        for stu in honor_students:
            for sem in SEMESTERS:
                db.add(StudentHonor(
                    student_id=stu.id,
                    honor_name=random.choice(['三好学生','优秀学生干部','校园之星','优秀共青团员','优秀志愿者']),
                    academic_year='2025-2026',
                    level=random.choice(['院级','校级']),
                    notes=f'{sem}学期',
                ))
                stats['honors'] += 1

        # 学科竞赛获奖
        competition_awards = [
            'ACM程序设计竞赛', '全国大学生数学建模竞赛',
            '"互联网+"大学生创新创业大赛', '"挑战杯"课外学术科技作品竞赛',
            '大数据分析大赛', 'AI创新应用大赛', '程序设计新生赛',
        ]
        award_levels = [
            ('国家级','一等奖'), ('国家级','二等奖'), ('国家级','三等奖'),
            ('省级','一等奖'), ('省级','二等奖'), ('省级','三等奖'),
            ('校级','一等奖'), ('校级','二等奖'), ('校级','三等奖'),
        ]
        comp_students = random.sample(all_students, k=int(len(all_students) * 0.2))
        for stu in comp_students:
            for sem in SEMESTERS:
                if random.random() < 0.6:
                    lvl, rank = random.choice(award_levels)
                    comp = random.choice(competition_awards)
                    db.add(StudentHonor(
                        student_id=stu.id,
                        honor_name=f'{comp} {rank}',
                        academic_year='2025-2026',
                        level=lvl, notes=f'{sem}学期学科竞赛',
                    ))
                    stats['honors'] += 1
        db.commit()

        # ═══════════════ 16. 日常管理 ═══════════════
        stats['dorm_visits'] = 0; stats['leaves'] = 0; stats['disciplines'] = 0
        stats['dorm_chats'] = 0; stats['attendance'] = 0

        # 宿舍走访：两个学期
        for stu in random.sample(all_students, k=int(len(all_students) * 0.4)):
            for sem in SEMESTERS:
                for _ in range(random.randint(1, 2)):
                    db.add(StudentDormVisit(
                        student_id=stu.id,
                        visit_date=rand_date_in_semester(sem),
                        dorm_room=stu.dorm_room,
                        visitor=random.choice(['辅导员','班主任','学工老师']),
                        situation='宿舍卫生整洁', notes='',
                    ))
                    stats['dorm_visits'] += 1

        # 请假：两个学期
        for stu in random.sample(all_students, k=int(len(all_students) * 0.3)):
            for sem in SEMESTERS:
                for _ in range(random.randint(1, 2)):
                    sem_start, sem_end = SEM_DATES[sem]
                    sdate = rand_date_in_range(sem_start, sem_end - timedelta(days=3))
                    edate_d = date.fromisoformat(sdate) + timedelta(days=random.randint(1, 3))
                    if edate_d > sem_end:
                        edate_d = sem_end
                    db.add(StudentLeave(
                        student_id=stu.id,
                        leave_type=random.choice(['事假','病假','其他']),
                        start_date=sdate,
                        end_date=edate_d.isoformat(),
                        destination=random.choice(['家中','医院','校外','其他']),
                        approval_status=random.choice(['approved','approved','pending']),
                        approver='辅导员', notes='',
                    ))
                    stats['leaves'] += 1

        # 违纪：少量
        for stu in random.sample(all_students, k=int(len(all_students) * 0.04)):
            sem = random.choice(SEMESTERS)
            db.add(StudentDiscipline(
                student_id=stu.id,
                discipline_date=rand_date_in_semester(sem),
                discipline_type=random.choice(['警告','严重警告','记过']),
                level=random.choice(['院级','校级']),
                reason=random.choice(['宿舍违规使用大功率电器','旷课累计超过规定','考试违纪']),
                attachment='', notes='',
            ))
            stats['disciplines'] += 1

        # 寝谈：两个学期
        for stu in random.sample(all_students, k=int(len(all_students) * 0.3)):
            for sem in SEMESTERS:
                db.add(StudentDormChat(
                    student_id=stu.id,
                    chat_date=rand_date_in_semester(sem),
                    topic=random.choice(['学习规划','职业发展','宿舍关系','假期安排']),
                    key_points='深入沟通',
                    follow_up='后续跟进',
                ))
                stats['dorm_chats'] += 1

        # 考勤异常：两个学期
        for stu in random.sample(all_students, k=int(len(all_students) * 0.25)):
            for sem in SEMESTERS:
                for _ in range(random.randint(1, 3)):
                    db.add(StudentAttendanceException(
                        student_id=stu.id,
                        exception_date=rand_date_in_semester(sem),
                        course_name=random.choice(
                            COURSE_POOL_SEM1 if sem == '2025-2026-1' else COURSE_POOL_SEM2
                        )[0],
                        exception_type=random.choice(['迟到','早退','旷课']),
                        notes='',
                    ))
                    stats['attendance'] += 1
        db.commit()

        # ═══════════════ 17. 学籍异动 ═══════════════
        stats['status_changes'] = 0
        for stu in random.sample(all_students, k=int(len(all_students) * 0.03)):
            change_type = random.choice(['休学','参军','转专业'])
            sem = random.choice(SEMESTERS)
            sem_start, sem_end = SEM_DATES[sem]
            sdate = rand_date_in_range(sem_start, sem_end - timedelta(days=30))
            edate = rand_date_in_range(date.fromisoformat(sdate), sem_end)
            db.add(StudentStatusChange(
                student_id=stu.id, change_type=change_type,
                start_date=sdate, end_date=edate,
                reason='个人原因', original_info='原班级', target_info='新班级',
                attachment='', notes='',
            ))
            stats['status_changes'] += 1
        db.commit()

        # ═══════════════ 18. 班会 ═══════════════
        stats['meetings'] = 0
        topics_pool = ['新学期规划','期末考试动员','安全教育','宿舍卫生检查','诚信考试','心理健康','奖学金评定','党团学习','假期安全','学习方法交流']
        for cobj in classes:
            # 学期1：3-4 次班会
            sem1_start, sem1_end = SEM_DATES['2025-2026-1']
            for _ in range(random.randint(3, 4)):
                mdate = rand_date_in_range(sem1_start + timedelta(days=14), sem1_end)
                _monitor = cobj.monitor or '班长'
                _host_pool = [cobj.class_teacher or '班主任', _monitor]
                _rec_pool = [cobj.league_secretary or '团支书', _monitor]
                db.add(ClassMeeting(
                    class_id=cobj.id, meeting_date=mdate,
                    topic=random.choice(topics_pool),
                    attendance_count=random.randint(30, 45), absent_students='',
                    content_summary='本次班会内容涉及学期重点工作',
                    resolution='已布置任务',
                    host=random.choice(_host_pool),
                    recorder=random.choice(_rec_pool),
                    notes='全体到会情况良好',
                ))
                stats['meetings'] += 1
            # 学期2：3-4 次班会
            sem2_start, sem2_end = SEM_DATES['2025-2026-2']
            for _ in range(random.randint(3, 4)):
                mdate = rand_date_in_range(sem2_start + timedelta(days=14), sem2_end)
                _monitor = cobj.monitor or '班长'
                _host_pool = [cobj.class_teacher or '班主任', _monitor]
                _rec_pool = [cobj.league_secretary or '团支书', _monitor]
                db.add(ClassMeeting(
                    class_id=cobj.id, meeting_date=mdate,
                    topic=random.choice(topics_pool),
                    attendance_count=random.randint(30, 45), absent_students='',
                    content_summary='本次班会内容涉及学期重点工作',
                    resolution='已布置任务',
                    host=random.choice(_host_pool),
                    recorder=random.choice(_rec_pool),
                    notes='全体到会情况良好',
                ))
                stats['meetings'] += 1
        db.commit()

        # ═══════════════ 19. 党团学习 ═══════════════
        stats['party_study'] = 0
        if all_students:
            # 学期1：7-8 次
            sem1_start, sem1_end = SEM_DATES['2025-2026-1']
            for _ in range(random.randint(7, 8)):
                sdate = rand_date_in_range(sem1_start, sem1_end)
                ps = PartyStudy(
                    study_type=random.choice(['主题党日','团日活动','党课学习','支部会议']),
                    study_date=sdate,
                    topic=random.choice(['学习二十大精神','党史学习教育','青年责任担当','雷锋精神传承','新时代青年使命']),
                    content_summary='集体学习并展开研讨', report_points='',
                )
                ps.students = random.sample(all_students, k=min(random.randint(5, 10), len(all_students)))
                db.add(ps); stats['party_study'] += 1
            # 学期2：7-8 次
            sem2_start, sem2_end = SEM_DATES['2025-2026-2']
            for _ in range(random.randint(7, 8)):
                sdate = rand_date_in_range(sem2_start, sem2_end)
                ps = PartyStudy(
                    study_type=random.choice(['主题党日','团日活动','党课学习','支部会议']),
                    study_date=sdate,
                    topic=random.choice(['两会精神学习','庆祝建党纪念日','脱贫攻坚成就','改革开放再出发','青年学子担当']),
                    content_summary='集体学习并展开研讨', report_points='',
                )
                ps.students = random.sample(all_students, k=min(random.randint(5, 10), len(all_students)))
                db.add(ps); stats['party_study'] += 1
            db.commit()

        # ═══════════════ 20. Setting / Tags / 知识库 / FAQ / 模板 ═══════════════
        for k, v in [('fail_course_threshold', '2'), ('gpa_drop_threshold', '0.5')]:
            if not db.query(Setting).filter(Setting.key == k).first():
                db.add(Setting(key=k, value=v))

        for group, names in {
            '政治面貌': ['群众','共青团员','积极分子','党员'],
            '学业状态': ['优秀','良好','观察','预警'],
            '资助类别': ['特困','困难','一般','无'],
            '学生干部': ['班长','团支书','学习委员','其他委员'],
        }.items():
            for n in names:
                if not db.query(Tag).filter(Tag.name == n, Tag.group_name == group).first():
                    db.add(Tag(name=n, group_name=group, color='#4A7A8C'))
        db.commit()
        stats['tags'] = db.query(Tag).count()

        if db.query(KnowledgeDoc).count() < 3:
            db.add_all([
                KnowledgeDoc(title='学生手册（2026版）', doc_type='markdown', content='# 学生手册\n\n## 第一章 总则\n本手册适用于全体在校学生。'),
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

        # ═══════════════ 21. 专项工作 ═══════════════
        if db.query(Project).count() < 1:
            proj = Project(
                name='2025级新生学业适应帮扶专项',
                start_date='2025-09-15', end_date='2026-07-15',
                status='active', progress=60,
                description='精准对接学业困难新生',
            )
            db.add(proj); db.flush()
            for stu in random.sample(all_students, k=min(20, len(all_students))):
                db.add(ProjectStudent(project_id=proj.id, student_id=stu.id, notes=''))
            db.commit()

        logger.info(f'[seed_large] 完成 {stats}')

        # ═══════════════ 最终校验 ═══════════════
        _validate_data(db)

        return stats
    except Exception as e:
        db.rollback()
        logger.exception(f'[seed_large] 失败: {e}')
        raise
    finally:
        db.close()


def _validate_data(db):
    """校验所有业务日期和学期字段"""
    errors = []

    def _check_date(d, label):
        if not d:
            return
        try:
            dd = date.fromisoformat(d)
        except Exception:
            errors.append(f'{label}: 非法日期 {d}')
            return
        if dd < MIN_DATE or dd > MAX_DATE:
            errors.append(f'{label}: 日期 {d} 超出范围 [{MIN_DATE}~{MAX_DATE}]')

    def _check_semester(s, label):
        if s and s not in SEMESTERS:
            errors.append(f'{label}: 非法学期 {s}')

    # 成绩
    for r in db.query(GradeRecord).all():
        _check_semester(r.semester, f'GradeRecord#{r.id}')
    # 预警
    for r in db.query(WarningRecord).all():
        _check_semester(r.semester, f'WarningRecord#{r.id}')
    # 综测
    for r in db.query(ComprehensiveAssessment).all():
        _check_semester(r.semester, f'ComprehensiveAssessment#{r.id}')
    # 干部
    for r in db.query(StudentCadreRecord).all():
        _check_date(r.start_date, f'CadreRecord#{r.id} start_date')
        _check_date(r.end_date, f'CadreRecord#{r.id} end_date')
    # 访谈
    for r in db.query(StudentInterview).all():
        _check_date(r.interview_date, f'Interview#{r.id} interview_date')
        _check_date(r.remind_date, f'Interview#{r.id} remind_date')
    # 党团
    for r in db.query(PartyProgress).all():
        _check_date(r.stage_date, f'PartyProgress#{r.id} stage_date')
    # 心理
    for r in db.query(PsychologyRecord).all():
        _check_date(r.record_date, f'PsychologyRecord#{r.id} record_date')
        _check_date(r.next_follow_date, f'PsychologyRecord#{r.id} next_follow_date')
    # 家校
    for r in db.query(FamilyContact).all():
        _check_date(r.contact_date, f'FamilyContact#{r.id} contact_date')
    # 活动
    for r in db.query(Activity).all():
        _check_date(r.activity_date, f'Activity#{r.id} activity_date')
        _check_date(r.end_date, f'Activity#{r.id} end_date')
    # 宿舍走访
    for r in db.query(StudentDormVisit).all():
        _check_date(r.visit_date, f'DormVisit#{r.id} visit_date')
    # 请假
    for r in db.query(StudentLeave).all():
        _check_date(r.start_date, f'Leave#{r.id} start_date')
        _check_date(r.end_date, f'Leave#{r.id} end_date')
    # 违纪
    for r in db.query(StudentDiscipline).all():
        _check_date(r.discipline_date, f'Discipline#{r.id} discipline_date')
    # 寝谈
    for r in db.query(StudentDormChat).all():
        _check_date(r.chat_date, f'DormChat#{r.id} chat_date')
    # 考勤
    for r in db.query(StudentAttendanceException).all():
        _check_date(r.exception_date, f'AttendanceException#{r.id} exception_date')
    # 学籍异动
    for r in db.query(StudentStatusChange).all():
        _check_date(r.start_date, f'StatusChange#{r.id} start_date')
        _check_date(r.end_date, f'StatusChange#{r.id} end_date')
    # 班会
    for r in db.query(ClassMeeting).all():
        _check_date(r.meeting_date, f'ClassMeeting#{r.id} meeting_date')
    # 党团学习
    for r in db.query(PartyStudy).all():
        _check_date(r.study_date, f'PartyStudy#{r.id} study_date')
    # 就业
    for r in db.query(EmploymentRecord).all():
        _check_date(r.offer_date, f'EmploymentRecord#{r.id} offer_date')

    # 学生入党日期
    for r in db.query(Student).all():
        if r.join_party_date:
            _check_date(r.join_party_date, f'Student#{r.id} join_party_date')

    if errors:
        print('=== 校验失败 ===')
        for e in errors[:50]:
            print(f'  {e}')
        if len(errors) > 50:
            print(f'  ... 共 {len(errors)} 条错误')
        assert False, f'数据校验失败，共 {len(errors)} 条错误'
    else:
        print('=== 数据校验通过：所有日期在 2025-09-01~2026-07-31，所有学期合法 ===')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    Base.metadata.create_all(bind=engine)
    print(seed_large_dataset())
