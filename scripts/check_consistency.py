#!/usr/bin/env python3
"""数据一致性检查脚本 - V3-A 验收用"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import text
from database import engine

def check_table_counts():
    """检查三级架构表数量"""
    print("=" * 60)
    print("【验收1】三级组织架构表数量")
    print("=" * 60)
    
    with engine.connect() as conn:
        # grades_org is the organization grades table (年级)
        grade_count = conn.execute(text("SELECT COUNT(*) FROM grades_org")).scalar()
        major_count = conn.execute(text("SELECT COUNT(*) FROM majors")).scalar()
        class_count = conn.execute(text("SELECT COUNT(*) FROM classes")).scalar()
        
        print(f"  grades_org (年级): {grade_count} (期望: 1)")
        print(f"  majors (专业): {major_count} (期望: 6)")
        print(f"  classes (班级): {class_count} (期望: 12)")
        
        if grade_count == 1 and major_count == 6 and class_count == 12:
            print("  ✅ 通过")
            return True
        else:
            print("  ❌ 失败")
            return False


def check_no_redundant_fields():
    """检查业务表无冗余字段"""
    print("\n" + "=" * 60)
    print("【验收2】冗余字段清理检查")
    print("=" * 60)
    
    # 使用实际存在的表名
    business_tables = [
        'grade_records', 'warning_records', 'party_progress', 'psychology_records',
        'family_contacts', 'employment_records', 'student_cadre_records', 'activity_signups',
        'student_hardship', 'student_grants', 'student_scholarships', 'student_loans',
        'student_work_study', 'student_honors', 'student_dorm_visits', 'student_leaves',
        'student_disciplines', 'student_dorm_chats', 'student_attendance_exceptions',
        'student_status_changes', 'project_students'
    ]
    
    all_clean = True
    with engine.connect() as conn:
        for table in business_tables:
            # 检查表是否存在
            result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")).fetchone()
            if not result:
                print(f"  {table}: 表不存在 (跳过)")
                continue
            
            # 检查是否有冗余字段
            columns = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            column_names = [col[1] for col in columns]
            
            has_redundant = any(c in column_names for c in ['student_name', 'student_class', 'student_major'])
            if has_redundant:
                print(f"  {table}: ❌ 存在冗余字段")
                all_clean = False
            else:
                print(f"  {table}: ✅ 无冗余字段")
    
    return all_clean


def check_unique_constraint():
    """检查学号唯一约束"""
    print("\n" + "=" * 60)
    print("【验收3】学号 UNIQUE 约束检查")
    print("=" * 60)
    
    with engine.connect() as conn:
        indexes = conn.execute(text("PRAGMA index_list('students')")).fetchall()
        
        has_unique = False
        for idx in indexes:
            idx_name = idx[1]
            is_unique = idx[2]
            if is_unique:
                # 获取索引的列
                cols = conn.execute(text(f"PRAGMA index_info('{idx_name}')")).fetchall()
                col_names = [c[2] for c in cols]
                if 'student_no' in col_names:
                    has_unique = True
                    print(f"  找到唯一索引: {idx_name} on {col_names}")
        
        if has_unique:
            print("  ✅ 通过 - student_no 有 UNIQUE 约束")
            return True
        else:
            print("  ❌ 失败 - student_no 缺少 UNIQUE 约束")
            return False


def check_all_tables():
    """检查所有表是否存在"""
    print("\n" + "=" * 60)
    print("【验收4】14张新业务表检查")
    print("=" * 60)
    
    # 使用实际存在的表名（复数形式）
    expected_tables = [
        'student_hardship', 'student_grants', 'student_scholarships', 'student_loans',
        'student_work_study', 'student_honors', 'student_dorm_visits', 'student_leaves',
        'student_disciplines', 'student_dorm_chats', 'student_attendance_exceptions',
        'student_status_changes', 'projects', 'project_students'
    ]
    
    all_exist = True
    with engine.connect() as conn:
        existing = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        existing_names = [t[0] for t in existing]
        
        for table in expected_tables:
            if table in existing_names:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  {table}: ✅ 存在 (记录数: {count})")
            else:
                print(f"  {table}: ❌ 不存在")
                all_exist = False
    
    return all_exist


def check_student_count():
    """检查学生总数"""
    print("\n" + "=" * 60)
    print("【验收5】学生总数检查")
    print("=" * 60)
    
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM students")).scalar()
        print(f"  学生总数: {count} (期望: 384)")
        
        if count == 384:
            print("  ✅ 通过")
            return True
        else:
            print("  ❌ 失败")
            return False


def main():
    print("\n" + "=" * 60)
    print("V3-A 数据一致性检查脚本")
    print("=" * 60)
    
    results = []
    results.append(("三级架构表数量", check_table_counts()))
    results.append(("冗余字段清理", check_no_redundant_fields()))
    results.append(("学号UNIQUE约束", check_unique_constraint()))
    results.append(("14张新业务表", check_all_tables()))
    results.append(("学生总数", check_student_count()))
    
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    all_pass = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("🎉 所有检查通过!")
        return 0
    else:
        print("⚠️ 部分检查未通过，请检查上述问题")
        return 1


if __name__ == '__main__':
    sys.exit(main())
