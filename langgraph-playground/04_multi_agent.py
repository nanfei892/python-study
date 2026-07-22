"""
多 Agent 协作。
🎯 场景：两个 Agent 协作 — 查询 Agent 从数据库获取信息，总结 Agent 将信息整理成报告。

Multi-agent 协作 — 查询 + 总结
================================
两个 Agent 通过 State 传递消息来协作

Graph 结构：
    START
      │
      ▼
  [query_agent] — 翻译用户问题 → 查询数据库 → 返回原始数据
      │
      ▼
  [summary_agent] — 接收原始数据 → 整理成报告
      │
      ▼
     END

关键概念：
    Agent 间的消息传递：Node 的输出（State 更新）→ 自动传给下一个 Node
"""
import os
from typing import TypedDict, Annotated, List

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langgraph.constants import START, END
from langgraph.graph import add_messages, StateGraph

load_dotenv()


# State
class MultiAgentState(TypedDict):
    messages: Annotated[List, add_messages]
    user_query: str  # 用户原始问题
    raw_data: str  # 查询 Agent 返回的原始数据
    final_report: str  # 总结 Agent 生成的报告


# ========= 模拟数据库 ============
FAKE_DB = {
    "orders": [
        {"id": 1, "user": "张三", "product": "Python 入门书", "amount": 39.9, "date": "2026-07-01"},
        {"id": 2, "user": "张三", "product": "机械键盘", "amount": 299.0, "date": "2026-07-05"},
        {"id": 3, "user": "李四", "product": "显示器", "amount": 1299.0, "date": "2026-07-10"},
        {"id": 4, "user": "张三", "product": "鼠标垫", "amount": 19.9, "date": "2026-07-12"},
        {"id": 5, "user": "王五", "product": "Python 入门书", "amount": 39.9, "date": "2026-07-14"},
    ],
    "products": [
        {"name": "Python 入门书", "stock": 50, "category": "图书"},
        {"name": "机械键盘", "stock": 30, "category": "外设"},
        {"name": "显示器", "stock": 15, "category": "外设"},
        {"name": "鼠标垫", "stock": 100, "category": "外设"},
    ],
}

# 定义节点
model = ChatOpenAI(
    model=os.getenv("DEEPSEEK_MODEL"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0
)


def query_agent(state: MultiAgentState) -> dict:
    """
    查询 Agent: 分析用户问题 -> 执行“数据库”查询 -> 返回原始数据
    这个 Agent 的角色类似于 “数据分析师” ---- 只负责拉取和整理数据
    """
    user_query = state["user_query"]
    # 1. 用 LLM 理解查询意图，决定查询什么
    analysis_prompt = f"""用户查询："{user_query}" 
    判断查询意图（只回复一个词）：
    - orders: 查询订单数据
    - products: 查询商品库存
    - both: 两者都需要
    """

    intent = model.invoke(analysis_prompt).content.strip().lower()
    print(f"[查询 Agent] 识别意图：{intent}")

    # 2. 执行 “查询” 操作（模拟数据库操作）
    raw_data_parts = []
    if "orders" in intent or "both" in intent:
        raw_data_parts.append("=== 订单数据 ===")
        for order in FAKE_DB["orders"]:
            raw_data_parts.append(str(order))

    if "products" in intent or "both" in intent:
        raw_data_parts.append("\n=== 商品库存 ===")
        for product in FAKE_DB["products"]:
            raw_data_parts.append(str(product))

    raw_data = "\n".join(raw_data_parts) if raw_data_parts else "未找到"
    print(f"[查询 Agent] 查询到 {len(raw_data)} 字符数据")

    return {"raw_data": raw_data}


def summary_agent(state: MultiAgentState) -> dict:
    """
    总结 Agent: 接收原始数据 -> 用 LLM 生成分析报告
    这个 Agent 角色类似于 “业务分析师” --- 把数据变成可读的洞察
    """
    user_query = state["user_query"]
    raw_data = state.get("raw_data", "无数据")

    prompt = f""" 你是一个数据分析师。请根据以下原始数据， 回答用户的问题并生成一份简洁的分析报告：
    用户问题： {user_query}
    原始数据：{raw_data}
    请生成分析报告（包含关键数据、趋势分析和建议）：
    """

    response = model.invoke(prompt)
    report = response.content
    print(f"[总结Agent] 生成了 {len(report)} 字符的报告")

    return {
        "final_report": report,
        "messages": [AIMessage(content=report)]
    }


# 构建 Multi-agent 图
multi_graph = StateGraph(MultiAgentState)

multi_graph.add_node("query_agent", query_agent)
multi_graph.add_node("summary_agent", summary_agent)

multi_graph.add_edge(START, "query_agent")
multi_graph.add_edge("query_agent", "summary_agent")
multi_graph.add_edge("summary_agent", END)

app_multi = multi_graph.compile()


# 测试
async def test_multi_agent():
    print("=" * 50)
    print("🤖 Multi-agent 协作测试")
    print("=" * 50)

    queries = [
        "张三最近买了什么？花了多少钱？",
        "哪些商品库存紧张？有什么建议？"
    ]

    for query in queries:
        print(f"\n{'=' * 40}")
        print(f"👤 用户：{query}")
        result = app_multi.invoke({
            "user_query": query,
            "raw_data": "",
            "final_report": ""
        })
        print(f"\n📊 分析报告：\n{result['final_report']}")


"""
流式输出：
💡 **LangGraph 1.0+ 推荐**：

- **StateGraph**：用 `.stream(version="v2")` —— 返回统一的 `StreamPart` dict
- **create_agent**：用 `.stream_events(version="v3")` —— 支持 `interleave("messages", "tool_calls")` 多通道交错流式

⚠️ **v1 旧格式** `(mode, chunk)` 元组已不推荐，请使用 `version="v2"`。
"""
"""
StateGraph.stream(version="v2")
LangGraph 流式输出（v2 格式）
===============================
.stream(version="v2") 返回统一的 StreamPart dict，不再需要解包元组

v1 旧格式（不推荐）：
    for mode, chunk in agent.stream(..., stream_mode=["updates"]):
        print(mode)   # "updates"
        print(chunk)  # payload

v2 新格式（⭐ 推荐）：
    for chunk in agent.stream(..., stream_mode=["updates", "custom"], version="v2"):
        print(chunk["type"])  # "updates" or "custom"
        print(chunk["data"])  # payload

与 .invoke() 的区别：
    .invoke() → 等全部执行完 → 返回最终状态
    .stream() → 每执行完一个节点 → 立即产出该节点的输出
"""


async def demo_stream():
    """演示流式输出"""
    # .stream(version="v2") 返回统一的 StreamPart dict
    async for chunk in app_multi.astream(
            {"user_query": "张三的消费情况如何？"},
            steam_model=["updates"],  # 支持多模式：["updates", "messages", "custom"]
            version="v2",
    ):
        # chunk 是统一的 StreamPart dict: {"type": "updates", "data": {...}}
        if chunk["type"] == "updates":
            for node_name, node_output in chunk["data"].items():
                print(f"\n[{node_name}]产生了输出：")
                for key, value in node_output.items():
                    display_value = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                    print(f"{key} = {display_value}")

if __name__ == "__main__":
    import asyncio

    # asyncio.run(test_multi_agent())
    asyncio.run(demo_stream())
