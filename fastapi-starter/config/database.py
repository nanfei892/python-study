"""
数据库配置 — SQLAlchemy 2.0 异步引擎 + Session 管理
====================================================
使用 async 模式，与 FastAPI 的 async/await 天然配合

Java 对照：
    这个文件相当于 DataSource 配置 + EntityManagerFactory + TransactionManager 的集合
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import(create_async_engine, AsyncSession, async_sessionmaker)
from sqlalchemy.orm import DeclarativeBase
from config.settings import settings


# 1. 创建异步引擎（<--> DataSource / HikariCP 连接池）
# echo = True  会打印所有 SQL 语句（调试用，生产关掉）

engine = create_async_engine(
    settings.database_url,
    echo = settings.debug,        # 调试时 打印 SQL
    connect_args = {"check_same_thread": False}      # SQLite 必须加这个
)

# 2. 创建异步 Session 工厂 (<--> EntityManagerFactory)
# async_sessionmaker 是一个工厂函数，每次调用都创建一个新的 AsyncSession
AsyncSessionLocacl = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False       # commit 后不过期对象（避免 lazy load 异常）
)

# 3. 声明积累（<--> JPA @Entity 的基类概念）
class Base(DeclarativeBase):
    """所有 ORM 模型都继承此类"""
    pass

# 4. FastAPI 依赖注入：获取数据库 Session
# 这个函数会作为 FastAPI 的 Depends 使用‘
# 类似于 Spring 的 @Transactional 注入 EntityManager
async def get_db() -> AsyncGenerator[AsyncSession, None]:     # 注意：这里使用 async def
    """
    为每个 HTTP 请求提供一个独立的数据库 Session
    用法（在路由中）：
        @router.get("/tasks")
        async def list_tasks(db: AsyncSession = Depends(get_db))
    """
    async with AsyncSessionLocacl() as session:
        try:
            yield session           # 把session交给路由函数
            await session.commit()  # 正常完成 -> 提交事务
        except Exception:
            await session.rollback()    # 出错 -> 回滚事务
            raise
        finally:
            await session.close()   # 无论如何 -> 关闭 session

# 5. 初始化数据库表（开发环境用，生产用 Alembic）
async def init_db():
    """创建所有表 - 开发环境快速建表，类似于 JPA 的 ddl-auto: update"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

