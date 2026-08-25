"""V6.19 校历同步 - 从教务处iframe数据源抓取校历并解析入库
路由前缀 /api/calendar

V6.19修复:
- 修复跨月fallback逻辑：根据学期代码和首个月份标题推断起始年月，
  秋季学期从8月开始，春季学期从2月开始，不再写死2月导致8月日期拼成无效日期
- 修复定时任务引用的函数名与实际不一致（_fetch_page→_fetch_data_page等）
- requirements.txt 补充 requests 依赖
"""
import re
import logging
from datetime import datetime
from typing import Optional, List
from html.parser import HTMLParser
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import delete as sa_delete
from database import get_db
from models import AcademicCalendarEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/calendar', tags=['V6.19 校历同步'])

# ===== 数据源 URL =====
CALENDAR_PAGE_URL = 'https://jwch.fzu.edu.cn/ggfw/xnxl.htm'
CALENDAR_DATA_URL = 'https://jwcjwxt2.fzu.edu.cn:82/xl.asp'

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
    '军训': '军训',
}

_HOLIDAY_KEYWORDS = {'暑假', '寒假', '放假', '国庆', '清明', '劳动节', '端午', '中秋', '元旦', '春节', '假'}


def _classify_event(desc: str):
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
    if len(semester) != 6:
        return semester
    year = int(semester[:4])
    part = int(semester[4:])
    if part == 1:
        return f'{year}-{year + 1}学年第一学期'
    elif part == 2:
        return f'{year - 1}-{year}学年第二学期'
    return semester


def _fetch_data_page(semester_code: str = '') -> str:
    """获取校历数据页面HTML，编码为 gb2312"""
    import requests

    url = CALENDAR_DATA_URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': CALENDAR_PAGE_URL,
    }

    for attempt in range(3):
        try:
            if semester_code:
                resp_init = requests.get(url, timeout=20, headers=headers, verify=False)
                resp_init.encoding = 'gb2312'
                option_map = _extract_option_map(resp_init.text)
                option_value = option_map.get(semester_code, '')

                if option_value:
                    resp = requests.post(url, data={'xq': option_value}, timeout=20, headers=headers, verify=False)
                else:
                    resp = resp_init
            else:
                resp = requests.get(url, timeout=20, headers=headers, verify=False)

            resp.encoding = 'gb2312'

            if resp.status_code == 200 and len(resp.text) > 500:
                return resp.text

            logger.warning(f'页面返回异常: status={resp.status_code}, len={len(resp.text)}')
        except Exception as e:
            logger.warning(f'请求失败(第{attempt+1}次): {e}')

    return ''


def _extract_option_map(html: str) -> dict:
    options = re.findall(r'<option\s+value=(\S+?)>(\d{6})</option>', html)
    return {code: value for value, code in options}


def _extract_semesters_from_html(html: str) -> tuple:
    current = ''
    available = []

    m = re.search(r'当前学期[：:]\s*(\d{6})', html)
    if m:
        current = m.group(1)

    option_codes = re.findall(r'<option\s+value=\S+?>(\d{6})</option>', html)
    if option_codes:
        available = list(dict.fromkeys(option_codes))

    return current, available


def _get_current_semester_code() -> str:
    now = datetime.now()
    year = now.year
    month = now.month
    if month >= 9:
        return f'{year}01'
    else:
        return f'{year - 1}02'


class _CalendarTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_td = False
        self.current_row = []
        self.rows = []
        self.current_text = ''
        self.table_count = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.table_count += 1
        if self.table_count == 1:
            if tag == 'tr':
                self.current_row = []
            elif tag in ('td', 'th'):
                self.in_td = True
                self.current_text = ''
            elif tag == 'br':
                self.current_text += '\n'

    def handle_endtag(self, tag):
        if self.table_count == 1:
            if tag in ('td', 'th'):
                self.in_td = False
                clean = re.sub(r'<[^>]+>', '', self.current_text)
                clean = re.sub(r'[\s\xa0]+', ' ', clean).strip()
                self.current_row.append(clean)
            elif tag == 'tr':
                if self.current_row:
                    self.rows.append(self.current_row)

    def handle_data(self, data):
        if self.in_td:
            self.current_text += data


