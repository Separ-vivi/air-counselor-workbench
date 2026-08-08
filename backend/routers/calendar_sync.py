"""V6.18-hotfix 校历同步 - 从教务处iframe数据源抓取校历并解析入库
路由前缀 /api/calendar

V6.18-hotfix修复:
- 改用 iframe 数据源 (jwcjwxt2.fzu.edu.cn:82/xl.asp)，该页面含静态HTML表格
- 修正编码为 gb2312（旧代码用 utf-8 导致乱码）
- 支持 POST 切换学期
- 重写 HTML 表格解析逻辑
- 修正月份追踪：基于月份标题行精确赋值年月
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

router = APIRouter(prefix='/api/calendar', tags=['V6.18 校历同步'])

# ===== 数据源 URL =====
# 主页面 (含 iframe)
CALENDAR_PAGE_URL = 'https://jwch.fzu.edu.cn/ggfw/xnxl.htm'
# iframe 数据源 (实际校历表格在此)
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
    """把学期代码转成可读标签，如 202502 → 2024-2025学年第二学期"""
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
    """获取校历数据页面HTML
    
    使用 iframe 数据源 URL，支持通过 POST 切换学期。
    编码为 gb2312。
    """
    import requests
    
    url = CALENDAR_DATA_URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': CALENDAR_PAGE_URL,
    }
    
    for attempt in range(3):
        try:
            if semester_code:
                # 需要先获取 option value 映射
                # 先 GET 获取所有 option
                resp_init = requests.get(url, timeout=20, headers=headers, verify=False)
                resp_init.encoding = 'gb2312'
                
                # 找到对应学期的 option value
                option_map = _extract_option_map(resp_init.text)
                option_value = option_map.get(semester_code, '')
                
                if option_value:
                    # POST 切换到目标学期
                    resp = requests.post(url, data={'xq': option_value}, timeout=20, headers=headers, verify=False)
                else:
                    # 找不到 option value，直接用 GET
                    resp = resp_init
            else:
                resp = requests.get(url, timeout=20, headers=headers, verify=False)
            
            # 关键：使用 gb2312 编码
            resp.encoding = 'gb2312'
            
            if resp.status_code == 200 and len(resp.text) > 500:
                return resp.text
            
            logger.warning(f'页面返回异常: status={resp.status_code}, len={len(resp.text)}')
        except Exception as e:
            logger.warning(f'请求失败(第{attempt+1}次): {e}')
    
    return ''


def _extract_option_map(html: str) -> dict:
    """从HTML中提取学期代码到option value的映射
    
    Returns: {'202502': '2025022026030220260710', ...}
    """
    options = re.findall(r'<option\s+value=(\S+?)>(\d{6})</option>', html)
    return {code: value for value, code in options}


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
    
    # 从 option 元素提取学期列表
    option_codes = re.findall(r'<option\s+value=\S+?>(\d{6})</option>', html)
    if option_codes:
        available = list(dict.fromkeys(option_codes))  # 去重保序
    
    return current, available


def _get_current_semester_code() -> str:
    """获取当前学期代码（基于日期推断）"""
    now = datetime.now()
    year = now.year
    month = now.month
    if month >= 9:
        return f'{year}01'
    else:
        return f'{year - 1}02'


class _CalendarTableParser(HTMLParser):
    """校历HTML表格解析器"""
    
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
                # 清理 HTML 标签和多余空白
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
    
    表格结构:
    - Row 0: 表头（星期周 + 一二三四五六日）
    - Row 1: 开学前一周数据（无月份标题）
    - Row 2+: 月份标题行（单列 "XXXX年X月份"）或 周数据行（8列）
    - 周数据行: [周次标签, 周一, 周二, ..., 周日]
    - 每个日期单元格: "日期数字\n事件描述1\n事件描述2"
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
    
    events = []
    current_year = None
    current_month = None
    
    # 跳过表头行（Row 0: 星期周 + 一二三四五六日）
    start_idx = 1 if '星' in parser.rows[0][0] else 0
    
    for row in parser.rows[start_idx:]:
        if not row:
            continue
        
        # 检测月份标题行（单列，包含"年X月份"）
        if len(row) == 1:
            month_match = re.search(r'(\d{4})年(\d{1,2})月份?', row[0])
            if month_match:
                current_year = int(month_match.group(1))
                current_month = int(month_match.group(2))
            continue
        
        # 周数据行：需要至少8列（周次 + 7天）
        if len(row) < 8:
            continue
        
        # 如果还没有月份信息，尝试从日期推断
        if current_year is None or current_month is None:
            # 从第一行数据推断：通常是2月底
            now = datetime.now()
            if now.month >= 8:
                current_year = now.year
                current_month = 2  # 春季学期从2月开始
            else:
                current_year = now.year - 1
                current_month = 2
        
        week_label = row[0].strip()
        week_number = 0
        is_holiday_week = False
        
        if '假' in week_label:
            is_holiday_week = True
        elif week_label:
            m = re.search(r'(\d+)', week_label)
            if m:
                week_number = int(m.group(1))
        
        # 解析7天
        prev_day_num = 0
        for day_idx in range(1, min(8, len(row))):
            cell = row[day_idx].strip()
            if not cell:
                continue
            
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
                    event_text = event_text + ' ' + extra
                else:
                    event_text = extra
            
            # 跨月检测：如果日期从大变小（如31→1），说明进入下一个月
            if prev_day_num > 0 and day_num < prev_day_num - 10:
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
            
            prev_day_num = day_num
            
            # 构建完整日期
            if current_year and current_month:
                date_str = f'{current_year}-{current_month:02d}-{day_num:02d}'
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    continue
                
                if event_text or is_holiday_week:
                    # 拆分多个事件
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
                elif not event_text:
                    # 没有事件文本但有日期，也记录（无描述）
                    pass
    
    return events


@router.get('/sync')
def sync_calendar(semester: str = '', db: Session = Depends(get_db)):
    """从教务处官网同步校历
    
    semester: 学期代码，如 202502, 202601。空=当前学期
    """
    # 如果未指定学期，从官网获取当前学期
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
    
    # 获取目标学期的校历数据
    html = _fetch_data_page(semester)
    if not html:
        raise HTTPException(502, f'无法获取校历页面，学期 {semester} 可能尚未发布或URL不可用')
    
    # 解析 HTML
    try:
        events = _parse_calendar_html(html, semester)
    except Exception as e:
        logger.error(f'校历解析异常: {e}', exc_info=True)
        raise HTTPException(500, f'校历解析失败: {str(e)}')
    
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
    """返回可用学期列表及当前学期
    
    V6.18-hotfix: 从 iframe 数据源获取真实学期列表
    """
    try:
        html = _fetch_data_page()
        if html:
            website_current, available_codes = _extract_semesters_from_html(html)
            if available_codes:
                # 过滤掉当前学期之后的学期
                current_code = _get_current_semester_code()
                filtered_codes = [c for c in available_codes if c <= current_code]
                
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
                    'semesters': semesters,
                }
    except Exception as e:
        logger.warning(f'从官网获取学期列表失败: {e}')
    
    # 回退：本地生成（只显示到当前学期）
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
