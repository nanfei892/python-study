"""数据库连接 + Session"""
"""SQLAlchemy 异步引擎、Session 与 ORM Base。"""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from config import settings

class Base(DeclarativeBase):
    """本项目所有的 ORM 实体基类"""

# Java 对照：DataSource / EntityManagerFactory
engine = create_async_engine(settings.database_url, echo=False)

# 每个 HTTP 请求使用一个独立的 AsyncSession
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：提供 Session，成功提交，异常回滚"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def init_db() -> None:
    """开发环境表；生成环境改用 Alembic 迁移。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

