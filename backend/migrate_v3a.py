"""V3-A 数据库迁移脚本
1. 创建三级组织架构表
2. 迁移现有学生数据到组织架构
3. 创建所有新业务表
4. 清理冗余字段
"""
import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'edu.db')

def migrate():
    """执行数据库迁移"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== V3-A 数据库迁移开始 ===")

    # 1. 创建三级组织架构表
    print("\n[1/6] 创建三级组织架构表...")
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS grades_org (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade_name TEXT NOT NULL,
            start_year INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS majors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            major_name TEXT NOT NULL,
            grade_id INTEGER NOT NULL REFERENCES grades_org(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL UNIQUE,
            major_id INTEGER NOT NULL REFERENCES majors(id) ON DELETE CASCADE,
            class_teacher TEXT DEFAULT '',
            monitor TEXT DEFAULT '',
            league_secretary TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    print("  ✓ grades_org, majors, classes 表已创建")

    # 2. 给 students 表添加 class_id 列（如果不存在）
    print("\n[2/6] 添加 class_id 外键到 students 表...")
    cursor.execute("PRAGMA table_info(students)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'class_id' not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL")
        conn.commit()
        print("  ✓ class_id 列已添加")
    else:
        print("  ✓ class_id 列已存在")

    # 3. 从现有学生数据中自动创建组织架构
    print("\n[3/6] 从现有学生数据迁移组织架构...")
    cursor.execute("SELECT DISTINCT major, class_name FROM students WHERE class_name != '' OR major != ''")
    org_data = cursor.fetchall()

    for major_name, class_name in org_data:
        if not major_name:
            major_name = "未分配专业"
        if not class_name:
            continue

        # 解析年级（从班级名中提取，如 "计科2401" → "2024级"）
        grade_name = "默认年级"
        start_year = 2024
        for i, ch in enumerate(class_name):
            if ch.isdigit():
                digits = ''
                for j in range(i, len(class_name)):
                    if class_name[j].isdigit():
                        digits += class_name[j]
                    else:
                        break
                if len(digits) >= 2:
                    year_suffix = int(digits[:2])
                    start_year = 2000 + year_suffix
                    grade_name = f"{start_year}级"
                break

        # 创建年级
        cursor.execute("SELECT id FROM grades_org WHERE grade_name = ?", (grade_name,))
        grade_row = cursor.fetchone()
        if grade_row:
            grade_id = grade_row[0]
        else:
            cursor.execute("INSERT INTO grades_org (grade_name, start_year) VALUES (?, ?)", (grade_name, start_year))
            grade_id = cursor.lastrowid

        # 创建专业
        cursor.execute("SELECT id FROM majors WHERE major_name = ? AND grade_id = ?", (major_name, grade_id))
        major_row = cursor.fetchone()
        if major_row:
            major_id = major_row[0]
        else:
            cursor.execute("INSERT INTO majors (major_name, grade_id) VALUES (?, ?)", (major_name, grade_id))
            major_id = cursor.lastrowid

        # 创建班级
        cursor.execute("SELECT id FROM classes WHERE class_name = ?", (class_name,))
        class_row = cursor.fetchone()
        if not class_row:
            cursor.execute("INSERT INTO classes (class_name, major_id) VALUES (?, ?)", (class_name, major_id))
            class_id = cursor.lastrowid
            print(f"  ✓ 创建班级: {class_name} (专业: {major_name}, 年级: {grade_name})")
        else:
            class_id = class_row[0]

        # 关联学生
        cursor.execute("UPDATE students SET class_id = ? WHERE class_name = ?", (class_id, class_name))

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM classes")
    class_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM students WHERE class_id IS NOT NULL")
    linked_count = cursor.fetchone()[0]
    print(f"  ✓ 共创建 {class_count} 个班级，{linked_count} 名学生已关联")

    # 4. 创建新业务表
    print("\n[4/6] 创建 V3-A 新业务表...")
    cursor.executescript("""
        -- 成绩记录表
        CREATE TABLE IF NOT EXISTS grade_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            semester TEXT NOT NULL,
            course_name TEXT NOT NULL,
            score REAL,
            gpa REAL,
            credit REAL,
            is_repair BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 资助与荣誉 (6子模块)
        CREATE TABLE IF NOT EXISTS student_hardship (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            hardship_level TEXT DEFAULT '',
            academic_year TEXT DEFAULT '',
            evidence TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_grants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            grant_type TEXT DEFAULT '',
            amount REAL DEFAULT 0,
            academic_year TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            scholarship_type TEXT DEFAULT '',
            amount REAL DEFAULT 0,
            academic_year TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            loan_type TEXT DEFAULT '',
            amount REAL DEFAULT 0,
            duration TEXT DEFAULT '',
            status TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_work_study (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            position TEXT DEFAULT '',
            hours REAL DEFAULT 0,
            compensation REAL DEFAULT 0,
            academic_year TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_honors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            honor_name TEXT DEFAULT '',
            academic_year TEXT DEFAULT '',
            level TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 日常管理 (5子模块)
        CREATE TABLE IF NOT EXISTS student_dorm_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            visit_date TEXT DEFAULT '',
            dorm_room TEXT DEFAULT '',
            visitor TEXT DEFAULT '',
            situation TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            leave_type TEXT DEFAULT '',
            start_date TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            destination TEXT DEFAULT '',
            approval_status TEXT DEFAULT 'pending',
            approver TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_disciplines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            discipline_date TEXT DEFAULT '',
            discipline_type TEXT DEFAULT '',
            level TEXT DEFAULT '',
            reason TEXT DEFAULT '',
            attachment TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_dorm_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            chat_date TEXT DEFAULT '',
            topic TEXT DEFAULT '',
            key_points TEXT DEFAULT '',
            follow_up TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_attendance_exceptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            exception_date TEXT DEFAULT '',
            course_name TEXT DEFAULT '',
            exception_type TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 学籍异动
        CREATE TABLE IF NOT EXISTS student_status_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            change_type TEXT NOT NULL,
            start_date TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            reason TEXT DEFAULT '',
            original_info TEXT DEFAULT '',
            target_info TEXT DEFAULT '',
            attachment TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 专项工作
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            progress INTEGER DEFAULT 0,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS project_students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            progress INTEGER DEFAULT 0,
            material_status TEXT DEFAULT 'pending',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 学生干部记录表
        CREATE TABLE IF NOT EXISTS student_cadre_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            position TEXT NOT NULL,
            term TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    print("  ✓ 所有新业务表已创建")

    # 5. 迁移旧 grades 表数据到 grade_records
    print("\n[5/6] 迁移旧数据到新表...")
    try:
        cursor.execute("SELECT COUNT(*) FROM grades")
        old_grade_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM grade_records")
        new_grade_count = cursor.fetchone()[0]
        if old_grade_count > 0 and new_grade_count == 0:
            cursor.execute("""
                INSERT INTO grade_records (student_id, semester, course_name, score, gpa, credit, created_at)
                SELECT student_id, semester, course_name, score, gpa, credit, created_at FROM grades
            """)
            conn.commit()
            print(f"  ✓ 迁移 {old_grade_count} 条成绩记录到 grade_records")
        else:
            print(f"  ✓ 成绩记录已存在或无需迁移")
    except Exception as e:
        print(f"  ! 旧 grades 表迁移跳过: {e}")

    # 6. 验证
    print("\n[6/6] 迁移验证...")
    tables = [
        'grades_org', 'majors', 'classes', 'grade_records',
        'student_hardship', 'student_grants', 'student_scholarships',
        'student_loans', 'student_work_study', 'student_honors',
        'student_dorm_visits', 'student_leaves', 'student_disciplines',
        'student_dorm_chats', 'student_attendance_exceptions',
        'student_status_changes', 'projects', 'project_students',
        'student_cadre_records'
    ]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} 条记录")

    # 验证学号唯一性
    cursor.execute("SELECT student_no, COUNT(*) as cnt FROM students GROUP BY student_no HAVING cnt > 1")
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"\n  ⚠ 发现 {len(duplicates)} 个重复学号:")
        for sno, cnt in duplicates:
            print(f"    学号 {sno}: {cnt} 条记录")
    else:
        print(f"\n  ✓ 学号唯一性验证通过")

    conn.close()
    print("\n=== V3-A 数据库迁移完成 ===")


if __name__ == '__main__':
    migrate()
