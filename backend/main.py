"""FastAPI 主入口 - 高校辅导员工作平台后端
单进程架构：同时提供 API 服务和前端静态文件服务
"""
import os
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from database import engine, Base
from seed_data import seed_if_empty

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import SessionLocal
from models import WeeklySummary, Student, GradeRecord, WarningRecord
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 周汇总自动生成任务
def generate_weekly_summary_job():
    """每周五 17:00 自动生成周汇总 (v3j-D · D2 重构：分板块统计)"""
    logger.info("定时任务触发: 生成周汇总")
    try:
        db = SessionLocal()
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        wk_start_dt = datetime.combine(week_start, datetime.min.time())
        wk_end_dt = datetime.combine(week_end, datetime.max.time())
        wk_start_str = week_start.strftime('%Y-%m-%d')
        wk_end_str = week_end.strftime('%Y-%m-%d')

        # 各板块统计（每一段 try/except 独立，一处失败不影响整体）
        parts = []

        # 1. 学工基础
        try:
            new_stu = db.query(Student).filter(
                Student.created_at >= wk_start_dt, Student.created_at <= wk_end_dt
            ).count()
            total_stu = db.query(Student).count()
            parts.append(f"【学工基础】\n  · 学生总数：{total_stu} 人\n  · 本周新增：{new_stu} 人")
        except Exception as _e:
            parts.append(f"【学工基础】统计失败：{_e}")

        # 2. 学业预警
        try:
            total_warn = db.query(WarningRecord).count()
            new_warn = db.query(WarningRecord).filter(
                WarningRecord.created_at >= wk_start_dt, WarningRecord.created_at <= wk_end_dt
            ).count()
            red_warn = db.query(WarningRecord).filter(WarningRecord.warning_type == 'red').count()
            unreminded = db.query(WarningRecord).filter(
                (WarningRecord.reminded == False) | (WarningRecord.reminded == None)
            ).count()
            parts.append(
                f"【学业预警】\n  · 累计预警：{total_warn} 条（红色 {red_warn}）\n"
                f"  · 本周新增：{new_warn} 条\n"
                f"  · 未提醒：{unreminded} 条"
            )
        except Exception as _e:
            parts.append(f"【学业预警】统计失败：{_e}")

        # 3. 心理关怀
        try:
            from models import PsychologyRecord
            new_psy = db.query(PsychologyRecord).filter(
                PsychologyRecord.record_date >= wk_start_str,
                PsychologyRecord.record_date <= wk_end_str
            ).count()
            focus_psy = db.query(PsychologyRecord).filter(
                PsychologyRecord.attention_level.in_(['一级', '一级重点关注', '一级关注'])
            ).count()
            parts.append(
                f"【心理关怀】\n  · 本周新增记录：{new_psy} 条\n  · 一级关注学生：{focus_psy} 人"
            )
        except Exception as _e:
            parts.append(f"【心理关怀】统计失败：{_e}")

        # 4. 党团发展
        try:
            from models import PartyProgress
            new_party = db.query(PartyProgress).filter(
                PartyProgress.updated_at >= wk_start_dt, PartyProgress.updated_at <= wk_end_dt
            ).count() if hasattr(PartyProgress, 'updated_at') else 0
            active_party = db.query(Student).filter(
                Student.political_status.in_(['中共预备党员', '中共党员', '入党积极分子'])
            ).count()
            parts.append(
                f"【党团发展】\n  · 本周进展更新：{new_party} 条\n  · 党员/积极分子：{active_party} 人"
            )
        except Exception as _e:
            parts.append(f"【党团发展】统计失败：{_e}")

        # 5. 班会与活动
        try:
            from models import ClassMeeting, Activity
            new_meeting = db.query(ClassMeeting).filter(
                ClassMeeting.meeting_date >= wk_start_str,
                ClassMeeting.meeting_date <= wk_end_str
            ).count()
            teacher_attended = db.query(ClassMeeting).filter(
                ClassMeeting.meeting_date >= wk_start_str,
                ClassMeeting.meeting_date <= wk_end_str,
                ClassMeeting.teacher_attended == True
            ).count() if hasattr(ClassMeeting, 'teacher_attended') else 0
            new_act = db.query(Activity).filter(
                Activity.activity_date >= wk_start_str,
                Activity.activity_date <= wk_end_str
            ).count()
            parts.append(
                f"【班会与活动】\n  · 本周班会：{new_meeting} 次（班主任出席 {teacher_attended}）\n"
                f"  · 本周活动：{new_act} 场"
            )
        except Exception as _e:
            parts.append(f"【班会与活动】统计失败：{_e}")

        # 6. 资助与困难
        try:
            from models import StudentHardship
            hardship_cnt = db.query(StudentHardship).count()
            parts.append(f"【资助情况】\n  · 困难档案总数：{hardship_cnt} 份")
        except Exception as _e:
            parts.append(f"【资助情况】统计失败：{_e}")

        content = (
            f"周汇总（{wk_start_str} ~ {wk_end_str}）\n"
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            + "\n\n".join(parts)
        )

        summary = WeeklySummary(
            title=f"周汇总 ({wk_start_str} ~ {wk_end_str})",
            content=content,
            created_at=datetime.now()
        )
        db.add(summary)
        db.commit()
        logger.info(f"周汇总已生成: {summary.title}")
        db.close()
    except Exception as e:
        logger.error(f"周汇总生成失败: {e}")

