"""
Task Service — 业务逻辑层
===========================
编排 Repository 调用，处理业务规则

Java 对照：
    @Service
    public class TaskService {
        private final TaskRepository taskRepository;
        ...
    }
"""

from repositories.task import TaskRepository
from schemas.task import TaskCreate, TaskUpdate, TaskResponse, PaginatedResponse
from math import ceil

class TaskService:
    """Task 业务逻辑层"""

    def __init__(self, repo: TaskRepository):
        """构造器注入 Repository"""
        self.repo = repo   # 注入 Repository层（数据访问层）
    
    async def create_task(self, data: TaskCreate) -> TaskResponse:
        task = await self.repo.create(data.model_dump())    # 调用 Repository层新增方法
        return TaskResponse.model_validate(task)

    async def get_task(self, task_id: int) -> TaskResponse | None:
        task = await self.repo.get_by_id(task_id)      # 调用查询方法
        if task is None:
            return None
        return TaskResponse.model_validate(task)

    async def list_tasks(
            self,
            page: int = 1,
            page_size: int = 10,
            keyword: str | None = None,
            completed: bool | None = None,
            order_by: str = "-created_at"
            ) -> PaginatedResponse:
        tasks, total = await self.repo.list_tasks(
            page, page_size, keyword, completed, order_by
        )

        return PaginatedResponse(
            items = [TaskResponse.model_validate(t) for t in tasks],
            total = total,
            page = page,
            page_size = page_size,
            total_pages = ceil(total / page_size) if total > 0 else 1
        )

    async def update_task(self, task_id: int, data: TaskUpdate) -> TaskResponse | None:
        # model_dump(execute_unset=True) 只包含用户显示传入的字段
        # 相当于 Java 中判断 if (dto.getTitle() != null) 才更新
        task = await self.repo.update(task_id, data.model_dump(exclude_unset=True))
        if task is None:
            return None
        return TaskResponse.model_validate(task)
    
    async def delete_task(self, task_id: int) -> bool:
        return await self.repo.delete(task_id)
        
        