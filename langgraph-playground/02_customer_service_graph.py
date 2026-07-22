"""
创建 `02_customer_service_graph.py`（在 `langchain-playground/` 下），完整搭建上图描述的客服路由图，加入：

1. **更多处理节点**：增加 `handle_feedback`（反馈建议）节点
2. **Memory**：使用 `InMemorySaver`
3. **流式输出**：使用 `.stream()` 而非 `.invoke()`

代码结构与上面完全一致，只需新增节点和条件分支即可。
"""
from typing import TypedDict, List, Literal, Annotated

from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import operator
import os
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("DEEPSEEK_MODEL"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0
)

# 1. 定义 State
class RouterState(TypedDict):
    """路由图状态"""
    messages: Annotated[List, add_messages]
    intent: str
    result: str

# 2.定义节点函数
# 2.1 获取用户意图
def classify_intent(state: RouterState) -> dict:
    """
    分析用户意图
    输入：state["message"]
    输出：{"intent": "complaint" | "inquiry" | "feedback" | "other"}
    """
    # 获取用户最后一条信息（最新消息）
    user_message = state["messages"][-1].content 

    prompt = f""" 分析以下用户消息的意图，只回复以下四个词之一：
    - complaint （投诉/不满）
    - inquiry   （咨询/提问）
    - feedback  （反馈/建议）
    - other     （其他） 
    
    用户消息： "{user_message}"

    意图（只回复一个词）：
    """

    response = model.invoke(prompt)
    intent = response.content.strip().lower()

    # 归一化：
    valid_intents = {"complaint", "inquiry", "feedback", "order", "other"}
    if intent not in valid_intents:
        intent = "other"

    print(f"[分类结果] 用户意图：{intent}")
    return {"intent": intent}

# 2.2 处理投诉 complaint
def handle_complaint(state: RouterState) -> dict:
    """处理投诉"""
    user_message = state["messages"][-1].content
    prompt = f""" 用户投诉内容："{user_message}" 
    请以客服身份回复，表达歉意并提供解决方案。回复要温暖专业、
    """
    response = model.invoke(prompt)
    return {
        "result": response.content,
        "messages": [AIMessage(content=response.content)]
    }

# 2.3 处理咨询 inquiry
def handle_inquiry(state: RouterState) -> dict:
    """处理咨询"""
    user_message = state["messages"][-1].content
    prompt = f""" 用户咨询："{user_message}" 
    请简洁清晰的回答用户问题。如果不确定的，建议用户联系人工客服。
    人工客服电话：18244550000
    """
    response = model.invoke(prompt)
    return {
        "result": response.content,
        "messages": [AIMessage(content=response.content)]
    }

# 2.4 处理反馈 feedback
def handle_feedback(state: RouterState) -> dict:
    """处理反馈"""
    user_message = state["messages"][-1].content
    prompt = f""" 用户反馈："{user_message}" 
    请谦虚的接受反馈或建议，并感谢用户指出问题。
    """
    response = model.invoke(prompt)
    return {
        "result": response.content,
        "messages": [AIMessage(content=response.content)]
    }

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

# 定义 tool 函数（查询订单）
@tool
def query_order(order_id: int) -> str:
    """根据订单号查询订单信息
    Args:
        order_id: 订单号（整数）
    """
    for order in FAKE_DB["orders"]:
        if order["id"] == order_id:
            return (
                f"订单  #{order['id']} \n"
                f"用户：{order['user']} \n"
                f"商品：{order['product']} \n"
                f"金额：{order['amount']} \n"
                f"日期：{order['date']} \n"
            )
    return f"未找到订单号为：{order_id} 的订单。"


from langgraph.prebuilt import ToolNode
# 绑定工具到模型
model_with_tools = model.bind_tools([query_order])

# 2.5 新增 call_model 节点（LLM + tools）
def call_model(state: RouterState) -> dict:
    """LLM 节点： 分析用户需求，决定是否调用工具"""
    response = model_with_tools.invoke(state["messages"])
    if response.tool_calls:
        # 还需要调用工具，只追加消息
        return {"messages": [response]}
    else:
        return {
            "messages": [response],
            "result": str(response.content)
        }

# 工具节点
tool_node = ToolNode([query_order])

# 2.6 处理其他消息 other
def handle_other(state: RouterState) -> dict:
    """处理其它消息"""
    return {
        "result": "您好！我是小深助手。我可以帮您处理投诉反馈或解答问题咨询，请告诉我您需要什么帮助？"
    }

# 3. 定义路由条件
# 3.1 条件路由函数
def route_by_intent(state: RouterState) -> Literal["handle_complaint", "handle_inquiry", "handle_feedback", "handle_other", "call_model"]:
    """根据分类结果，返回下一个节点要执行的节点名"""
    intent = state.get("intent")
    user_message = state["messages"][-1].content
    # 关键：inquiry + 包含 “订单” 走 Tool 路线
    if intent == "inquiry" and "订单" in user_message:
        return "call_model"

    route_map = {
        "complaint": "handle_complaint",
        "inquiry": "handle_inquiry",
        "feedback": "handle_feedback"
    }
    return route_map.get(intent, "handle_other")

# 3.2 新增条件路由（判断是否调用工具）
def should_continue(state: RouterState) -> Literal["tools", END]:
    """检查 LLM 是否想调用工具"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

# 4. 构建图
graph = StateGraph(RouterState)

# 添加节点
graph.add_node("classify", classify_intent)
graph.add_node("handle_complaint", handle_complaint)
graph.add_node("handle_inquiry", handle_inquiry)
graph.add_node("handle_feedback", handle_feedback)
graph.add_node("handle_other", handle_other)
graph.add_node("call_model", call_model)
graph.add_node("tools", tool_node)

# 添加边
graph.add_edge(START, "classify")
graph.add_conditional_edges(
    "classify",
    route_by_intent,
    {
        "handle_complaint": "handle_complaint",
        "handle_inquiry": "handle_inquiry",
        "handle_feedback": "handle_feedback",
        "handle_other": "handle_other",
        "call_model": "call_model"
    }
)
graph.add_conditional_edges(                             # LLM 自主决定是否调用工具
    "call_model",
    should_continue,
    {"tools": "tools", END: END}
)
graph.add_edge("tools", "call_model")    # tools 执行完 ——> 回到 call_model（LLM 生成回复）

# 处理所有节点 -> END
graph.add_edge("handle_complaint", END)
graph.add_edge("handle_inquiry", END)
graph.add_edge("handle_feedback", END)
graph.add_edge("handle_other", END)

# 5. 记忆
memory = InMemorySaver()

# 编译
app = graph.compile(checkpointer=memory)

# 测试
async def main():
    print("=" * 50)
    print("🧪 客服路由图测试")
    print("=" * 50)

    test_case = [
        "帮我查一下订单 3 的状态",
        # "我买的商品有质量问题，用了两天就坏了！",
        # "请问退货流程是什么？",
        # "我提一个建议，我觉得你们公司的退货流程可以简化一下，退货流程有些复杂，对于中老年人不太优化。",
        # "很好，问题给我解决了！真不错"
    ]

    config = {"configurable": {"thread_id": "user-001"}}

    for i, test_input in enumerate(test_case, 1):
        result = app.invoke({
            "messages": [HumanMessage(content=test_input)],
            "intent": "",
            "result": ""},
            config=config
        )
        print(f"意图：{result['intent']}")
        print(f"回复：{result['result']}")

if __name__=="__main__":
    import asyncio
    asyncio.run(main())