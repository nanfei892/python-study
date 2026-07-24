"""
查询 API 路由

POST /api/query — SSE 流式 NL2SQL 查询
GET  /api/conversations — 历史列表
GET  /api/conversations/{id} — 对话详情
DELETE /api/conversations/{id} — 删除对话
"""
import json

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nl2sql_engine import NL2SQLEngine
from config import settings
from database import get_db
from models import Conversation
from schemas import(
    ConversationDetailResponse,
    ConversationListItem,
    ConversationListResponse,
    QueryRequest
)

router = APIRouter(prefix="/api", tags=["NL2SQL"])

# 全局引擎实例（启动时初始化）
engine: NL2SQLEngine = None

def get_negine() -> NL2SQLEngine:
    """获取 NL2SQL 引擎实例"""
    global engine
    if engine is None:
        engine = NL2SQLEngine(
            db_path="sample_data.db",
            api_key=settings.deepseek_api_key
        )
    return engine



# 自然语言查询 （SSE 流式响应）
@router.post("/query")
async def natural_language_query(request: QueryRequest, 
                                 eng: NL2SQLEngine = Depends(get_negine), 
                                 db: AsyncSession = Depends(get_db)):
    """
    自然语言查询 （SSE 流式响应）
    请求体：{"question": "北京有多少用户?"}
    响应： SSE 事件流
        - generating_sql: 正在生成 SQL
        - sql_generated: SQL 已生成
        - executing: 正在执行
        - result：结果数据
        - error：错误
        - done：完成
    """
    async def generate():
        """SSE 事件生成器"""
        generated_sql: str | None = None
        result_data: list[dict] | None = None
        is_success = False
        error_message: str | None = None

        async for event in eng.query_stream(request.question):
            # SSE 格式为 data: {json}\n\n。解析后既可持久化，也原样转发给前端。
            if event.startswith("data: "):
                palyoad = json.loads(event[6:].strip())
                event_type = palyoad["type"]
                if event_type == "sql_generated":
                    generated_sql = palyoad["sql"]
                elif event_type == "result":
                    generated_sql = palyoad["sql"]
                    result_data = palyoad["data"]
                    is_success = True
                elif event_type == "error":
                    error_message = palyoad["message"]
            yield event

        # 流结束以后记录本次查询：Session 会由 get_db 在请求结束时提交。
        db.add(
            Conversation(
                user_query = request.question,
                generated_sql = generated_sql,
                result_data = json.dumps(result_data, ensure_ascii=False) if result_data else None,
                is_success = is_success,
                error_message = error_message
            )
        )


    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",     # 禁用 Nginx 缓冲
        }
    )

# 获取对话历史列表
@router.get("/conversations")
async def list_conversations(page: int = Query(default=1, ge=1), 
                             page_size: int = Query(default=20, ge=1, le=100), 
                             db: AsyncSession = Depends(get_db)):

    """获取对话历史列表"""
    count_result = await db.execute(select(func.count()).select_from(Conversation))
    total = count_result.scalar()

    result = await db.execute(
        select(Conversation)
        .order_by(desc(Conversation.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    conversations = result.scalar().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            ConversationListItem(
                id = c.id,
                user_query = c.user_query[:100],
                is_success = c.is_success,
                created_at = c.created_at
            )
            for c in conversations
        ]
    }

# 获取单条对话详情
@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    """获取单条对话详情"""
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    return ConversationDetailResponse(
        id = conv_id,
        user_query = conv.user_query,
        generated_sql = conv.generated_sql,
        result_data = json.loads(conv.result_data) if conv.result_data else None,
        is_success = conv.is_success,
        error_message = conv.error_message,
        token_usage = conv.token_usage,
        created_at = conv.created_at
    )


# 删除对话
@router.delete("/conversations/{conv_id}", status_code=204)
async def delete_conversation(conv_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    """删除对话"""
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    await db.execute(conv)
    # get_db 会在请求正常结束时提交事务
    return Response(status_code=204)
