"""
Task Repository — 数据库操作层
================================
封装所有 SQL 操作，对外暴露业务语义的方法名

Java 对照：
    @Repository
    public class TaskRepository {
        private final EntityManager em;
        ...
    }

SQLAlchemy 2.0 查询语法要点：
    - select(Model)  →  SELECT * FROM model
    - .where(...)    →  WHERE ...
    - .order_by(...) →  ORDER BY ...
    - .offset(n)     →  OFFSET n
    - .limit(n)      →  LIMIT n
"""

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models.task import Task

class TaskRepository:
    """Task 数据访问层   -- 纯 SQLAlchemy 查询"""
    def __init__(self, db: AsyncSession):
        """
        构造器注入 Session（<-->  @Autowired EntityManager）
        Args:
            db: 异步数据库会话，由 FastAPI 的 Depends(get_db) 提供
        """
        self.db = db
    
    async def create(self, task_data: dict) -> Task:
        """创建任务"""
        task = Task(**task_data)    # ** 展开字典为关键字参数，（等同于 Task(title="...", description="...")
        self.db.add(task)    # 加入会话跟踪（类似于 em.persist())
        await self.db.flush()    # 立即发送 SQL 到数据库（获取自增ID）
        await self.db.refresh(task)    # 刷新对象（获取数据库生成的值，如 created_at）
        return task
    
    async def get_by_id(self, task_id: int)  -> Task | None:
        """根据 ID 查询单个任务"""
        result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.id == task_id,
                    Task.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()    # 返回单个结果 或 None
    
    async def list_tasks(
            self,
            page: int = 1,
            page_size: int = 10,
            keyword: str | None = None,
            completed: bool | None = None,
            order_by: str = "-created_at"    # 默认按创建时间倒序
    ) -> tuple[list[Task], int]:
        """分页查询任务列表（支持搜索、筛选、排序"""
        # 1.构建基础查询条件
        conditions = [Task.is_deleted == False]

        if keyword:
            # ilike 不区分大小写的模糊查询（类似于 SQL LIKE '%keyword%'）
            conditions.append(Task.title.ilike(f"%{keyword}%"))

        if completed is not None:
            conditions.append(Task.completed == completed)

        #2. 查询总数（用户分页元数据）
        count_query = select(func.count()).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar()

        # 3. 构建排序
        order_column = Task.created_at.desc()   # 默认
        if order_by == "created_at":
            order_column = Task.created_at.asc()
        elif order_by == "title":
            order_column = Task.title.asc()

        # 4. 查询数据
        data_query = (
            select(Task)
            .where(and_(*conditions))
            .order_by(order_column)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        tasks = (await self.db.execute(data_query)).scalars().all()

        return list(tasks), total
    
    async def update(self, task_id: int, update_data: dict) -> Task | None:
        """更新任务"""
        task = await self.get_by_id(task_id)
        if task is None:
            return None
        
        # 只更新传入的字段（Pydantic 的 model_dump(exclued_unset=True))
        for key, value in update_data.items():
            if value is not None:    # 跳过 None 字段
                setattr(task, key, value)     # 动态设置属性
            
        await self.db.flush()
        await self.db.refresh()
        return task
    
    async def delete(self, task_id: int) -> bool:
        """删除"""
        task = await self.get_by_id(task_id)
        if task is None:
            return False
        task.is_deleted = True
        await self.db.flush()
        return True
    