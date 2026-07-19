"""
AI 智能数据导入 - 两步式：detect(预览) + confirm(确认写入)
支持 10 种数据类型：students / grades / party / hardship / scholarship / honor / family / cadre / activity / employment
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/import', tags=['智能导入'])

# ============ 列名同义词映射表（10 种类型） ============

STUDENT_COLUMN_SYNONYMS = {
    'student_no': ['学号', '学生编号', '学生号', '编号', 'student_no', 'student_id'],
    'name': ['姓名', '学生姓名', '名字', '名', 'name', '学生名'],
    'gender': ['性别', '男女', 'sex', 'gender'],
    'major': ['专业', '所学专业', '专业名称', 'major', '院系', '学院'],
    'class_name': ['班级', '所在班级', '班级号', '班级名称', 'class_name', '班名'],
    'birth_date': ['出生日期', '出生年月', '生日', 'birth_date', 'birthday'],
    'political_status': ['政治面貌', '政治身份', 'political_status'],
    'phone': ['联系电话', '手机号', '电话', 'phone', 'tel', '手机号码'],
    'parent_phone': ['家长电话', '紧急联系电话', '家庭联系方式', '家长联系方式', 'parent_phone'],
    'email': ['邮箱', '电子邮箱', 'email', '邮件'],
    'birth_source': ['生源地', '籍贯', '生源省份', '生源', 'birth_source'],
    'id_card': ['身份证', '身份证号', '身份证号码', '证件号', 'id_card', 'idcard', 'id_number'],
    'campus': ['校区', 'campus'],
    'dorm_building': ['宿舍楼', '宿舍', '楼栋', 'dorm_building'],
    'dorm_room': ['宿舍号', '房间号', '寝室号', '门牌号', 'dorm_room', 'room'],
    'is_off_campus': ['是否外宿', '外宿', 'off_campus', 'is_off_campus'],
    'off_campus_address': ['外宿地址', '校外住址', 'off_campus_address'],
    'notes': ['备注', '说明', 'notes', 'remark'],
}

GRADE_COLUMN_SYNONYMS = {
    'student_no': ['学号', '学生编号', '学生号', '编号', 'student_no'],
    'name': ['姓名', '学生姓名', '名字', 'name'],
    'semester': ['学期', '开课学期', '学年学期', 'semester', 'term'],
    'course_name': ['课程名', '课程名称', '课程', '科目', '科目名称', '课名', 'course', 'course_name'],
    'score': ['分数', '成绩', '得分', '总分', '考试成绩', 'score', 'total_score'],
    'gpa': ['绩点', 'GPA', 'gpa', '学分绩点'],
    'credit': ['学分', 'credit', 'credits'],
    'is_repair': ['重修', '是否重修', 'is_repair', 'is_makeup', '补修', '是否补修'],
}

PARTY_COLUMN_SYNONYMS = {
    'student_no': ['学号', '学生编号', '编号', 'student_no'],
    'name': ['姓名', '学生姓名', '名字', 'name'],
    'class_name': ['班级', '所在班级', 'class_name'],
    'stage': ['阶段', '发展', '当前阶段', 'stage'],
    'stage_date': ['阶段日期', '日期', 'stage_date'],
    'contact_person': ['联系人', '经办人', '培养联系人', 'contact_person'],
    'notes': ['备注', '说明', 'notes'],
}

# V5-c 新增 7 种类型的同义词映射

HARDSHIP_COLUMN_SYNONYMS = {
    'student_no': ['学号', '学生编号', '编号', 'student_no'],
    'hardship_level': ['困难等级', '困难程度', '认定等级', 'hardship_level', 'level'],
    'school_year': ['学年', '认定学年', '学年年度', 'school_year', 'academic_year', 'year'],
    'family_situation': ['家庭情况', '家庭状况', 'family_situation', '家庭信息'],
    'family_income': ['家庭收入', '年收入', 'family_income', '家庭年收入'],
    'per_capita_income': ['人均收入', '人均年收入', 'per_capita_income'],
    'hardship_type': ['困难类型', '困难类别', 'hardship_type', '类型'],
}

SCHOLARSHIP_COLUMN_SYNONYMS = {
    'student_no': ['学号', '学生编号', '编号', 'student_no'],
    'scholarship_name': ['奖学金名称', '奖项名称', '奖学金', 'scholarship_name', 'grant_name'],
    'level': ['级别', '等级', '层次', 'level', '奖学金等级'],
    'amount': ['金额', '奖金', '额度', 'amount', 'award_amount'],
    'school_year': ['学年', '评奖学年', 'school_year', 'academic_year'],
    'semester': ['学期', 'semester'],
}

HONOR_COLUMN_SYNONYMS = {
    'student_no': ['学号', '学生编号', '编号', 'student_no'],
    'honor_name': ['荣誉名称', '奖项名称', '荣誉称号', 'honor_name', 'award_name'],
    'honor_level': ['荣誉级别', '获奖级别', '级别', 'honor_level', 'award_level'],
    'award_date': ['获奖日期', '颁发日期', 'award_date', '日期'],
    'granting_org': ['授予单位', '颁发单位', '授予机构', 'granting_org', 'org'],
}

FAMILY_COLUMN_SYNONYMS = {
    'student_no': ['学号', '学生编号', '编号', 'student_no'],
    'parent_name': ['家长姓名', '联系人姓名', 'parent_name', '家长'],
    'relationship': ['关系', '与家长关系', 'relationship', '亲属关系'],
    'parent_phone': ['家长电话', '联系电话', 'parent_phone', '联系方式'],
    'contact_date': ['联系日期', '沟通日期', 'contact_date', '日期'],
    'contact_method': ['联系方式', '沟通方式', 'contact_method', '方式'],
    'topic': ['沟通主题', '主题', 'topic', '谈话内容'],
}

CADRE_COLUMN_SYNONYMS = {
    'student_no': ['学号', '学生编号', '编号', 'student_no'],
    'position': ['职务', '职位', '岗位', 'position', '干部职务'],
    'org_name': ['组织名称', '所在组织', '部门', 'org_name', 'organization'],
    'start_date': ['任职起始', '开始日期', 'start_date', '起始日期'],
    'end_date': ['任职结束', '结束日期', 'end_date', '终止日期'],
    'status': ['状态', '任职状态', 'status', '在职状态'],
}

ACTIVITY_COLUMN_SYNONYMS = {
    'student_no': ['学号', '学生编号', '编号', 'student_no'],
    'activity_name': ['活动名称', '活动', 'activity_name', '活动标题'],
    'activity_date': ['活动日期', '日期', 'activity_date', '参加日期'],
    'role': ['角色', '参与角色', 'role', '身份'],
    'hours': ['志愿时长', '时长', 'hours', '服务时长', '工时'],
}

EMPLOYMENT_COLUMN_SYNONYMS = {
    'student_no': ['学号', '学生编号', '编号', 'student_no'],
    'company_name': ['单位名称', '公司名称', 'company_name', '就业单位', '实习单位'],
    'job_title': ['岗位', '职位', 'job_title', '工作岗位', '职务'],
    'employment_type': ['就业类型', '去向类型', 'employment_type', '就业去向', '类型'],
    'offer_date': ['签约日期', '录用日期', 'offer_date', '入职日期'],
    'salary': ['薪资', '月薪', '薪酬', 'salary', '薪资范围'],
}

# 按类型索引同义词表
ALL_SYNONYMS = {
    'students': STUDENT_COLUMN_SYNONYMS,
    'grades': GRADE_COLUMN_SYNONYMS,
    'party': PARTY_COLUMN_SYNONYMS,
    'hardship': HARDSHIP_COLUMN_SYNONYMS,
    'scholarship': SCHOLARSHIP_COLUMN_SYNONYMS,
    'honor': HONOR_COLUMN_SYNONYMS,
    'family': FAMILY_COLUMN_SYNONYMS,
    'cadre': CADRE_COLUMN_SYNONYMS,
    'activity': ACTIVITY_COLUMN_SYNONYMS,
    'employment': EMPLOYMENT_COLUMN_SYNONYMS,
}

# 数据库字段中文名（用于展示）
DB_FIELD_NAMES = {
    # 学生
    'student_no': '学号', 'name': '姓名', 'gender': '性别', 'major': '专业',
    'class_name': '班级', 'birth_date': '出生日期', 'political_status': '政治面貌',
    'phone': '联系电话', 'parent_phone': '家长电话', 'email': '邮箱',
    'birth_source': '生源地', 'notes': '备注',
    'id_card': '身份证号', 'campus': '校区', 'dorm_building': '宿舍楼',
    'dorm_room': '房间号', 'is_off_campus': '是否外宿', 'off_campus_address': '外宿地址',
    # 成绩
    'semester': '学期', 'course_name': '课程名', 'score': '分数', 'gpa': '绩点', 'credit': '学分',
    'is_repair': '是否重修',
    # 党团
    'stage': '阶段', 'stage_date': '阶段日期', 'contact_person': '联系人',
    # 困难认定
    'hardship_level': '困难等级', 'school_year': '学年',
    'family_situation': '家庭情况', 'family_income': '家庭收入',
    'per_capita_income': '人均收入', 'hardship_type': '困难类型',
    # 奖助学金
    'scholarship_name': '奖学金名称', 'level': '级别', 'amount': '金额',
    # 评优荣誉
    'honor_name': '荣誉名称', 'honor_level': '荣誉级别',
    'award_date': '获奖日期', 'granting_org': '授予单位',
    # 家庭联络
    'relationship': '关系', 'contact_date': '联系日期',
    'contact_method': '联系方式', 'topic': '主题',
    # 学生干部
    'position': '职务', 'org_name': '组织名称',
    'start_date': '任职起始', 'end_date': '任职结束', 'status': '状态',
    # 学生活动
    'activity_name': '活动名称', 'activity_date': '活动日期',
    'role': '角色', 'hours': '志愿时长',
    # 就业跟踪
    'company_name': '单位名称', 'job_title': '岗位',
    'employment_type': '就业类型', 'offer_date': '签约日期', 'salary': '薪资',
}


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """清洗 DataFrame：跳过说明行、空行、汇总行"""
    # 1. 找到真正的列名行（包含最多非空字符串的行）
    best_row_idx = 0
    best_score = 0
    for i in range(min(10, len(df))):  # 只检查前10行
        row = df.iloc[i]
        score = sum(1 for v in row if isinstance(v, str) and len(v.strip()) > 1 and not v.strip().isdigit())
        if score > best_score:
            best_score = score
            best_row_idx = i

    # 2. 用找到的行作为列名
    header_row = df.iloc[best_row_idx]
    df = df.iloc[best_row_idx + 1:].reset_index(drop=True)
    df.columns = [str(h).strip() for h in header_row.values]

    # 3. 删除全空行
    df = df.dropna(how='all')
    df = df[df.apply(lambda row: any(str(v).strip() != '' for v in row), axis=1)]

    # 4. 删除汇总行
    summary_keywords = ['合计', '总计', '汇总', '统计', '小计', '平均']
    mask = df.apply(lambda row: not any(
        kw in str(v) for v in row for kw in summary_keywords
    ), axis=1)
    df = df[mask].reset_index(drop=True)

    return df


def map_columns(columns: List[str], synonyms: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """列名映射：同义词匹配"""
    mapping = []
    used_db_fields = set()
    for col in columns:
        col_clean = str(col).strip()
        matched_db_field = None
        best_alias_len = 0
        for db_field, alias_list in synonyms.items():
            if db_field in used_db_fields:
                continue
            for alias in alias_list:
                if col_clean == alias:
                    matched_db_field = db_field
                    best_alias_len = len(alias)
                    break
                elif (alias in col_clean or col_clean in alias) and len(alias) > best_alias_len:
                    matched_db_field = db_field
                    best_alias_len = len(alias)
            if matched_db_field and best_alias_len == len(col_clean):
                break
        mapping.append({
            'file_column': col_clean,
            'db_column': matched_db_field,
            'db_field_name': DB_FIELD_NAMES.get(matched_db_field, '') if matched_db_field else '',
        })
        if matched_db_field:
            used_db_fields.add(matched_db_field)
    return mapping


def detect_file_type(df: pd.DataFrame, mapping: List[Dict]) -> str:
    """自动识别文件属于 10 种类型中的哪一种（根据列名关键词判断）"""
    mapped_fields = {m['db_column'] for m in mapping if m['db_column']}
    all_columns_str = ' '.join(str(c) for c in df.columns)

    # ---- 优先匹配特殊类型（关键词优先级高） ----

    # 困难认定：困难等级 / 困难类型 / 家庭收入
    hardship_kw = ['困难等级', '困难程度', '困难类型', '家庭收入', '人均收入',
                   'hardship_level', 'hardship_type', 'family_income']
    if any(kw in all_columns_str for kw in hardship_kw) or 'hardship_level' in mapped_fields:
        return 'hardship'

    # 奖助学金：奖学金名称 / 金额
    scholarship_kw = ['奖学金名称', '奖项名称', '奖学金', 'hardship']
    if any(kw in all_columns_str for kw in ['奖学金名称', '奖项名称']) or 'scholarship_name' in mapped_fields:
        return 'scholarship'

    # 评优荣誉：荣誉名称 / 授予单位
    honor_kw = ['荣誉名称', '荣誉称号', '授予单位', '颁发单位']
    if any(kw in all_columns_str for kw in honor_kw) or 'honor_name' in mapped_fields:
        return 'honor'

    # 家庭联络：家长姓名 / 联系日期 / 沟通方式
    family_kw = ['家长姓名', '联系人姓名', '联系日期', '沟通方式', '沟通主题']
    if any(kw in all_columns_str for kw in family_kw) or ('parent_name' in mapped_fields and 'contact_date' in mapped_fields):
        return 'family'

    # 学生干部：职务 / 任职起始
    cadre_kw = ['职务', '任职起始', '干部职务', '所在组织']
    if any(kw in all_columns_str for kw in cadre_kw) or ('position' in mapped_fields and 'org_name' in mapped_fields):
        return 'cadre'

    # 学生活动：活动名称 / 志愿时长 / 参与角色
    activity_kw = ['活动名称', '志愿时长', '参与角色', '服务时长']
    if any(kw in all_columns_str for kw in activity_kw) or 'activity_name' in mapped_fields:
        return 'activity'

    # 就业跟踪：单位名称 / 就业类型 / 签约日期
    employment_kw = ['单位名称', '公司名称', '就业类型', '就业去向', '签约日期', '录用日期']
    if any(kw in all_columns_str for kw in employment_kw) or 'company_name' in mapped_fields:
        return 'employment'

    # ---- 通用类型 ----

    # 成绩单：有学号+姓名+多个数值列
    if 'student_no' in mapped_fields and 'name' in mapped_fields:
        unmapped_cols = [m['file_column'] for m in mapping if not m['db_column']]
        if len(unmapped_cols) >= 3:
            numeric_count = 0
            for col in unmapped_cols:
                if col in df.columns:
                    try:
                        vals = pd.to_numeric(df[col], errors='coerce')
                        if vals.notna().sum() > 0:
                            numeric_count += 1
                    except:
                        pass
            if numeric_count >= 3:
                return 'grades'

    # 党团发展表：有阶段相关字段
    party_keywords = ['阶段', '发展', '积极分子', '预备党员', '中共预备党员', '中共党员', '党员', '团员']
    for col in df.columns:
        if any(kw in str(col) for kw in party_keywords):
            return 'party'
    if 'stage' in mapped_fields:
        return 'party'

    return 'students'


# ============ 存储待确认的导入数据（内存） ============
_pending_imports: Dict[str, Dict[str, Any]] = {}


class ConfirmRequest(BaseModel):
    data_type: str
    mapping: List[Dict[str, Any]]
    conflict_strategy: str = 'skip'  # skip / overwrite / keep_both
    import_id: Optional[str] = None


@router.post('/detect')
async def detect_file(file: UploadFile = File(...)):
    """第一步：上传文件，AI 识别类型 + 列名映射 + 数据预览"""
    content = await file.read()
    filename = file.filename or ''
    logger.info(f"[导入检测] 文件名={filename}, 大小={len(content)} bytes")

    # 解析文件
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content), dtype=str, header=None).fillna('')
        else:
            df = pd.read_excel(io.BytesIO(content), dtype=str, header=None).fillna('')
    except Exception as e:
        logger.exception(f"[导入检测] 文件解析失败: {e}")
        raise HTTPException(400, f'文件解析失败: {str(e)}')

    if len(df) == 0:
        raise HTTPException(400, '文件为空')

    # 清洗数据
    df = clean_dataframe(df)

    if len(df) == 0:
        raise HTTPException(400, '清洗后无有效数据行')

    # 先用学生同义词做初步映射以检测类型
    columns = list(df.columns)
    mapping = map_columns(columns, STUDENT_COLUMN_SYNONYMS)

    # 识别文件类型
    data_type = detect_file_type(df, mapping)

    # 根据检测到的类型，用对应的同义词表重新映射
    synonym_table = ALL_SYNONYMS.get(data_type, STUDENT_COLUMN_SYNONYMS)
    mapping = map_columns(columns, synonym_table)

    # 成绩单智能兜底：未映射且是数值型的列，自动当作课程列
    if data_type == 'grades':
        mapped_file_cols = {m['file_column'] for m in mapping if m.get('db_column')}
        for col in df.columns:
            if col in mapped_file_cols:
                continue
            try:
                vals = pd.to_numeric(df[col], errors='coerce')
                if vals.notna().sum() >= 3:
                    mapping.append({
                        'file_column': str(col).strip(),
                        'db_column': f'course:{str(col).strip()}',
                        'db_field_name': f'课程：{str(col).strip()}',
                    })
            except Exception:
                pass

    # 数据预览
    rows = df.head(5).to_dict(orient='records')
    for r in rows:
        for k, v in r.items():
            r[k] = str(v) if v != '' else ''

    # 重复学号检测
    duplicate_count = 0
    if 'student_no' in df.columns:
        vals = df['student_no'].dropna().astype(str).str.strip()
        duplicate_count = int(vals.duplicated().sum())

    suggested_mapping = [
        {'file_column': m['file_column'], 'db_column': m['db_column'] or '', 'db_field_name': m.get('db_field_name', '')}
        for m in mapping
    ]
    samples = rows

    # 生成 import_id 并缓存
    import_id = f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(df) % 100000:05d}"
    _pending_imports[import_id] = {
        'dataframe': df,
        'data_type': data_type,
        'columns': columns,
        'mapping': mapping,
        'created_at': datetime.now().isoformat(),
    }

    logger.info(f"[导入检测] 类型={data_type}, import_id={import_id}, 行数={len(df)}")

    return {
        'import_id': import_id,
        'data_type': data_type,
        'type_label': DB_FIELD_NAMES.get(data_type, data_type),
        'columns': columns,
        'mapping': suggested_mapping,
        'suggested_mapping': suggested_mapping,
        'samples': samples,
        'preview_data': rows,
        'preview': rows,
        'total_rows': len(df),
        'valid_rows': len(df),
        'duplicate_count': duplicate_count,
        'warnings': [],
    }


@router.post('/confirm')
async def confirm_import(req: ConfirmRequest):
    """第二步：确认导入，写入数据库"""
    from database import SessionLocal
    from models import (
        Student, GradeRecord, PartyProgress,
        StudentHardship, StudentScholarship, StudentHonor,
        FamilyContact, StudentCadreRecord, ActivitySignup, Activity,
        EmploymentRecord
    )

    import_id = req.import_id
    if not import_id or import_id not in _pending_imports:
        raise HTTPException(400, '导入数据已过期，请重新上传文件')

    pending = _pending_imports.pop(import_id)
    df = pending['dataframe']
    data_type = pending['data_type']
    mapping = req.mapping
    logger.info(f"[导入确认] 开始, import_id={import_id}, 类型={data_type}, 数据行数={len(df)}")

    # 构建列名映射字典
    col_map = {}
    course_columns = []
    for m in mapping:
        if m.get('db_column'):
            if m['db_column'].startswith('course:'):
                course_columns.append((m['file_column'], m['db_column'].replace('course:', '')))
            else:
                col_map[m['db_column']] = m['file_column']

    # 成绩单智能兜底
    if data_type == 'grades':
        mapped_file_cols = {m['file_column'] for m in mapping if m.get('db_column')}
        for col in df.columns:
            if col in mapped_file_cols:
                continue
            try:
                vals = pd.to_numeric(df[col], errors='coerce')
                if vals.notna().sum() >= 3:
                    course_columns.append((col, str(col).strip()))
                    logger.info(f'[导入] 自动识别课程列: {col}')
            except Exception:
                pass

    db = SessionLocal()
    created = 0
    skipped = 0
    updated = 0

    def _val(row, field):
        """从行中根据 col_map 取字段值"""
        col = col_map.get(field, '')
        if col and col in row.index:
            return str(row[col]).strip()
        return ''

    try:
        if data_type == 'students':
            # ---------- Student 直属字段 ----------
            STUDENT_DIRECT_FIELDS = ['gender', 'birth_date', 'political_status',
                                     'phone', 'parent_phone', 'email', 'birth_source', 'notes']
            from models import Grade as GradeOrg, Major, ClassModel

            def resolve_class_id(row):
                cn = _val(row, 'class_name')
                mj = _val(row, 'major')
                gd = _val(row, 'grade') if 'grade' in col_map else ''
                if not cn:
                    return None
                existing = db.query(ClassModel).filter(ClassModel.class_name == cn).first()
                if existing:
                    return existing.id
                if not gd:
                    m = re.search(r'(\d{2})\d{2}', cn)
                    if m:
                        yy = int(m.group(1))
                        gd = f'{2000 + yy}级'
                if not gd:
                    gd = '未分年级'
                if not mj:
                    mj = '未分专业'
                grade_obj = db.query(GradeOrg).filter(GradeOrg.grade_name == gd).first()
                if not grade_obj:
                    start_year = 2000
                    m = re.search(r'(\d{4})', gd)
                    if m:
                        start_year = int(m.group(1))
                    grade_obj = GradeOrg(grade_name=gd, start_year=start_year)
                    db.add(grade_obj)
                    db.flush()
                major_obj = db.query(Major).filter(Major.major_name == mj, Major.grade_id == grade_obj.id).first()
                if not major_obj:
                    major_obj = Major(major_name=mj, grade_id=grade_obj.id)
                    db.add(major_obj)
                    db.flush()
                new_class = ClassModel(class_name=cn, major_id=major_obj.id)
                db.add(new_class)
                db.flush()
                return new_class.id

            for _, row in df.iterrows():
                student_no = _val(row, 'student_no')
                name = _val(row, 'name')
                if not student_no or not name:
                    skipped += 1
                    continue
                existing = db.query(Student).filter(Student.student_no == student_no).first()
                if existing:
                    if req.conflict_strategy == 'skip':
                        skipped += 1
                        continue
                    elif req.conflict_strategy == 'overwrite':
                        existing.name = name
                        for field in STUDENT_DIRECT_FIELDS:
                            v = _val(row, field)
                            if v:
                                setattr(existing, field, v)
                        cid = resolve_class_id(row)
                        if cid:
                            existing.class_id = cid
                        updated += 1
                    else:
                        skipped += 1
                else:
                    student = Student(student_no=student_no, name=name)
                    for field in STUDENT_DIRECT_FIELDS:
                        v = _val(row, field)
                        if v:
                            setattr(student, field, v)
                    cid = resolve_class_id(row)
                    if cid:
                        student.class_id = cid
                    db.add(student)
                    created += 1

        elif data_type == 'grades':
            semester_col = col_map.get('semester', '')
            for _, row in df.iterrows():
                student_no = _val(row, 'student_no')
                if not student_no:
                    skipped += 1
                    continue
                student = db.query(Student).filter(Student.student_no == student_no).first()
                if not student:
                    skipped += 1
                    continue
                semester = str(row.get(semester_col, '')).strip() if semester_col else ''
                for course_col, course_name in course_columns:
                    score_val = row.get(course_col, '')
                    try:
                        score = float(score_val) if score_val != '' else None
                    except (ValueError, TypeError):
                        score = None
                    if score is not None:
                        grade = GradeRecord(
                            student_id=student.id,
                            semester=semester or '未指定学期',
                            course_name=course_name,
                            score=score,
                            gpa=score / 25 if score <= 100 else None,
                            credit=1.0,
                        )
                        db.add(grade)
                        created += 1
            from routers.grades import recalculate_warnings
            recalculate_warnings(db)

        elif data_type == 'party':
            for _, row in df.iterrows():
                student_no = _val(row, 'student_no')
                if not student_no:
                    skipped += 1
                    continue
                student = db.query(Student).filter(Student.student_no == student_no).first()
                if not student:
                    skipped += 1
                    continue
                stage = _val(row, 'stage')
                if stage:
                    progress = PartyProgress(
                        student_id=student.id,
                        stage=stage,
                        stage_date=_val(row, 'stage_date') or None,
                        contact_person=_val(row, 'contact_person'),
                        notes=_val(row, 'notes'),
                    )
                    db.add(progress)
                    created += 1

        # ===== V5-c 新增 7 种类型 =====

        elif data_type == 'hardship':
            # 困难认定 → StudentHardship
            for _, row in df.iterrows():
                student_no = _val(row, 'student_no')
                if not student_no:
                    skipped += 1
                    continue
                student = db.query(Student).filter(Student.student_no == student_no).first()
                if not student:
                    skipped += 1
                    continue
                hardship = StudentHardship(
                    student_id=student.id,
                    hardship_level=_val(row, 'hardship_level'),
                    academic_year=_val(row, 'school_year'),
                    evidence=_val(row, 'family_situation'),
                    notes=f"家庭收入:{_val(row, 'family_income')} | 人均收入:{_val(row, 'per_capita_income')} | 困难类型:{_val(row, 'hardship_type')}",
                )
                db.add(hardship)
                created += 1

        elif data_type == 'scholarship':
            # 奖助学金 → StudentScholarship
            for _, row in df.iterrows():
                student_no = _val(row, 'student_no')
                if not student_no:
                    skipped += 1
                    continue
                student = db.query(Student).filter(Student.student_no == student_no).first()
                if not student:
                    skipped += 1
                    continue
                amount_str = _val(row, 'amount')
                try:
                    amount_val = float(amount_str) if amount_str else 0
                except (ValueError, TypeError):
                    amount_val = 0
                scholarship = StudentScholarship(
                    student_id=student.id,
                    scholarship_type=_val(row, 'scholarship_name'),
                    amount=amount_val,
                    academic_year=_val(row, 'school_year'),
                    notes=f"级别:{_val(row, 'level')} | 学期:{_val(row, 'semester')}",
                )
                db.add(scholarship)
                created += 1

        elif data_type == 'honor':
            # 评优荣誉 → StudentHonor
            for _, row in df.iterrows():
                student_no = _val(row, 'student_no')
                if not student_no:
                    skipped += 1
                    continue
                student = db.query(Student).filter(Student.student_no == student_no).first()
                if not student:
                    skipped += 1
                    continue
                honor = StudentHonor(
                    student_id=student.id,
                    honor_name=_val(row, 'honor_name'),
                    level=_val(row, 'honor_level'),
                    academic_year=_val(row, 'award_date'),  # 用 award_date 暂存学年信息
                    notes=f"获奖日期:{_val(row, 'award_date')} | 授予单位:{_val(row, 'granting_org')}",
                )
                db.add(honor)
                created += 1

        elif data_type == 'family':
            # 家庭联络 → FamilyContact
            for _, row in df.iterrows():
                student_no = _val(row, 'student_no')
                if not student_no:
                    skipped += 1
                    continue
                student = db.query(Student).filter(Student.student_no == student_no).first()
                if not student:
                    skipped += 1
                    continue
                contact = FamilyContact(
                    student_id=student.id,
                    parent_name=_val(row, 'parent_name'),
                    contact_method=_val(row, 'contact_method'),
                    contact_date=_val(row, 'contact_date'),
                    topic=_val(row, 'topic'),
                    notes=f"关系:{_val(row, 'relationship')} | 电话:{_val(row, 'parent_phone')}",
                )
                db.add(contact)
                created += 1

        elif data_type == 'cadre':
            # 学生干部 → StudentCadreRecord
            for _, row in df.iterrows():
                student_no = _val(row, 'student_no')
                if not student_no:
                    skipped += 1
                    continue
                student = db.query(Student).filter(Student.student_no == student_no).first()
                if not student:
                    skipped += 1
                    continue
                cadre = StudentCadreRecord(
                    student_id=student.id,
                    position=_val(row, 'position'),
                    organization=_val(row, 'org_name'),
                    start_date=_val(row, 'start_date'),
                    end_date=_val(row, 'end_date'),
                    notes=f"状态:{_val(row, 'status')}",
                )
                db.add(cadre)
                created += 1

        elif data_type == 'activity':
            # 学生活动 → Activity + ActivitySignup
            for _, row in df.iterrows():
                student_no = _val(row, 'student_no')
                if not student_no:
                    skipped += 1
                    continue
                student = db.query(Student).filter(Student.student_no == student_no).first()
                if not student:
                    skipped += 1
                    continue
                act_name = _val(row, 'activity_name')
                act_date = _val(row, 'activity_date')
                if not act_name:
                    skipped += 1
                    continue
                # 查找或创建活动
                activity = db.query(Activity).filter(
                    Activity.title == act_name,
                    Activity.activity_date == act_date,
                ).first()
                if not activity:
                    activity = Activity(
                        title=act_name,
                        activity_date=act_date,
                        description=f"角色:{_val(row, 'role')}",
                    )
                    db.add(activity)
                    db.flush()
                # 志愿时长存入 points 字段
                hours_str = _val(row, 'hours')
                try:
                    hours_val = int(float(hours_str)) if hours_str else 0
                except (ValueError, TypeError):
                    hours_val = 0
                signup = ActivitySignup(
                    activity_id=activity.id,
                    student_id=student.id,
                    signed_up=True,
                    checked_in=True,
                    points=hours_val,
                )
                db.add(signup)
                created += 1

        elif data_type == 'employment':
            # 就业跟踪 → EmploymentRecord
            for _, row in df.iterrows():
                student_no = _val(row, 'student_no')
                if not student_no:
                    skipped += 1
                    continue
                student = db.query(Student).filter(Student.student_no == student_no).first()
                if not student:
                    skipped += 1
                    continue
                emp = EmploymentRecord(
                    student_id=student.id,
                    internship_company=_val(row, 'company_name'),
                    target_position=_val(row, 'job_title'),
                    intention_type=_val(row, 'employment_type'),
                    offer_date=_val(row, 'offer_date'),
                    salary_range=_val(row, 'salary'),
                )
                db.add(emp)
                created += 1

        db.commit()
        logger.info(f"[导入确认] 类型={data_type}, 新增={created}, 跳过={skipped}, 更新={updated}")
    except Exception as e:
        db.rollback()
        logger.exception(f"[导入确认] 失败: {e}")
        raise HTTPException(500, f'导入失败: {str(e)}')
    finally:
        db.close()

    total = created + skipped + updated
    return {
        'success': True,
        'created': created,
        'skipped': skipped,
        'updated': updated,
        'data_type': data_type,
        'total': total,
        'total_rows': total,
        'imported': created + updated,
        'success_count': created + updated,
        'failed': skipped,
        'fail_count': skipped,
        'errors': [],
    }


@router.get('/template')
def download_template(type: str = 'students'):
    """下载导入模板 xlsx — 支持 10 种类型"""
    import io
    import pandas as pd
    from fastapi.responses import Response
    from urllib.parse import quote

    templates = {
        'students': {
            'sheet': '学生花名册模板',
            'columns': ['学号','姓名','性别','班级','专业','年级','出生日期','政治面貌',
                        '手机','邮箱','家长手机','生源地','身份证号','校区','宿舍楼',
                        '房间号','是否外宿','外宿地址','备注'],
            'example': ['20240101001','张三','男','计科2401','计算机科学与技术','2024级',
                        '2005-03-01','共青团员','13800000000','zhangsan@qq.com','13900000000',
                        '福建省·福州市·鼓楼区','350102200503010001','铜盘校区','1号楼',
                        '101','否','','示例行，请删除'],
        },
        'grades': {
            'sheet': '成绩单模板（长表）',
            'columns': ['学号','姓名','学期','课程名','分数','学分'],
            'example': ['20240101001','张三','2024-2025-1','高等数学A','85','4'],
        },
        'grades_wide': {
            'sheet': '成绩单模板（宽表-推荐）',
            'columns': ['学号','姓名','学期','高等数学A','大学英语I','程序设计基础','线性代数'],
            'example': ['20240101001','张三','2024-2025-1','85','78','92','88'],
        },
        'party': {
            'sheet': '党团发展模板',
            'columns': ['学号','姓名','阶段','阶段日期','联系人','备注'],
            'example': ['20240101001','张三','积极分子','2024-09-01','李老师','已递交入党申请书'],
        },
        'hardship': {
            'sheet': '困难认定模板',
            'columns': ['学号','困难等级','学年','家庭情况','家庭收入','人均收入','困难类型'],
            'example': ['20240101001','特别困难','2024-2025','单亲家庭','20000','5000','孤儿'],
        },
        'scholarship': {
            'sheet': '奖助学金模板',
            'columns': ['学号','奖学金名称','级别','金额','学年','学期'],
            'example': ['20240101001','国家奖学金','国家级','8000','2024-2025','1'],
        },
        'honor': {
            'sheet': '评优荣誉模板',
            'columns': ['学号','荣誉名称','荣誉级别','获奖日期','授予单位'],
            'example': ['20240101001','三好学生','校级','2024-12-20','学生处'],
        },
        'family': {
            'sheet': '家庭联络模板',
            'columns': ['学号','家长姓名','关系','家长电话','联系日期','联系方式','沟通主题'],
            'example': ['20240101001','张大明','父亲','13900000000','2024-11-15','电话','学业进展沟通'],
        },
        'cadre': {
            'sheet': '学生干部模板',
            'columns': ['学号','职务','组织名称','任职起始','任职结束','状态'],
            'example': ['20240101001','班长','计科2401班委','2024-09-01','2025-08-31','在职'],
        },
        'activity': {
            'sheet': '学生活动模板',
            'columns': ['学号','活动名称','活动日期','角色','志愿时长'],
            'example': ['20240101001','校园环保志愿活动','2024-10-15','志愿者','4'],
        },
        'employment': {
            'sheet': '就业跟踪模板',
            'columns': ['学号','单位名称','岗位','就业类型','签约日期','薪资'],
            'example': ['20240101001','某某科技有限公司','软件开发工程师','签约','2025-03-01','12000'],
        },
    }

    if type not in templates:
        raise HTTPException(400, f'type 必须为: {list(templates.keys())}')

    tpl = templates[type]
    df = pd.DataFrame([tpl['example']], columns=tpl['columns'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name=tpl['sheet'])
    output.seek(0)
    filename = f"{tpl['sheet']}.xlsx"
    return Response(
        content=output.getvalue(),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{quote(filename)}"}
    )
