"""
# 🎯 场景：用户输入 → LLM 分类意图 → 路由到不同处理节点 → 最终回复
# 定义 State
LangGraph 客服意图路由图
==========================
用户输入 → 意图分类 → 按意图路由 → 不同处理 → 返回回复

Graph 结构：
    start
      │
      ▼
  [classify] — 分类意图
      │
      ├─ 投诉 ──→ [handle_complaint] ──┐
      ├─ 咨询 ──→ [handle_inquiry]  ──┤
      └─ 其他 ──→ [handle_other]     ──┤
                                        ▼
                                    [END]
"""
from typing import TypedDict, List, Literal, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import operator
import os
from dotenv import load_dotenv

load_dotenv()

# 1. 定义 State （状态结构）
# State 是图的各个节点间流动的数据对象
# TypeDict 类似于 Java 中的 record - 定义字段名和类型
class RouterState(TypedDict):
    """
    路由图的状态
    字段说明：
        messages: 消息列表（add_messages reducre 会合并新旧消息）
        initent: 分类出的意图
        result:  最终处理结果
    """
    messages: Annotated[List, add_messages]   # add_messages = 追加而非覆盖
    intent: str
    result: str

# Annotated[List, add_messages] 的含义：
# 每次节点返回新的 messages 时，不是替换整个列表，而是追加到已有列表。
# 类似于 Java 的 List.addAll() 而不是 = new ArrayList()。


"""
StateGraph 高级参数（LangGraph 1.0 新增）
"""
class State(TypedDict):
    messages: Annotated[list, add_messages]

class Context(TypedDict):
    """运行时不可变上下文（如 API_KEY、用户信息等）"""
    user_id: str
    api_key: str

class InputState(TypedDict):
    """约束输入格式"""
    messages: list

class OutputState(TypedDict):
    """约束输出格式"""
    response: str

graph = StateGraph(
    state_schema=State,         # 内部状态
    context_schema=Context,     # 1.0 新增：运行时上下文（不可变，节点只读）
    input_schema=InputState,    # 1.0 新增：约束输入
    output_schema=OutputState   # 1.0 新增：约束输出
)

# 调用时传入 context
compiled = graph.compile()
result = compiled.invoke(
    {"messages": [{"role": "user", "content": "Hellow"}]},
    context={"user_id": "123", "api_key": "sk-xxx"}
)

