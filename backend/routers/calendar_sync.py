"""V6.17 校历同步 - 从教务处官网抓取校历并解析入库
路由前缀 /api/calendar

V6.17修复:
- 从官网实际HTML获取当前学期和可用学期列表（不再硬编码推断）
- 修复月份跨月边界解析错误
- 增强HTML解析容错
"""
import re
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import delete as sa_delete
from database import get_db
from models import AcademicCalendarEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/calendar', tags=['V6.16 校历同步'])

# 官方校历 URL
CALENDAR_BASE_URL = 'https://jwch.fzu.edu.cn/ggfw/xnxl.htm'

# 事件类型关键词 → event_type 映射
_EVENT_KEYWORDS = {
    '补考': '补考',
    '注册': '注册',
    '正式上课': '上课',
    '上课': '上课',
    '期末考试': '期末考试',
    '考试': '考试',
    '暑假': '暑假',
    '寒假': '寒假',
    '放假': '放假',
    '国庆': '放假',
    '清明': '放假',
    '劳动节': '放假',
    '端午': '放假',
    '中秋': '放假',
    '元旦': '放假',
    '春节': '放假',
}

# 假期关键词
_HOLIDAY_KEYWORDS = {'暑假', '寒假', '放假', '国庆', '清明', '劳动节', '端午', '中秋', '元旦', '春节', '假'}


def _classify_event(desc: str):
    """从描述文本中提取事件类型和是否放假"""
    event_type = ''
    is_holiday = False
    for kw, etype in _EVENT_KEYWORDS.items():
        if kw in desc:
            event_type = etype
            break
    for kw in _HOLIDAY_KEYWORDS:
        if kw in desc:
            is_holiday = True
            break
    return event_type or '其他', is_holiday


def _parse_semester_label(semester: str) -> str:
    """把学期代码转成可读标签，如 202502 → 2025-2026学年第二学期"""
    if len(semester) != 6:
        return semester
    year = int(semester[:4])
    part = int(semester[4:])
    if part == 1:
        return f'{year}-{year + 1}学年第一学期'
    elif part == 2:
        return f'{year - 1}-{year}学年第二学期'
    return semester


def _fetch_page(url: str) -> str:
    """获取网页HTML，带重试"""
    import requests
    for attempt in range(2):
        try:
            resp = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            resp.encoding = 'utf-8'
            if resp.status_code == 200:
                return resp.text
            logger.warning(f'页面返回 {resp.status_code}: {url}')
        except requests.RequestException as e:
            logger.warning(f'请求失败(第{attempt+1}次): {e}')
    return ''


def _extract_semesters_from_html(html: str) -> tuple:
    """从官网HTML中提取当前学期和可用学期列表
    
    Returns: (current_semester_code, [list_of_semester_codes])
    """
    current = ''
    available = []
    
    # 提取当前学期: "当前学期：202502"
    m = re.search(r'当前学期[：:]\s*(\d{6})', html)
    if m:
        current = m.group(1)
    
    # 提取可用学期列表
    # 方式1: 从 <option> 元素中提取
    options = re.findall(r'<option[^>]*value=["\']?(\d{6})["\']?[^>]*>', html)
    if options:
        available = list(dict.fromkeys(options))  # 去重保序
    
    # 方式2: 从 "请选择学年学期：" 后面的文本提取
    if not available:
        m = re.search(r'请选择学年学期.*?(\d{6}(?:\s*\d{6})*)', html, re.DOTALL)
        if m:
            codes = re.findall(r'\d{6}', m.group(1))
            available = codes
    
    # 方式3: 如果都没找到，从全文提取所有6位数字学期码
    if not available:
        all_codes = re.findall(r'\b(20\d{4})\b', html)
        available = list(dict.fromkeys(all_codes))
    
    return current, available


