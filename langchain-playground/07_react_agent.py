"""
ReAct Agent — 带工具的推理执行 Agent
========================================
ReAct = Reasoning（推理）+ Acting（执行）

工作流程：
    Human: "今天星期几？"
    → Thought: 我需要调用获取时间的工具
    → Action: get_current_time()
    → Observation: 当前时间：2026年7月16日
    → Thought: 我知道是星期几了
    → Answer: 今天是星期四

Java 对照：
    Agent 类似于 LangGraph4j 的 AiServices
    概念完全一样，只是 Python API 写法不同

LangChain 1.0 更新：
    ✅ create_agent（推荐） → 简洁、Middleware、stream_events
    ❌ create_react_agent（langgraph.prebuilt）→ 已废弃
    ❌ AgentExecutor → 已不需要，create_agent 返回可直接调用的对象
"""
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from tools_demo import calculator, get_current_time, search_knowledge_base

# =========== 1. 创建模型 ===========
model = ChatOpenAI(
    api_key = os.getenv("DEEPSEEK_API_KEY"),
    model=os.getenv("DEEPSEEK_MODEL"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0      # Agent需要推理，温度设为0
)

# ============= 2. 准备工具列表 ============
tools = [calculator, get_current_time, search_knowledge_base]

# =============== 3. 自定义 System Prompt ==============
system_prompt = """你是一个智能助手，可以使用工具来回答问题。
使用工具前请先判断是否真的需要。

可用工具：
- calculator：执行数学计算，传入数学表达式
- get_current_time：获取当前日期和时间
- search_knowledge_base：搜索知识库

规则：
1. 能用工具解决的问题就调用工具
2. 不需要工具的问题直接回答
3. 计算器只处理纯数学表达式，不要传自然语言进去
4. 回复用中文
"""

# ============== 4. 创建Agent ==============
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt
)

# 查看 Agent 结构
print(f"Agent 类型：{type(agent).__name__}")
print(f"Agent 底层是编译后的 LangGraph 图")
print("=" * 50)

# ============ 5. 运行 Agent ===================
async def test_agent():
    print("=" * 50)
    print("🧪 Agent 测试 — ReAct 推理循环")
    print("=" * 50)

    # 测试 1. 需要调用工具
    print("\n------- 测试 1： 计算 -----------")
    response = await agent.ainvoke({
        "messages": [HumanMessage(content="计算 123 * 456 + 789的结果")]}
    )
    #response["messages"] 包含完整的推理链（Thought -> Action -> Observation -> Final Answer)
    for msg in response["messages"]:
        print(f"[{msg.type.upper()}] {msg.content[:100]}...")

    # 测试 2: 获取时间
    print(f"\n------ 测试 2： 获取时间 -----------")
    response = await agent.ainvoke(
        {"messages": [HumanMessage(content="现在是几点？今天是星期几？")]}
    )
    # 最后一条消息就是最终回复
    final_answer = response["messages"][-1].content
    print(f"最终回复：{final_answer}")

    # 测试 3： 知识库搜索
    print("\n-------- 测试3： 知识库搜索 ------------")
    response = await agent.ainvoke(
        {"messages": [HumanMessage(content="关于 Python 有什么资料？")]}
    )
    print(f"最终回复：{response['messages'][-1].content}")

    # 测试 4：不需要工具的问题
    print("\n------ 测试4：常识问题(不需要工具) ------------")
    response = await agent.ainvoke(
        {"messages": [HumanMessage(content="地球绕太阳一圈需要多久？")]}
    )
    print(f"最终回复：{response['messages'][-1].content}")

if __name__=="__main__":
    import asyncio
    asyncio.run(test_agent())
