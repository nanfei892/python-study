"""
Structured Output — 让 LLM 直接返回结构化对象
================================================
LangChain 1.0 的方式：model.with_structured_output()
底层利用模型的 tool calling 能力，自动保证输出符合你的 Pydantic 模型。

旧方式（PydanticOutputParser，不推荐）：
    Pydantic Model → parser.get_format_instructions() → 手动注入 Prompt
    → LLM 返回文本 → parser.invoke() 手动解析 → Pydantic 对象
    问题：依赖 prompt 遵守，格式错误率高，token 浪费多

新方式（with_structured_output，⭐ 推荐）：
    Pydantic Model → model.with_structured_output() → invoke() → Pydantic 对象
    优势：模型原生保证、无格式指令浪费、更可靠

Java 对照：
    LangChain4j 用 AiServices 接口自动映射返回值类型
    Python 1.0 的 with_structured_output 概念几乎一样
"""

import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
from pydantic import BaseModel, Field
from typing import List
from langchain.chat_models import init_chat_model
# from langchain_openai import ChatOpenAI

model = init_chat_model(
    model="qwen3.6-flash",
    model_provider="openai",
    api_key=os.getenv("QW_API_KEY"),
    base_url="https://llm-5ppsxufa7637b8mq.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    extra_body={"enable_thinking": False}
)

# ====== 1. StrOutputParser - 提取纯文本回复 =========
# 最简单的解析器：AIMessage.content - str
parser_str = StrOutputParser()

# 直接和模型串联
# model | parser 的意思是：model 的输出 -> parser 的输入
chain = model | parser_str
#     ^^^^^   ^^^^^^^^^^^
#     LLM 调用   提取纯文本
result = chain.invoke("什么是Python？用一句话解答")
print(f"纯文本回复： {result}")
print(f"结果类型： {type(result)}")
print("=" * 50)

# 2. ======= with_structured_output() - 结构化输出
# 第一步：定义你想要的输出结构（Pydantic Model）
class MovieReview(BaseModel):
    """影评结构"""
    title: str = Field(description="电影名称")
    director: str = Field(description="导演姓名")
    rating: float = Field(description="评分，1-10 分")
    summary: str = Field(description="一句话总结")
    pros: List[str] = Field(description="优点列表")
    cons: List[str] = Field(description="缺点列表")

# 第二步：一行创建结构化模型
# with_structured_output()  利用模型 toll calling 能力自动保证输出格式
structured_model = model.with_structured_output(MovieReview, method="function_calling")

# 第三步：直接调用，返回的就是 Pydantic 对象
result = structured_model.invoke("请评价电影《肖申克的救赎》")
print(f"电影名称：{result.title}")
print(f"导演：{result.director}")
print(f"评分：{result.rating}/10")
print(f"总结：{result.summary}")
print(f"优点：{result.pros}")
print(f"缺点：{result.cons}")
print(f"结果类型：{type(result).__name__}")  # MovieReview — 直接就是 Pydantic 对象！
print("=" * 50)

# 也可以在 LCEL 链中：
from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个电影评论分析助手。请根据用户提供的电影名称，输出结构化影评"),
    ("human", "{movie_name}")
])
chain = prompt | structured_model
result = chain.invoke({"movie_name": "肖申克的救赎"})
print(f"LCEL链：{result}")
print("=" * 50)

# 需要同时获取原始 AIMessage（含 token 用量）？用 include_raw=True
structured_model_with_raw = model.with_structured_output(MovieReview, method="function_calling", include_raw=True)
response = structured_model_with_raw.invoke("请评价肖申克的救赎")
print(response["parsed"])                 # MovieReview 对象
print(response["raw"].usage_metadata)     # token 用量
