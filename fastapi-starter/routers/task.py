"""
Task Router — API 路由层
=========================
定义 HTTP 端点，参数校验，调用 Service

Java 对照：
    @RestController
    @RequestMapping("/api/tasks")
    public class TaskController { ... }
"""


from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_db
from repositories.task import TaskRepository
from services.task import TaskService
from schemas.task import TaskCreate, TaskUpdate, TaskResponse, PaginatedResponse

# 创建路由器（<--> @RequestMapping("/api/tasks")）
# prefix 表示所有路由都以 /api/tasks 开头
# tags 用户 Swagger UI 分组
router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

#==============================================
# 依赖注入辅助函数
# FastAPI 的 Depends 类似于 Spring 的 @Autowired
#==============================================

def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    """
    组装 Service 层 （类似于 Spring 的依赖注入链）
    调用链：Router -> get_task_service() -> Service -> Repository -> DB
    """
    repo = TaskRepository(db = db)
    return TaskService(repo = repo)

# ============================================
# CRUD 路由
# ============================================
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(data: TaskCreate, service: TaskService = Depends(get_task_service)):
    """创建任务"""
    return await service.create_task(data)

@router.get("/", response_model=PaginatedResponse)
async def list_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, get=1, le=100, description="每页数量"),
    keyword: str | None = Query(None, description="搜索关键词（标题匹配）"),
    completed: bool | None = Query(None, description="完成状态筛选"),
    order_by: str = Query("-created_at", description="排序字段"),
    service: TaskService = Depends(get_task_service)
):
    """
    任务列表（分页 + 搜索 + 筛选 + 排序）

    试试这些请求：
    - `/api/tasks/` — 默认第 1 页，每页 10 条
    - `/api/tasks/?page=2&page_size=5` — 第 2 页，每页 5 条
    - `/api/tasks/?keyword=python` — 搜索标题含 "python" 的任务
    - `/api/tasks/?completed=true` — 只看已完成任务
    """
    return await service.list_tasks(page, page_size, keyword, completed, order_by)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, servcie: TaskService = Depends(get_task_service)):
    """获取单个任务"""
    result = await servcie.get_task(task_id)
    if result is None:
        raise HTTPException(status_code=40004, detail=f"任务 {task_id} 不存在")
    return result

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, data: TaskUpdate, service: TaskService = Depends(get_task_service)):
    """更新任务"""
    result = await service.update_task(task_id, data)
    if result is None:
        raise HTTPException(status_code=40004, detail=f"任务 {task_id} 不存在")
    return result

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, service: TaskService = Depends(get_task_service)):
    """删除"""
    success = await service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=40004, detail=f"任务 {task_id} 不存在")