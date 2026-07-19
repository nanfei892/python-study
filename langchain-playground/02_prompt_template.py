"""
PromptTemplate — 提示词模板
=============================
将变量注入到预设的提示词中，实现 Prompt 的结构化管理

Java 对照：
    PromptTemplate.from("你是一个{role}，请回答：{question}")
    在 LangChain4j 中使用方式几乎一样
"""
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_deepseek import ChatDeepSeek

# ========= 1. 基础模版：字符串替换 ============
# 使用 {} 作为占位符，format() 方法填充
from langchain_core.prompts import PromptTemplate

template = PromptTemplate.from_template("将以下文本翻译成{target_language}：\n\n{text}")
# .format() 填充变量， ———>  返回最终 prompt 字符串
prompt_str = template.format(target_language="英文", text="你好，世界！")
print(f"生成的 Prompt：\n {prompt_str}")
print("=" * 50)

# ========= 2. 聊天模版：带消息角色的 prompt =========
# ChatPromptTemplate 是聊天场景的标准模板
# 支持 SystemMessage、HumanMessage、AIMessage 的模板化
chat_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}。回答风格：{style}。"),
    ("human", "{question}")
])
# .invoke()  传入变量 --> 返回消息列表（可直接传给模型）
messages = chat_template.invoke({
    "role": "Python编程导师",
    "style": "简洁明了，每段代码带注释",
    "question": "如何读取 CSV 文件？"
})
print("生成的模版消息：")
for msg in messages.messages:
    print(f" [{msg.type}] {msg.content}")
print("=" * 50)

# ========= 3. MessagePlaceholder: 多轮对话的“历史消息槽位”===================
# 这是 LangChain 最常用的模式之一
# 在模版中预留一个位置，用来插入任意数量的历史消息
chat_with_history = ChatPromptTemplate.from_messages([
    ("system", "你是一个有用的助手"),
    # MessagesPlaceholder - 历史消息的占位符（列表！）
    # 变量名 “history” 会在调用时被替换为消息列表
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])
# 模拟历史消息
history = [
    HumanMessage(content="你好！"),
    AIMessage(content="你好！有什么可以帮助你的吗？")
]

# 注入历史
messages = chat_with_history.invoke({
    "history": history,
    "input": "我刚才说了什么？"
})
print("带历史的模版消息：")
for msg in messages.messages:
    print(f" [{msg.type}] {msg.content}")
