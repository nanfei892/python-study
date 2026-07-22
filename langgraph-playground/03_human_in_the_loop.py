"""
HuMan-in-the-Loop ------人工介入
场景：Agent 在执行关键操作（如删除数据、发送支付）之前，需要人工审批

Human-in-the-Loop — 人工审批模式
===================================
在关键节点前暂停执行，等待人工确认后再继续

LangGraph 1.0+ 最新 API：
    interrupt_before=["节点名"]   — 在编译时指定暂停点
    result.interrupts             — ⭐ 检查是否被中断（替代旧的手动判断）
    Command(resume=...)           — 人工确认后恢复执行
    stream_events(version="v3")   — ⭐ 最新的流式 API，可直接获取 interrupts

Java 对照：
    LangGraph4j 的 interruptBefore + Command(resume=...)
    API 几乎一致！
"""

import os

from dotenv import load_dotenv
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

# 审批流 State
class ApprovalState(TypedDict):
    messages: Annotated[List, add_messages]
    request: str        # 用户请求
    decision: str    # LLM 决定的动作
    approvied: bool     # 是否已审批
    result: str         # 最终结果

# 定义节点
model = ChatOpenAI(
    model=os.getenv("DEEPSEEK_MODEL"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0
)

def analzyze_request(state: ApprovalState) -> dict:
    """分析用户请求，需要执行什么动作"""
    request = state['request']
    prompt = f""" 分析以下请求，判断需要执行什么动作。只回复动作名称（不要解释）：
    - delete_user: 删除用户
    - send_email: 发送邮件
    - query_data: 查询数据

    请求："{request}"

    动作：
    """
    response = model.invoke(prompt)
    decision = str(response.content).strip()
    print(f"[分析] 决定动作：{decision}")
    return {"decision": decision}

def execute_action(state: ApprovalState) -> dict:
    """执行审批通过后的动作"""
    decision = state["decision"]
    print(f"[执行] 正在执行：{decision}")

    # 模拟执行
    if decision == "delete_user":
        result = f"✅️ 已执行：用户删除成功"
    elif decision == "send_email":
        result = f"✅️ 已执行：邮件发送成功"
    else:
        result = f"✅️ 已执行：{decision} 完成"

    return {
        "result": result,
        "messages": [AIMessage(content=result)]
    }

def require_approval(state: ApprovalState) -> dict:
    """
    审批节点：暂停并等待人工审批
    这个节点再被调用前会暂停（因为 interrupt_before = ["require_approval"]
    """
    print(f"\n ⚠️ 需要审批：{state['decision']}")
    print("等待人工确认...")
    return {}

# 构建审批流图
approval_graph = StateGraph(ApprovalState)
approval_graph.add_node("analyze", analzyze_request)
approval_graph.add_node("require_approval", require_approval)
approval_graph.add_node("execute_action", execute_action)

approval_graph.add_edge(START, "analyze")
approval_graph.add_edge("analyze", "require_approval")
approval_graph.add_edge("require_approval", "execute_action")
approval_graph.add_edge("execute_action", END)

# 关键！在 require_approval 前暂停
app_approval = approval_graph.compile(
    checkpointer=InMemorySaver(),
    interrupt_before=["require_approval"]   # 在这个节点前暂停
)

from langgraph.types import Command

# 方式一：stream_events(version="v3") - 最新推荐
async def test_approval_v3():
    """使用 stream_events v3 -- 自动检测中断、流式获取 LLM token"""
    config = {"configurable": {"thread_id": "approval-001"}}

    print("=" * 50)
    print("📤 发送请求（v3 流式）...")

    # stream_events v3: 流式输出 + 自动检测中断
    stream = app_approval.stream_events(
        {"request": "请帮我删除用户ID为12345的账号"},
        config=config,
        version="v3"
    )

    # 流式读取 LLM 输出
    for message in stream.messages:
        for token in message.text:
            print(token, end="", flush=True)

    if stream.interrupted:
        print(f"\n\n ⚠️， 中断！ 等待审批...")
        for interrupt in stream.interrupts:
            print(f"中断 ID：{interrupt.id}")
            print(f"需要审批：{interrupt.value}")
        
        # 恢复执行
        print("\n📝 人工审批：通过！")
        stream = app_approval.stream_events(
            Command(resume={"approved": True}),    # 恢复并传入审批结果
            config=config,
            version="v3"
        )

        for message in stream.messages:
            for token in message.text:
                print(token, end="", flush=True)

# ========= 方式二：invoke() + result.interrupts --- 简洁版
async def test_approval_simple():
    """使用 invoke() --- 更简单直接"""
    config = {"configurable": {"thread_id": "approval-002"}}
    
    # 第一步：发送请求（会停在 require_approval 之前）
    print("=" * 50)
    print("📤 发送请求...")
    result = app_approval.invoke(
        {"request": "请帮我删除用户 ID 为 12345 的账号"},
        config=config,
        version="v2",   # v2 格式返回 GraphOutput 
    )

    # LangGrap 1.0 + 用 result.interrupts 检测中断
    if result.interrupts:
        print(f"⚠️中断！等待审批：{result.interrupts}")
    else:
        print(f"当前决策：{result.value['decision']}")
    
    # 第二步：人工审批通过
    print("\n📝 人工审批：通过！")

    result = app_approval.invoke(
        Command(resume={"approved": True}),
        config=config
    )
    print(f"最终结果：{result['result']}")

if __name__=="__main__":
    import asyncio
    asyncio.run(test_approval_v3())
    print(f"=" * 50)
    asyncio.run(test_approval_simple())