def _parse_calendar_html(html: str, semester: str):
    """解析校历 HTML 表格，返回事件列表

    表格结构:
    - 行头是周次（如"第1周"，或"假"表示放假，或空表示开学前）
    - 月份行: colspan=8 的单元格，内容为"2026年3月份"
    - 每行 8 列: 周次 + 一~日
    - 单元格内容: "**23**" 或 "**2 正式上课<br>学生补考**"
    
    V6.17: 修复月份跨月边界问题
    """
    from html.parser import HTMLParser

    events = []

    class CalendarParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_td = False
            self.in_th = False
            self.current_row = []
            self.rows = []
            self.current_text = ''
            self.td_count = 0

        def handle_starttag(self, tag, attrs):
            if tag == 'tr':
                self.current_row = []
                self.td_count = 0
            elif tag in ('td', 'th'):
                self.in_td = True
                self.current_text = ''
                self.td_count += 1
            elif tag == 'br':
                self.current_text += '\n'

        def handle_endtag(self, tag):
            if tag in ('td', 'th'):
                self.in_td = False
                text = self.current_text.strip()
                self.current_row.append(text)
            elif tag == 'tr':
                if self.current_row:
                    self.rows.append(self.current_row)

        def handle_data(self, data):
            if self.in_td:
                self.current_text += data

    parser = CalendarParser()
    try:
        parser.feed(html)
    except Exception as e:
        logger.error(f'HTML解析异常: {e}')
        return events

    # 解析行数据
    current_month = None  # 当前月份信息
    current_year = None   # 当前年
    prev_day_num = 0      # 上一个日期数字，用于检测跨月

    for row in parser.rows:
        if not row:
            continue

        # 检测月份行: 通常只有1个元素，包含"年X月份"
        if len(row) == 1 or (len(row) >= 1 and '月份' in row[0]):
            month_match = re.search(r'(\d{4})年(\d{1,2})月份?', row[0])
            if month_match:
                current_year = int(month_match.group(1))
                current_month = int(month_match.group(2))
                prev_day_num = 0  # 新月重置
            continue

        # 检测表头行（星期）
        if len(row) >= 2 and '星' in row[0] and '期' in row[0]:
            continue

        # 数据行: 第1列是周次或"假"，后续7列是周一到周日
        if len(row) < 8:
            continue

        week_label = row[0].strip()
        week_number = 0
        is_holiday_week = False

        if '假' in week_label:
            is_holiday_week = True
            week_number = 0
        elif not week_label:
            week_number = 0
        else:
            m = re.search(r'(\d+)', week_label)
            if m:
                week_number = int(m.group(1))

        # 解析7天
        for day_idx in range(1, 8):
            cell = row[day_idx] if day_idx < len(row) else ''
            cell = cell.strip()
            if not cell:
                continue

            # 去掉 ** 标记
            cell = cell.replace('**', '').strip()
            lines = cell.split('\n')
            first_line = lines[0].strip()

            # 提取日期数字
            m = re.match(r'^(\d{1,2})\s*(.*)', first_line)
            if not m:
                continue

            day_num = int(m.group(1))
            event_text = m.group(2).strip()

            # 合并多行事件描述
            if len(lines) > 1:
                extra = '\n'.join(lines[1:]).strip()
                if event_text:
                    event_text = event_text + '\n' + extra
                else:
                    event_text = extra

            # V6.17: 跨月检测 - 如果日期突然从大数变小（如31→1），说明跨月了
            cell_year = current_year
            cell_month = current_month
            if cell_month and prev_day_num > 0 and day_num < prev_day_num - 10:
                # 跨月了，月份+1
                cell_month += 1
                if cell_month > 12:
                    cell_month = 1
                    if cell_year:
                        cell_year += 1
            prev_day_num = day_num

            # 构建完整日期
            if cell_year and cell_month:
                date_str = f'{cell_year}-{cell_month:02d}-{day_num:02d}'
                # 验证日期有效性
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    continue

                # 如果有事件文本或放假周，创建事件记录
                if event_text or is_holiday_week:
                    descriptions = event_text.split('\n') if event_text else []
                    if is_holiday_week and not descriptions:
                        descriptions = ['放假']

                    for desc in descriptions:
                        desc = desc.strip()
                        if not desc:
                            continue
                        etype, is_hol = _classify_event(desc)
                        if is_holiday_week:
                            is_hol = True
                            if not etype or etype == '其他':
                                etype = '放假'

                        events.append({
                            'semester': semester,
                            'date': date_str,
                            'week_number': week_number,
                            'day_of_week': day_idx,  # 1=周一...7=周日
                            'event_type': etype,
                            'event_description': desc,
                            'is_holiday': is_hol,
                        })

    return events


