"""Pydantic 请求/响应模型"""
"""
ORM 实体面向数据库，Pydantic Schema 面向 HTTP API。
即使本项目较小，也应保持两者分离：客户端只能提交允许的字段，接口返回格式也不会随表结构泄露或漂移。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

class QueryRequest(BaseModel):
    """POST /api/query 的请求体"""

    question: str = Field(..., min_length=1, max_length=1000, description="用户输入的自然语言")

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("问题不能为空")
        return value

class ConversationListItem(BaseModel):
    """历史列表中的简要记录"""
    id: int
    user_query: str
    is_success: bool
    created_at: datetime

class ConversationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ConversationListItem]

class ConversationDetailResponse(ConversationListItem):
    """单条历史详情。result_data 已从 JSON 字符串反序列化。"""
    generated_sql: str | None
    result_data: list[dict[str, Any]] | None
    error_message: str | None
    token_usage: int

