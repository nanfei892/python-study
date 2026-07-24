"""FastAPI 应用入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from database import init_db
from routers.query import router
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库表"""
    await init_db()
    logger.info(f"📖 Swagger UI: http://{settings.host}:{settings.port}/docs")
    yield

app = FastAPI(
    title="NL2SQL 智能问数系统",
    description="自然语言 -> SQL -> 数据库查询 -> 结果返回",
    version="1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# 注册路由
app.include_router(router)

# 静态文件（前端页面）
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__=="__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )