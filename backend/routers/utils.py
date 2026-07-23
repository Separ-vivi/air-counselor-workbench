"""通用工具函数"""


def semester_to_date_range(semester: str):
    """将 '2024-2025-1' 转为 (start_date, end_date)
    2024-2025-1 → 2024-09-01 ~ 2025-01-31
    2024-2025-2 → 2025-02-01 ~ 2025-07-31
    """
    if not semester or semester == 'all':
        return None, None
    parts = semester.split('-')
    if len(parts) != 3:
        return None, None
    year1, year2, term = int(parts[0]), int(parts[1]), parts[2]
    if term == '1':
        start = f"{year1}-09-01"
        end = f"{year2}-01-31"
    elif term == '2':
        start = f"{year2}-02-01"
        end = f"{year2}-07-31"
    else:
        return None, None
    return start, end


def get_prev_semester(semester: str):
    """获取上一学期。'2025-2026-1' → '2024-2025-2'"""
    parts = semester.split('-')
    if len(parts) != 3:
        return None
    y1, y2, term = int(parts[0]), int(parts[1]), int(parts[2])
    if term == 2:
        return f"{y1}-{y2}-1"
    else:
        return f"{y1-1}-{y1}-2"