def _parse_calendar_html(html: str, semester: str) -> list:
    """解析校历HTML表格，返回事件列表

    V6.19修复：
    - 先扫描所有月份标题确定年月序列
    - 开学前一周（无月份标题的首行）根据首个月份标题推断上月日期
    - 秋季学期从8月底开始，春季学期从2月底开始
    """
    parser = _CalendarTableParser()
    try:
        parser.feed(html)
    except Exception as e:
        logger.error(f'HTML解析异常: {e}')
        return []

    if not parser.rows:
        logger.warning('未解析到任何表格行')
        return []

    # 先扫描所有月份标题
    month_headers = []
    for row in parser.rows:
        if len(row) == 1:
            m = re.search(r'(\d{4})年(\d{1,2})月份?', row[0])
            if m:
                month_headers.append((int(m.group(1)), int(m.group(2))))

    events = []

    # 根据首个月份标题推断开学前一周的年月
    if month_headers:
        first_hy, first_hm = month_headers[0]
        if first_hm == 3:
            # 春季学期：第一个月是3月，开学前一周在2月
            current_year, current_month = first_hy, 2
        elif first_hm == 9:
            # 秋季学期：第一个月是9月，开学前一周在8月
            current_year, current_month = first_hy, 8
        else:
            current_year, current_month = first_hy, first_hm
    else:
        # 回退：根据学期代码推断
        sem_year = int(semester[:4])
        sem_part = int(semester[4:]) if len(semester) == 6 else 2
        if sem_part == 1:
            current_year, current_month = sem_year, 8
        else:
            current_year, current_month = sem_year - 1, 2

    start_idx = 1 if '星' in parser.rows[0][0] else 0

    for row in parser.rows[start_idx:]:
        if not row:
            continue

        # 月份标题行：更新当前年月
        if len(row) == 1:
            month_match = re.search(r'(\d{4})年(\d{1,2})月份?', row[0])
            if month_match:
                current_year = int(month_match.group(1))
                current_month = int(month_match.group(2))
            continue

        if len(row) < 8:
            continue

        week_label = row[0].strip()
        week_number = 0
        is_holiday_week = False

        if '假' in week_label:
            is_holiday_week = True
        elif week_label:
            m = re.search(r'(\d+)', week_label)
            if m:
                week_number = int(m.group(1))

        prev_day_num = 0
        for day_idx in range(1, min(8, len(row))):
            cell = row[day_idx].strip()
            if not cell:
                continue

            lines = cell.split('\n')
            first_line = lines[0].strip()

            m = re.match(r'^(\d{1,2})\s*(.*)', first_line)
            if not m:
                continue

            day_num = int(m.group(1))
            event_text = m.group(2).strip()

            if len(lines) > 1:
                extra = '\n'.join(lines[1:]).strip()
                if event_text:
                    event_text = event_text + ' ' + extra
                else:
                    event_text = extra

            # 跨月检测
            if prev_day_num > 0 and day_num < prev_day_num - 10:
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1

            prev_day_num = day_num

            if current_year and current_month:
                date_str = f'{current_year}-{current_month:02d}-{day_num:02d}'
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    # 尝试下个月
                    next_month = current_month + 1
                    next_year = current_year
                    if next_month > 12:
                        next_month = 1
                        next_year += 1
                    date_str2 = f'{next_year}-{next_month:02d}-{day_num:02d}'
                    try:
                        datetime.strptime(date_str2, '%Y-%m-%d')
                        date_str = date_str2
                    except ValueError:
                        logger.warning(f'无效日期跳过: {current_year}-{current_month:02d}-{day_num:02d}, cell={cell[:40]}')
                        continue

                if event_text or is_holiday_week:
                    descriptions = event_text.split() if event_text else []
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
                            'day_of_week': day_idx,
                            'event_type': etype,
                            'event_description': desc,
                            'is_holiday': is_hol,
                        })

    return events


@router.get('/sync')
def sync_calendar(semester: str = '', db: Session = Depends(get_db)):
    """从教务处官网同步校历"""
    if not semester:
        try:
            data_html = _fetch_data_page()
            if data_html:
                website_current, _ = _extract_semesters_from_html(data_html)
                if website_current:
                    semester = website_current
                    logger.info(f'从官网获取到当前学期: {semester}')
        except Exception as e:
            logger.warning(f'获取官网当前学期失败: {e}')

        if not semester:
            semester = _get_current_semester_code()
            logger.info(f'使用本地推断学期: {semester}')

    html = _fetch_data_page(semester)
    if not html:
        raise HTTPException(502, f'无法获取校历页面，学期 {semester} 可能尚未发布或URL不可用')

    try:
        events = _parse_calendar_html(html, semester)
    except Exception as e:
        logger.error(f'校历解析异常: {e}', exc_info=True)
        raise HTTPException(500, f'校历解析失败: {str(e)}')

    if not events:
        raise HTTPException(422, f'未能从页面解析到校历事件，学期 {semester} 可能尚未发布')

    db.execute(sa_delete(AcademicCalendarEvent).where(
        AcademicCalendarEvent.semester == semester
    ))
    db.flush()

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
    if not semester:
        semester = _get_current_semester_code()

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
    try:
        html = _fetch_data_page()
        if html:
            website_current, available_codes = _extract_semesters_from_html(html)
            if available_codes:
                current_code = _get_current_semester_code()
                # V6.19：保留当前学期及下一学期（允许提前同步下学期校历）
                max_code = str(int(current_code) + 100)
                filtered_codes = [c for c in available_codes if c <= max_code]

                if not filtered_codes:
                    filtered_codes = available_codes[:3]

                semesters = []
                for code in filtered_codes:
                    semesters.append({
                        'code': code,
                        'label': _parse_semester_label(code),
                        'is_current': code == website_current,
                    })
                semesters.sort(key=lambda x: x['code'], reverse=True)
                return {
                    'current_semester': website_current or current_code,
                    'semesters': semesters[:8],
                }
    except Exception as e:
        logger.warning(f'从官网获取学期列表失败: {e}')

    current_code = _get_current_semester_code()
    semesters = []
    now = datetime.now()
    for year_offset in range(-2, 1):
        y = now.year + year_offset
        for part in [1, 2]:
            code = f'{y}{part:02d}'
            if code <= current_code:
                semesters.append({
                    'code': code,
                    'label': _parse_semester_label(code),
                    'is_current': code == current_code,
                })
    semesters.sort(key=lambda x: x['code'], reverse=True)
    return {
        'current_semester': current_code,
        'semesters': semesters[:6],
    }
