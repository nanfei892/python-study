"""
Pydantic Schema — API 的请求/响应模型
=======================================
数据校验 + 序列化，与 ORM 模型分离

Java 对照：
    DTO（Data Transfer Object）— 不和 Entity 直接暴露给外部

为什么分离 Schema 和 Model？
    1. ORM 模型 = 数据库表结构（内部关注）
    2. Pydantic Schema = API 契约（外部关注）
    3. 分离后可以独立演化，互不影响
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# ==================请求模型=======================
class TaskCreate(BaseModel):
    """创建任务的请求体"""
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: str | None = Field(None, max_length=1000, description="任务描述")

    @field_validator("title")
    @classmethod
    def title_not_blank(cla, v: str) -> str:
        """标题不能全是空格"""
        if not v.strip():
            raise ValueError("任务标题不能为空")
        return v.strip()
    
class TaskUpdate(BaseModel):
    """更新任务的请求体（所有字段可选）"""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    completed: bool | None = None

    # model_config 是 Pydantic v2 的配置方式
    model_config = {"extra": "forbid"}    # 进制传入额外字段



# ==================响应模型=======================
class TaskResponse(BaseModel):
    """单个任务的响应体"""
    id: int
    title: str
    description: str
    completed: bool
    created_at: datetime
    update_at: datetime

    # model_config 告诉 Pydantic 可以接受 ORM 对象
    # 这让你可以直接传 TASK ORM 对象给 TaskResponse
    model_config = {"from_attributes": True}

class PaginatedResponse(BaseModel):
    """分页响应 -- 企业级 API 的标准格式"""
    items: list[TaskResponse]
    total: int      # 总记录数
    page: int       # 当前页码
    page_size: int  # 每页数量
    total_pages: int # 总页数
