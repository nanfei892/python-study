"""
LCEL 多轮对话机器人
=====================
使用 RunnableWithMessageHistory 自动管理对话历史

这是 LangChain 中最实用的模式之一：
    你不需要手动维护消息列表！
    RunnableWithMessageHistory 自动帮你：
        - 从存储中加载历史消息
        - 把新消息加入历史
        - 保存更新后的历史

Java 对照：
    类似 LangChain4j 的 ChatMemory + AiServices 自动管理
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
import asyncio

load_dotenv()

# ============ 1.构建 Prompt  ===============
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的AI助手，你的名字叫小深。"),
    MessagesPlaceholder(variable_name="history"),     # 历史消息插槽
    ("human", "{input}")
])

# ============== 2. 构建基础链 ==============
model = ChatOpenAI(
    model="deepseek-v4-flash",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.7
)
base_chain = prompt | model | StrOutputParser()

# ========== 3. 对话历史存储 ===============
# 用字典管理多个会话历史（session_id -> 消息列表）
store: dict[str, InMemoryChatMessageHistory] = {}
def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """
    获取或创建指定 session 的历史记录
    session_id 类似于 HTTP 的 session cookie
    不同 session_id 对应不同的对话上下文
    """
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# =========== 4. 包装为带历史的链 ==============
chain_with_history = RunnableWithMessageHistory(
    base_chain,
    get_session_history,    # 历史获取函数
    input_messages_key="input",    # 输入变量名 input
    history_messages_key="history"    # 历史变量名 history
)

# ====== 5. 使用 =============
async def main():
    # 配置固定一个session 测试多轮对话
    config = {"configurable": {"session_id": "user_001"}}

    # 第一轮
    response1 = chain_with_history.invoke(
        {"input": "我叫张三，我喜欢编程"},
        config=config
    )
    print(f"Round 1： {response1}\n")

    # 第二轮（历史自动加载！无需手动管理消息列表）
    response2 = chain_with_history.invoke(
        {"input": "我刚才说我叫什么？我喜欢什么？"},
        config=config
    )
    print(f"Round 2： {response2}\n")

    # 检查历史内容
    history = get_session_history("user_001")
    print(f"历史消息数量： {len(history.messages)}")

asyncio.run(main())