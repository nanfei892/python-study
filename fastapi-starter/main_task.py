"""
FastAPI 应用主入口
===================
组装所有路由器、中间件、启动服务器

Java 对照：
    @SpringBootApplication
    public class Application {
        public static void main(String[] args) {
            SpringApplication.run(Application.class, args);
        }
    }
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from config.database import init_db
from config.settings import settings
from routers import task
from middleware.auth import APIKeyMiddleware

# ============================================
# 应用生命周期管理
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用启动/关闭时的回调

    类似于 Spring 的 @EventListener(ApplicationReadyEvent.class)

    启动时：创建数据库表
    关闭时：释放资源
    """
    # ----- 启动时 ------
    print("🚀   正在启动 FastAPI...")
    await init_db()    # 创建表（开发用，生产用 Alembic）
    print("✅️    数据库表已就绪")
    print(f"📖   Swagger UI： http://{settings.host}:{settings.port}/docs")

    yield     # <--- 应用运行中

    # ----- 关闭时 -----
    print("👋    FastAPI 正在关闭....")

# 创建 FastAPi 应用（传入 lifespan 管理生命周期）
app = FastAPI(
    title="FastAPI Starter -- Todo 应用",
    description="三层架构 + SQLAlchemy 2.0 async + Pydantic v2",
    version="1.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(task.router)

# 根路径 --- 健康检查
@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": "FastAPI Starter"}

# 添加全局认证中间件（如果需要全局保护）
# app.add_middleware(APIKeyMiddleware)

if __name__=="__main__":
    import uvicorn
    uvicorn.run(
        "main_task:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
