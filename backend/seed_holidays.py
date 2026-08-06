"""
预置 2026 年法定节假日到 countdowns 表，供校历倒计时使用。
- 幂等：按 title 判重，已存在则跳过
- 覆盖：元旦/春节/清明/劳动节/端午/中秋/国庆
"""
import logging
from datetime import date
from database import SessionLocal
from models import Countdown

logger = logging.getLogger(__name__)

HOLIDAYS_2026 = [
    ('元旦', '2026-01-01', 'holiday', '#409EFF'),
    ('春节', '2026-02-17', 'holiday', '#F56C6C'),
    ('清明节', '2026-04-05', 'holiday', '#67C23A'),
    ('劳动节', '2026-05-01', 'holiday', '#E6A23C'),
    ('端午节', '2026-06-19', 'holiday', '#B77FCB'),
    ('中秋节', '2026-09-25', 'holiday', '#F1B24A'),
    ('国庆节', '2026-10-01', 'holiday', '#F56C6C'),
    ('2027 元旦', '2027-01-01', 'holiday', '#409EFF'),
]

SEMESTER_MILESTONES = [
    ('2026 秋季学期开学', '2026-09-01', 'event', '#4A7A8C'),
    ('国庆假期结束返校', '2026-10-08', 'event', '#4A7A8C'),
    ('期中考试周', '2026-11-09', 'exam', '#F56C6C'),
    ('期末考试周', '2026-12-28', 'exam', '#F56C6C'),
    ('寒假开始', '2027-01-19', 'holiday', '#409EFF'),
]


def seed_holidays(overwrite: bool = False):
    db = SessionLocal()
    added = 0
    skipped = 0
    try:
        for title, dstr, cat, color in HOLIDAYS_2026 + SEMESTER_MILESTONES:
            existing = db.query(Countdown).filter(Countdown.title == title).first()
            if existing:
                if overwrite:
                    db.delete(existing)
                    db.commit()
                else:
                    skipped += 1
                    continue
            row = Countdown(
                title=title,
                target_date=date.fromisoformat(dstr),
                category=cat,
                color=color,
                description=f'系统预置 · {cat}',
                pinned=(cat == 'holiday'),
            )
            db.add(row)
            added += 1
        db.commit()
        logger.info(f'[seed_holidays] added={added}, skipped={skipped}')
        return {'added': added, 'skipped': skipped}
    finally:
        db.close()


if __name__ == '__main__':
    print(seed_holidays())