# 创建定时任务调度器
scheduler = BackgroundScheduler()
# 每周五 17:00 触发
scheduler.add_job(
    generate_weekly_summary_job,
    trigger=CronTrigger(day_of_week='fri', hour=17, minute=0),
    id='weekly_summary',
    name='每周五生成周汇总',
    replace_existing=True
)

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(BASE_DIR, 'frontend', 'dist')

# 创建数据表
Base.metadata.create_all(bind=engine)
logger.info("数据库表已创建/确认")

# Schema 自愈：把 model 新增的字段 ALTER 到已存在的表
from schema_migrations import ensure_schema_up_to_date
try:
    ensure_schema_up_to_date(engine, Base)
except Exception as e:
    logger.error(f"schema 自愈失败: {e}")

# V5-B 知识库 AI 能力迁移
try:
    from knowledge_ai_migrations import run_knowledge_ai_migrations
    run_knowledge_ai_migrations(engine)
except Exception as e:
    logger.error(f"知识库 AI 迁移失败: {e}")

app = FastAPI(title='高校辅导员工作平台', version='1.0.0')

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# 注册 API 路由
from routers.students import router as students_router
from routers.tags import router as tags_router
from routers.grades import router as grades_router
from routers.dashboard import router as dashboard_router
from routers.settings import router as settings_router
from routers.care_modules import router as care_router
from routers.org_modules import router as org_router
from routers.activity_modules import router as activity_router
from routers.knowledge_modules import router as knowledge_router
from routers.import_router import router as import_router
from routers.student360 import router as student360_router
from routers.class360 import router as class360_router
from routers.organization import router as organization_router
from routers.system import router as system_router
from routers.productivity import router as productivity_router
from routers.system_backup import router as system_backup_router
from routers.semester_report import router as semester_report_router
from routers.knowledge_ai import router as knowledge_ai_router

app.include_router(students_router)
app.include_router(tags_router)
app.include_router(grades_router)
app.include_router(dashboard_router)
app.include_router(settings_router)
app.include_router(care_router)
app.include_router(org_router)
app.include_router(activity_router)
app.include_router(knowledge_ai_router)
app.include_router(knowledge_router)
app.include_router(import_router)
app.include_router(student360_router)
app.include_router(class360_router)
app.include_router(organization_router)
app.include_router(system_router)
app.include_router(productivity_router)
app.include_router(system_backup_router)
app.include_router(semester_report_router)


