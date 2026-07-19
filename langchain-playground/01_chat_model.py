"""
ChatModel 基础调用
===================
演示：创建模型 → 构造消息 → 调用模型

Java 对照：
    ChatLanguageModel model = DeepSeekChatModel.builder()
        .apiKey("sk-xxx")
        .modelName("deepseek-chat")
        .build();
    String reply = model.chat("你好");

运行前确保：
    1. 项目根目录 .env 文件中有 DEEPSEEK_API_KEY
    2. 已 pip install langchain langchain-deepseek
"""
import os
from dotenv import load_dotenv
load_dotenv()   # 加载 .env （必须在其他模块导入之前执行）
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# =========== 1. 创建模型实例 =============
model = ChatDeepSeek(
    model="deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.7,      # 温度 0~2，越高越随机
    max_tokens=2048       # 最大输出 token 数
)

# =========== 2. 最简单的调用：传一个字符串 =============
# .invoke() 是 LangChain 的统一调用接口
# 所有 Runnable 对象（模型、链、Agent）都用 .invoke()
response = model.invoke("你好！请用一句话介绍你自己。")
print(f"回复内容： {response.content}")        # 提取文本内容
print(f"回复类型： {type(response).__name__}")  # AIMessage
print(f"Token 用量： {response.usage_metadata}")   # {'input_tokens': ..., 'output_tokens': ..., 'total_tokens': ....}
print("=" * 50)

# ============= 3. 带消息角色的调用 =============
# LangChain 使用 Message 对象而非纯字符串
# SystemMessage  — 系统指令（定义 AI 的角色和行为）
# HumanMessage   — 用户输入
# AIMessage      — AI 回复
messages = [
    SystemMessage(content="你是一个 Python + Java 双栈的编程专家，回答时Python问题请用Java类比，回答Java问题请用Python类比。 回答要简洁，每个回答不超过3句话。"),
    HumanMessage(content="Python 的装饰器是什么？")
]
response = model.invoke(messages)
print(f"AI回复：{response.content}")
print("=" * 50)

# =============== 4. 多轮对话 （手动维护消息列表） ====================
print("\n ========= 多轮对话演示 ==========")

conversation = [
    SystemMessage(content="你是一个友好的助手")
]
# 第一轮
conversation.append(HumanMessage(content="我叫张三"))
response = model.invoke(conversation)
conversation.append(response)   # 把 AI 回复加入历史
print(f"AI：{response.content}")

# 第二轮
conversation.append(HumanMessage(content="我刚说我叫什么？"))
response = model.invoke(conversation)
conversation.append(response)
print(f"AI: {response.content}")

