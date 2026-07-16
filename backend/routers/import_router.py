"""
AI 智能数据导入 - 两步式：detect(预览) + confirm(确认写入)
支持：学生花名册 / 成绩单 / 党团进度
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

# ============ 列名同义词映射表 ============
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

# 数据库字段中文名（用于展示）
DB_FIELD_NAMES = {
    'student_no': '学号', 'name': '姓名', 'gender': '性别', 'major': '专业',
    'class_name': '班级', 'birth_date': '出生日期', 'political_status': '政治面貌',
    'phone': '联系电话', 'parent_phone': '家长电话', 'email': '邮箱',
    'birth_source': '生源地', 'notes': '备注',
    'id_card': '身份证号', 'campus': '校区', 'dorm_building': '宿舍楼',
    'dorm_room': '房间号', 'is_off_campus': '是否外宿', 'off_campus_address': '外宿地址',
    'semester': '学期', 'course_name': '课程名', 'score': '分数', 'gpa': '绩点', 'credit': '学分',
    'is_repair': '是否重修',
    'stage': '阶段', 'stage_date': '阶段日期', 'contact_person': '联系人',
}


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """清洗 DataFrame：跳过说明行、空行、汇总行"""
    # 1. 找到真正的列名行（包含最多非空字符串的行）
    best_row_idx = 0
    best_score = 0
    for i in range(min(10, len(df))):  # 只检查前10行
        row = df.iloc[i]
        # 计算该行中非空且非数字的字符串数量
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

    # 4. 删除汇总行（包含"合计"、"总计"、"汇总"等关键词的行）
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
                # 精确匹配优先
                if col_clean == alias:
                    matched_db_field = db_field
                    best_alias_len = len(alias)
                    break
                # 模糊匹配：取最长别名匹配，避免短别名误匹配
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
    """自动识别文件类型"""
    mapped_fields = {m['db_column'] for m in mapping if m['db_column']}

    # 成绩单特征：有学号+姓名+多个未映射列（课程名）
    if 'student_no' in mapped_fields and 'name' in mapped_fields:
        unmapped_cols = [m['file_column'] for m in mapping if not m['db_column']]
        if len(unmapped_cols) >= 3:
            # 检查未映射列是否像课程名（包含数字成绩值）
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

    # 党团发展表特征：有阶段相关字段
    party_keywords = ['阶段', '发展', '积极分子', '预备党员', '党员', '团员']
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

    # 解析文件（header=None 让 clean_dataframe 统一处理表头定位）
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

    # 列名映射
    columns = list(df.columns)
    mapping = map_columns(columns, STUDENT_COLUMN_SYNONYMS)

    # 识别文件类型
    data_type = detect_file_type(df, mapping)

    # 如果是成绩单，用成绩同义词重新映射
    if data_type == 'grades':
        mapping = map_columns(columns, GRADE_COLUMN_SYNONYMS)
        # 未映射的列视为课程名
        for m in mapping:
            if not m['db_column']:
                m['db_column'] = f'course:{m["file_column"]}'
                m['db_field_name'] = f'课程: {m["file_column"]}'
    elif data_type == 'party':
        mapping = map_columns(columns, PARTY_COLUMN_SYNONYMS)

    # 生成导入 ID
    import_id = f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(df)}"

    # 存储待确认数据
    _pending_imports[import_id] = {
        'dataframe': df,
        'data_type': data_type,
        'mapping': mapping,
        'columns': columns,
    }

    # 构建预览数据
    rows = []
    for _, row in df.head(5).iterrows():
        row_dict = {}
        for col in columns:
            row_dict[col] = str(row.get(col, ''))
        rows.append(row_dict)

    # 查重统计
    duplicate_count = 0
    if data_type == 'students':
        from database import SessionLocal
        from models import Student
        db = SessionLocal()
        try:
            student_no_col = next((m['file_column'] for m in mapping if m.get('db_column') == 'student_no'), None)
            if student_no_col:
                student_nos = [str(x) for x in df[student_no_col].dropna().unique().tolist() if str(x).strip()]
                if student_nos:
                    existing_count = db.query(Student).filter(Student.student_no.in_(student_nos)).count()
                    duplicate_count = existing_count
        finally:
            db.close()
    elif data_type == 'grades':
        from database import SessionLocal
        from models import Student
        db = SessionLocal()
        try:
            student_no_col = next((m['file_column'] for m in mapping if m.get('db_column') == 'student_no'), None)
            if student_no_col:
                student_nos = [str(x) for x in df[student_no_col].dropna().unique().tolist() if str(x).strip()]
                if student_nos:
                    # 统计学号存在于数据库中的记录数（这些是有效的，可以导入成绩）
                    existing_count = db.query(Student).filter(Student.student_no.in_(student_nos)).count()
                    duplicate_count = existing_count  # 这里表示"学号已存在"的数量
        finally:
            db.close()

    # 供前端使用：source -> target 建议映射
    suggested_mapping = {m['file_column']: m['db_column'] for m in mapping if m.get('db_column') and not m['db_column'].startswith('course:')}
    # 供前端使用：每列的示例值
    samples = {}
    for col in columns:
        try:
            if col in df.columns and df[col].notna().any():
                samples[col] = str(df[col].dropna().iloc[0])
            else:
                samples[col] = ''
        except Exception:
            samples[col] = ''

    return {
        'import_id': import_id,
        'data_type': data_type,
        'columns': columns,
        'headers': columns,  # 前端兼容
        'mapping': mapping,
        'suggested_mapping': suggested_mapping,  # 前端兼容
        'samples': samples,  # 前端兼容
        'preview_data': rows,
        'preview': rows,  # 前端兼容
        'total_rows': len(df),
        'valid_rows': len(df),
        'duplicate_count': duplicate_count,
        'warnings': [],
    }


@router.post('/confirm')
async def confirm_import(req: ConfirmRequest):
    """第二步：确认导入，写入数据库"""
    from database import SessionLocal
    from models import Student, GradeRecord, PartyProgress

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

    db = SessionLocal()
    created = 0
    skipped = 0
    updated = 0

    try:
        if data_type == 'students':
            # ---------- Student 直属字段（不含 class_name / major / grade / family_situation） ----------
            STUDENT_DIRECT_FIELDS = ['gender', 'birth_date', 'political_status',
                                     'phone', 'parent_phone', 'email', 'birth_source', 'notes']

            # ---------- class_name / major / grade 用于组织层级：找到或创建 ClassModel ----------
            from models import Grade as GradeOrg, Major, ClassModel

            def resolve_class_id(row):
                """根据 class_name / major / grade 三层信息定位或创建 ClassModel，返回 class_id"""
                cn = str(row.get(col_map.get('class_name', ''), '')).strip() if col_map.get('class_name') else ''
                mj = str(row.get(col_map.get('major', ''), '')).strip() if col_map.get('major') else ''
                gd = str(row.get(col_map.get('grade', ''), '')).strip() if col_map.get('grade') else ''
                if not cn:
                    return None
                # class_name 全局唯一，先直接查
                existing = db.query(ClassModel).filter(ClassModel.class_name == cn).first()
                if existing:
                    return existing.id
                # 不存在则创建组织层级：Grade -> Major -> ClassModel
                # 从班级名中尝试提取年级信息（e.g. "计科2401" -> 2024级）
                if not gd:
                    m = re.search(r'(\d{2})\d{2}', cn)
                    if m:
                        yy = int(m.group(1))
                        year = 2000 + yy
                        gd = f'{year}级'
                if not gd:
                    gd = '未分年级'
                if not mj:
                    mj = '未分专业'
                # Grade
                grade_obj = db.query(GradeOrg).filter(GradeOrg.grade_name == gd).first()
                if not grade_obj:
                    start_year = 2000
                    m = re.search(r'(\d{4})', gd)
                    if m:
                        start_year = int(m.group(1))
                    grade_obj = GradeOrg(grade_name=gd, start_year=start_year)
                    db.add(grade_obj)
                    db.flush()
                # Major
                major_obj = db.query(Major).filter(Major.major_name == mj, Major.grade_id == grade_obj.id).first()
                if not major_obj:
                    major_obj = Major(major_name=mj, grade_id=grade_obj.id)
                    db.add(major_obj)
                    db.flush()
                # ClassModel
                new_class = ClassModel(class_name=cn, major_id=major_obj.id)
                db.add(new_class)
                db.flush()
                return new_class.id

            for _, row in df.iterrows():
                student_no = str(row.get(col_map.get('student_no', ''), '')).strip()
                name = str(row.get(col_map.get('name', ''), '')).strip()
                if not student_no or not name:
                    skipped += 1
                    continue

                existing = db.query(Student).filter(Student.student_no == student_no).first()
                if existing:
                    if req.conflict_strategy == 'skip':
                        skipped += 1
                        continue
                    elif req.conflict_strategy == 'overwrite':
                        # name
                        existing.name = name
                        # 直属字段
                        for field in STUDENT_DIRECT_FIELDS:
                            col_name = col_map.get(field, '')
                            if col_name and col_name in row.index:
                                val = str(row[col_name]).strip()
                                if val:
                                    setattr(existing, field, val)
                        # class_id
                        cid = resolve_class_id(row)
                        if cid:
                            existing.class_id = cid
                        updated += 1
                    else:
                        skipped += 1
                else:
                    student = Student(student_no=student_no, name=name)
                    for field in STUDENT_DIRECT_FIELDS:
                        col_name = col_map.get(field, '')
                        if col_name and col_name in row.index:
                            val = str(row[col_name]).strip()
                            if val:
                                setattr(student, field, val)
                    cid = resolve_class_id(row)
                    if cid:
                        student.class_id = cid
                    db.add(student)
                    created += 1

        elif data_type == 'grades':
            semester_col = col_map.get('semester', '')
            student_no_col = col_map.get('student_no', '')
            name_col = col_map.get('name', '')

            for _, row in df.iterrows():
                student_no = str(row.get(student_no_col, '')).strip()
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

            # 导入成绩后重新计算预警
            from routers.grades import recalculate_warnings
            recalculate_warnings(db)

        elif data_type == 'party':
            for _, row in df.iterrows():
                student_no = str(row.get(col_map.get('student_no', ''), '')).strip()
                if not student_no:
                    skipped += 1
                    continue

                student = db.query(Student).filter(Student.student_no == student_no).first()
                if not student:
                    skipped += 1
                    continue

                stage = str(row.get(col_map.get('stage', ''), '')).strip()
                stage_date = str(row.get(col_map.get('stage_date', ''), '')).strip()
                contact = str(row.get(col_map.get('contact_person', ''), '')).strip()
                notes = str(row.get(col_map.get('notes', ''), '')).strip()

                if stage:
                    progress = PartyProgress(
                        student_id=student.id,
                        stage=stage,
                        stage_date=stage_date or None,
                        contact_person=contact,
                        notes=notes,
                    )
                    db.add(progress)
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
        # 前端兼容字段
        'total': total,
        'total_rows': total,
        'imported': created + updated,
        'success_count': created + updated,
        'failed': skipped,
        'fail_count': skipped,
        'errors': [],
    }