@app.on_event('startup')
async def startup():
    """启动时导入示例数据并启动定时任务"""
    seed_if_empty()
    # v3j-C c01 · 幂等 migration：老库 party_progress.stage='申请入党' → '递交入党申请书'
    try:
        from sqlalchemy import text
        with SessionLocal() as _mdb:
            _mdb.execute(text("UPDATE party_progress SET stage='递交入党申请书' WHERE stage='申请入党'"))
            _mdb.commit()
        logger.info("Migration: party_progress.stage 已完成命名统一")
    except Exception as _e:
        logger.warning(f"Migration party_progress.stage 失败(可忽略): {_e}")
    # v3j-C c02 · 幂等 migration：党员术语统一（预备党员→中共预备党员, 正式党员→中共党员）
    try:
        from sqlalchemy import text
        with SessionLocal() as _mdb:
            _mdb.execute(text("UPDATE party_progress SET stage='中共预备党员' WHERE stage='预备党员'"))
            _mdb.execute(text("UPDATE party_progress SET stage='中共党员' WHERE stage='正式党员'"))
            _mdb.execute(text("UPDATE students SET political_status='中共预备党员' WHERE political_status='预备党员'"))
            _mdb.commit()
        logger.info("Migration: 党员术语已统一(预备党员→中共预备党员, 正式党员→中共党员)")
    except Exception as _e:
        logger.warning(f"Migration 党员术语 失败(可忽略): {_e}")
    # v3j-C c02-hotfix2 · 幂等 migration：干部级别修正（团支书→团支部，党支部干部→党支部）
    try:
        from sqlalchemy import text
        with SessionLocal() as _mdb:
            _mdb.execute(text("UPDATE student_cadre_records SET level='团支部' WHERE position='团支书'"))
            _mdb.execute(text("UPDATE student_cadre_records SET level='党支部' WHERE position IN ('党支部书记','党支部组织委员','党支部宣传委员','党支部纪检委员')"))
            _mdb.commit()
        logger.info("Migration: 干部级别修正完成（团支书→团支部, 党支部干部→党支部）")
    except Exception as _e:
        logger.warning(f"Migration 干部级别 失败(可忽略): {_e}")
    # v3j-D · D1: warning_records 加 reminded / reminded_at 字段（SQLite 幂等）
    try:
        from sqlalchemy import text
        with SessionLocal() as _mdb:
            for _sql in [
                "ALTER TABLE warning_records ADD COLUMN reminded INTEGER DEFAULT 0",
                "ALTER TABLE warning_records ADD COLUMN reminded_at TEXT",
            ]:
                try:
                    _mdb.execute(text(_sql))
                    _mdb.commit()
                except Exception:
                    _mdb.rollback()
        logger.info("Migration: warning_records 已添加 reminded / reminded_at 字段")
    except Exception as _e:
        logger.warning(f"Migration warning_records reminded 失败(可忽略): {_e}")

    # v3j-D 补丁2: psychology_records 加 reminded / reminded_at 字段（SQLite 幂等）
    try:
        with engine.connect() as conn:
            for sql in [
                "ALTER TABLE psychology_records ADD COLUMN reminded INTEGER DEFAULT 0",
                "ALTER TABLE psychology_records ADD COLUMN reminded_at TEXT",
            ]:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception:
                    pass
        logger.info("Migration: psychology_records 已添加 reminded / reminded_at 字段")
    except Exception as _e:
        logger.warning(f"Migration psychology_records reminded 失败(可忽略): {_e}")
    # v3j-D · D2: class_meetings 加 teacher_attended / teacher_names 字段
    try:
        from sqlalchemy import text
        with SessionLocal() as _mdb:
            for _sql in [
                "ALTER TABLE class_meetings ADD COLUMN teacher_attended INTEGER DEFAULT 0",
                "ALTER TABLE class_meetings ADD COLUMN teacher_names VARCHAR(200) DEFAULT ''",
            ]:
                try:
                    _mdb.execute(text(_sql))
                    _mdb.commit()
                except Exception:
                    _mdb.rollback()
        logger.info("Migration: class_meetings 已添加 teacher_attended / teacher_names 字段")
    except Exception as _e:
        logger.warning(f"Migration class_meetings teacher_attended 失败(可忽略): {_e}")
    # v3j-D · D3: classes 加班级档案字段（slogan/features/office_location）
    try:
        from sqlalchemy import text
        with SessionLocal() as _mdb:
            for _sql in [
                "ALTER TABLE classes ADD COLUMN slogan VARCHAR(200) DEFAULT ''",
                "ALTER TABLE classes ADD COLUMN features TEXT DEFAULT ''",
                "ALTER TABLE classes ADD COLUMN office_location VARCHAR(200) DEFAULT ''",
            ]:
                try:
                    _mdb.execute(text(_sql))
                    _mdb.commit()
                except Exception:
                    _mdb.rollback()
        logger.info("Migration: classes 已添加 slogan / features / office_location 字段")
    except Exception as _e:
        logger.warning(f"Migration classes 班级档案字段 失败(可忽略): {_e}")
    # v3h · 记事本联动: notes 加 remind_at 字段
    try:
        from sqlalchemy import text
        with SessionLocal() as _mdb:
            try:
                _mdb.execute(text("ALTER TABLE notes ADD COLUMN remind_at VARCHAR(30) DEFAULT ''"))
                _mdb.commit()
            except Exception:
                _mdb.rollback()
        logger.info("Migration: notes 已添加 remind_at 字段")
    except Exception as _e:
        logger.warning(f"Migration notes remind_at 失败(可忽略): {_e}")
    # 启动定时任务调度器
    scheduler.start()
    logger.info("定时任务调度器已启动")
    # 获取下次触发时间
    job = scheduler.get_job('weekly_summary')
    if job:
        logger.info(f"周汇总任务下次执行时间: {job.next_run_time}")


@app.on_event('shutdown')
async def shutdown():
    """关闭时停止定时任务"""
    scheduler.shutdown(wait=False)
    logger.info("定时任务调度器已停止")


@app.get('/api/health')
def health_check():
    return {'status': 'ok', 'message': '高校辅导员工作平台运行中'}


# ===== 前端静态文件服务 =====
# 挂载静态资源目录（js/css/images 等带 hash 的文件）
if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, 'assets')
    if os.path.isdir(assets_dir):
        app.mount('/assets', StaticFiles(directory=assets_dir), name='static-assets')


@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    """SPA 回退：非 /api 路径的 404 返回 index.html"""
    if not request.url.path.startswith('/api'):
        index_path = os.path.join(FRONTEND_DIST, 'index.html')
        if os.path.isfile(index_path):
            return FileResponse(index_path)
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail': exc.detail}
    )


@app.get('/')
async def serve_index():
    """根路径返回前端 index.html"""
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        status_code=503,
        content={'error': '前端未构建，请先执行 pnpm run build'}
    )


if __name__ == '__main__':
    port = int(os.environ.get('DEPLOY_RUN_PORT', '5000'))
    uvicorn.run(app, host='0.0.0.0', port=port)
