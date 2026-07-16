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
    """每周五 17:00 自动生成周汇总"""
    logger.info("定时任务触发: 生成周汇总")
    try:
        db = SessionLocal()
        # 计算本周的日期范围
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())  # 本周一
        week_end = week_start + timedelta(days=6)  # 本周日
        
        # 统计本周数据
        new_students_count = db.query(Student).filter(
            Student.created_at >= datetime.combine(week_start, datetime.min.time()),
            Student.created_at <= datetime.combine(week_end, datetime.max.time())
        ).count()
        
        total_students = db.query(Student).count()
        warning_count = db.query(WarningRecord).count()
        
        # 创建周汇总记录
        summary = WeeklySummary(
            title=f"周汇总 ({week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')})",
            content=f"本周新增学生: {new_students_count}人\n"
                    f"学生总数: {total_students}人\n"
                    f"预警记录: {warning_count}条\n"
                    f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
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

app.include_router(students_router)
app.include_router(tags_router)
app.include_router(grades_router)
app.include_router(dashboard_router)
app.include_router(settings_router)
app.include_router(care_router)
app.include_router(org_router)
app.include_router(activity_router)
app.include_router(knowledge_router)
app.include_router(import_router)
app.include_router(student360_router)
app.include_router(class360_router)
app.include_router(organization_router)
app.include_router(system_router)


@app.on_event('startup')
async def startup():
    """启动时导入示例数据并启动定时任务"""
    seed_if_empty()
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
