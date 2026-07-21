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
# class State(TypedDict):
#     messages: Annotated[list, add_messages]

# class Context(TypedDict):
#     """运行时不可变上下文（如 API_KEY、用户信息等）"""
#     user_id: str
#     api_key: str

# class InputState(TypedDict):
#     """约束输入格式"""
#     messages: list

# class OutputState(TypedDict):
#     """约束输出格式"""
#     response: str

# graph = StateGraph(
#     state_schema=State,         # 内部状态
#     context_schema=Context,     # 1.0 新增：运行时上下文（不可变，节点只读）
#     input_schema=InputState,    # 1.0 新增：约束输入
#     output_schema=OutputState   # 1.0 新增：约束输出
# )

# # 调用时传入 context
# compiled = graph.compile()
# result = compiled.invoke(
#     {"messages": [{"role": "user", "content": "Hellow"}]},
#     context={"user_id": "123", "api_key": "sk-xxx"}
# )


"""
定义节点
"""
# 2. 创建模型
model = ChatOpenAI(
    model=os.getenv("DEEPSEEK_MODEL"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0
)

# 3. 定义节点函数
# 每个节点接收当前 State，返回 State 的部分更新
def classify_intent(state: RouterState) -> dict:
    """
    分类节点：分析用户意图

    输入：state["message"]（用户最新消息）
    输出：{"intent": "complaint" | "inquiry" | "other"}
    """
    user_message = state["messages"][-1].content

    # 用 LLM 分类（简单的分类任务用 prompt 就够）
    prompt = f""" 分析以下用户消息的意图，只回复以下三个词之一：
    - complaint （投诉/不满）
    - inquiry（咨询/提问）
    - other （其它）

    用户消息："{user_message}"

    意图（只回复一个词）：
    """

    response = model.invoke(prompt)
    intent = response.content.strip().lower()

    # 归一化
    valid_intents = {"complaint", "inquiry", "other"}
    if intent not in valid_intents:
        intent = "other"

    print(f"[分类结果] 用户意图：{intent}")
    return {"intent": intent}

def handle_complaint(state: RouterState) -> dict:
    """处理投诉"""
    user_message = state["messages"][-1].content
    prompt = f"""用户投诉内容："{user_message}" 
    请以客服身份回复，表达歉意并提供解决方案。回复要温暖、专业。
    """
    response = model.invoke(prompt)
    return {
        "result": response.content,
        "messages": [AIMessage(content=response.content)]
    }

def handle_inquiry(state: RouterState) -> dict:
    """处理咨询"""
    user_message = state["messages"][-1].content
    prompt = f"""用户咨询："{user_message}" 
    请简洁清晰的回答用户问题。如果不确定的，建议练习人工客服。
    """
    response = model.invoke(prompt)
    return {
        "result": response.content,
        "messages": [AIMessage(content=response.content)]
    }

def handle_other(state: RouterState) -> dict:
    """处理其它消息"""
    return {
        "result": "您好！我是小深助手。我可以帮您处理投诉反馈或解答问题咨询，请告诉我您需要什么帮助？"
    }


"""
定义路由条件 + 构件图
"""
# 4. 条件路由函数
def route_by_intent(state: RouterState) -> Literal["handle_complaint", "handle_inquiry", "handle_other"]:
    """
    根据分类结果，返回下一个节点要执行的节点名
    返回值必须是已注册的节点名！
    """
    intent = state.get("intent", "other")
    route_map = {
        "complaint": "handle_complaint",
        "inquiry": "handle_inquiry"
    }
    return route_map.get(intent, "handle_other")

# 5. 构建图
# 创建 StateGraph，泛型参数为我们的 State 类型
graph = StateGraph(RouterState)

# ------ 添加节点 ---------
graph.add_node("classify", classify_intent)
graph.add_node("handle_complaint", handle_complaint)
graph.add_node("handle_inquiry", handle_inquiry)
graph.add_node("handle_other", handle_other)

# ------- 添加边 --------
# START -> classify：图入口
graph.add_edge(START, "classify")

# classify -> 条件路由（根据 intent 选择下一个节点）
graph.add_conditional_edges(
    "classify",         # 从哪个节点出发
    route_by_intent,    # 路由函数
    {
        "handle_complaint": "handle_complaint",       # 返回值 -> 目标节点
        "handle_inquiry": "handle_inquiry",
        "handle_other": "handle_other"      
    }
)

# 处理所有节点 -> END
graph.add_edge("handle_complaint", END)
graph.add_edge("handle_inquiry", END)
graph.add_edge("handle_other", END)

# ----- 编译 -----
app = graph.compile()


# ======== 6. 测试 ===========
async def main():
    print("=" * 50)
    print("🧪 客服路由图测试")
    print("=" * 50)

    test_cases = [
        "我买的商品有质量问题，用了两天就坏了！",
        "请问退货流程是什么？",
        "今天天气真不错"
    ]

    for i, test_input in enumerate(test_cases, 1):
        result = app.invoke({
            "messages": [HumanMessage(content=test_input)],
            "intent": "",
            "result": ""
        })

        print(f"意图：{result['intent']}")
        print(f"回复：{result['result'][:100]}...")


"""
Memory - 对话记忆持久化
Java对照：InMemorySaver/SqliteSaver ≈ LangChain4j的MemorySaver/SqliteSaver

LangGraph Memory — Checkpoint 持久化
======================================
Checkpointer 会自动在每个节点执行后保存状态快照
这样即使程序重启，对话历史也不会丢失

两种 Save 模式：
    InMemorySaver: 内存存储（重启丢失，调试用）
    SqliteSaver:   SQLite 文件持久化（生产用）
"""
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

# ========== 方式一：InMemorySaver ===========
memory = InMemorySaver()
app_with_memory = graph.compile(checkpointer=memory)

# 配置中的 thread_id 类似于“会话ID”
# 同一个 thread_id 共享历史和 checkpoint
config = {"configurable": {"thread_id": "user-001"}}

# 第一轮
result1 = app_with_memory.invoke(
    {"messages": {HumanMessage(content="我叫张三")}},
    config=config         # 必须传config
)
print(f"Round 1: {result1["messages"][-1].content}")

# 第二轮（自动加载上一轮状态）
result2 = app_with_memory.invoke(
    {"messages": {HumanMessage(content="我刚才说我叫什么？")}},
    config=config         # 同一个 thread_id
)
print(f"Round 2: {result2["messages"][-1].content}")

# ============================================
# 方式二：SqliteSaver（持久化到文件）
# ============================================
# ⭐ 新版 API 使用 from_conn_string
# with SqliteSaver.from_conn_string("langgraph_checkpoints.db") as checkpointer:
#     graph = workflow.compile(checkpointer=checkpointer)


if __name__=="__main__":
    import asyncio
    asyncio.run(main())