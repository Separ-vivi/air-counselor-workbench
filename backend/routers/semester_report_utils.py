"""学期报表工具函数"""
from datetime import datetime


def _get_current_semester():
    """根据当前日期自动计算当前学期，格式如 2025-2026-1"""
    now = datetime.now()
    y = now.year
    m = now.month
    if m >= 9:
        return f"{y}-{y+1}-1"
    elif m >= 2:
        return f"{y-1}-{y}-2"
    else:
        return f"{y-1}-{y}-1"


def _format_semester_display(semester: str) -> str:
    """将学期代码转为显示格式"""
    if not semester or semester == 'all':
        return '全部学期'
    parts = semester.split('-')
    if len(parts) == 3:
        return f"{parts[0]}-{parts[1]}学年第{parts[2]}学期"
    elif len(parts) == 2:
        y = int(parts[0])
        sem_num = parts[1]
        if sem_num == '1':
            return f"{y-1}-{y}学年第1学期"
        else:
            return f"{y}-{y+1}学年第2学期"
    return semester


def _semester_date_range(semester: str):
    """将学期字符串转为日期范围"""
    if not semester or semester == 'all':
        return None, None
    parts = semester.split('-')
    if len(parts) == 3:
        y1, y2, term = parts[0], parts[1], parts[2]
        if term == '1':
            return f"{y1}-09-01", f"{y2}-01-31"
        else:
            return f"{y2}-02-01", f"{y2}-07-31"
    return None, None


def _semester_to_academic_year(semester: str):
    """将学期代码转为学年，如 '2025-2026-1' -> '2025-2026'"""
    if not semester or semester == 'all':
        return None
    parts = semester.split('-')
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return None