@router.get('/sync')
def sync_calendar(semester: str = '', db: Session = Depends(get_db)):
    """从教务处官网同步校历

    semester: 学期代码，如 202502, 202601。空=当前学期
    """
    # V6.17: 如果未指定学期，从官网获取当前学期
    if not semester:
        try:
            base_html = _fetch_page(CALENDAR_BASE_URL)
            if base_html:
                website_current, _ = _extract_semesters_from_html(base_html)
                if website_current:
                    semester = website_current
                    logger.info(f'从官网获取到当前学期: {semester}')
        except Exception as e:
            logger.warning(f'获取官网当前学期失败: {e}')
        
        if not semester:
            # 回退到本地推断
            semester = _infer_current_semester()
            logger.info(f'使用本地推断学期: {semester}')

    # 构建 URL
    url = CALENDAR_BASE_URL
    # 获取官网当前学期，判断是否需要访问特定学期页面
    website_current = ''
    try:
        base_html = _fetch_page(CALENDAR_BASE_URL)
        if base_html:
            website_current, _ = _extract_semesters_from_html(base_html)
    except Exception:
        pass
    
    if semester and semester != website_current:
        url = f'https://jwch.fzu.edu.cn/ggfw/xnxl/{semester}.htm'

    # 获取目标页面
    html = _fetch_page(url)
    if not html:
        raise HTTPException(502, f'无法获取校历页面，学期 {semester} 可能尚未发布或URL不可用')

    # 解析 HTML
    events = _parse_calendar_html(html, semester)

    if not events:
        raise HTTPException(422, f'未能从页面解析到校历事件，学期 {semester} 可能尚未发布')

    # 删除该学期旧数据再写入
    db.execute(sa_delete(AcademicCalendarEvent).where(
        AcademicCalendarEvent.semester == semester
    ))
    db.flush()

    # 批量插入
    for ev in events:
        db.add(AcademicCalendarEvent(**ev))

    db.commit()

    logger.info(f'校历同步完成: 学期={semester}, 事件数={len(events)}')

    return {
        'ok': True,
        'semester': semester,
        'semester_label': _parse_semester_label(semester),
        'count': len(events),
        'message': f'已同步 {_parse_semester_label(semester)} 校历，共 {len(events)} 条事件',
    }


@router.get('/events')
def list_calendar_events(
    semester: str = '',
    db: Session = Depends(get_db),
):
    """返回该学期所有校历事件"""
    if not semester:
        semester = _infer_current_semester()

    events = db.query(AcademicCalendarEvent).filter(
        AcademicCalendarEvent.semester == semester
    ).order_by(AcademicCalendarEvent.date, AcademicCalendarEvent.day_of_week).all()

    return {
        'semester': semester,
        'semester_label': _parse_semester_label(semester),
        'count': len(events),
        'events': [
            {
                'id': e.id,
                'date': e.date,
                'week_number': e.week_number,
                'day_of_week': e.day_of_week,
                'event_type': e.event_type,
                'event_description': e.event_description,
                'is_holiday': bool(e.is_holiday),
            }
            for e in events
        ],
    }


@router.get('/semesters')
def list_semesters():
    """返回可用学期列表及当前学期
    
    V6.17: 优先从官网获取可用学期列表，避免生成不存在的"虚空学期"
    """
    # 尝试从官网获取
    try:
        html = _fetch_page(CALENDAR_BASE_URL)
        if html:
            website_current, available_codes = _extract_semesters_from_html(html)
            if available_codes:
                semesters = []
                for code in available_codes:
                    semesters.append({
                        'code': code,
                        'label': _parse_semester_label(code),
                        'is_current': code == website_current,
                    })
                # 按学期代码降序排列
                semesters.sort(key=lambda x: x['code'], reverse=True)
                return {
                    'current_semester': website_current or (semesters[0]['code'] if semesters else ''),
                    'semesters': semesters,
                }
    except Exception as e:
        logger.warning(f'从官网获取学期列表失败: {e}')

    # 回退：本地生成（仅最近2年，避免虚空学期）
    current = _infer_current_semester()
    semesters = []
    now = datetime.now()
    for year_offset in range(-1, 2):  # 只生成最近2年
        y = now.year + year_offset
        for part in [1, 2]:
            code = f'{y}{part:02d}'
            semesters.append({
                'code': code,
                'label': _parse_semester_label(code),
                'is_current': code == current,
            })
    semesters.sort(key=lambda x: x['code'], reverse=True)
    return {
        'current_semester': current,
        'semesters': semesters,
    }


def _infer_current_semester() -> str:
    """根据当前日期推断当前学期代码（本地回退）
    
    修正: 8月仍属于上一学年的第二学期（暑假），新学年从9月开始
    第一学期(01): 9月~次年1月
    第二学期(02): 2月~8月（含暑假）
    """
    now = datetime.now()
    year = now.year
    month = now.month
    if month >= 9:
        return f'{year}01'  # 如 2026年9月 → 202601
    else:
        return f'{year - 1}02'  # 如 2026年8月 → 202502
