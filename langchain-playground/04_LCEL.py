"""
LCEL — LangChain Expression Language
======================================
使用 | 操作符串联组件，构建数据处理管道

核心理念：一切皆 Runnable
    - ChatModel 是 Runnable
    - PromptTemplate 是 Runnable
    - OutputParser 是 Runnable
    - 用 | 串联后还是 Runnable（可以继续串联）

Java 对照：
    LCEL RunnableSequence ≈ LangChain4j 的 Chain
"""
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import(
    RunnableSequence,    # 串联
    RunnableParallel,    # 并行
    RunnableLambda,      # 自定义函数
    RunnablePassthrough  # 透传
)
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model = os.getenv("DEEPSEEK_MODEL"),
    base_url = os.getenv("DEEPSEEK_BASE_URL"),
    api_key = os.getenv("DEEPSEEK_API_KEY"),
    temperature = 0
)

# ========= 1. 基础连：prompt -> Model -> OutputParser ============
# 这是最经典的 LCEL 模式
prompt = ChatPromptTemplate.from_template("将以下内容翻译成{target_language}: \n\n{text}")
parser = StrOutputParser()

# | 操作符串联三个组件
chain = prompt | model | parser
#        ^^^^^^   ^^^^^   ^^^^^^
#        输入     处理     提取
# 数据流：
#   {"text": "...", "target_language": "英文"}
#   → prompt.invoke() → [SystemMessage, HumanMessage]
#   → model.invoke()  → AIMessage(content="...")
#   → parser.invoke() → "..."

result = chain.invoke({"text": "今天天气真好", "target_language": "英文"})
print(result)
print("=" * 50)

# ========== 2. RunnableParallel - 并行执行多个子链 ==============
# 同时做多件事，结果合并到一个 dict

# 定义两个子链
translate_chain = (
    ChatPromptTemplate.from_template("翻译成英文：{text}")
    | model
    | StrOutputParser()
)
summarize_chain = (
    ChatPromptTemplate.from_template("用5个字总结：{text}")
    | model
    | StrOutputParser()
)

# 并行执行！RunnableParallel 的 key ——> 子链名称，value -> 子链
parallel_chain = RunnableParallel(
    translation = translate_chain,    # 翻译
    summary = summarize_chain         # 总结
)

result = parallel_chain.invoke({"text": "人工智能旨在深刻改变我们的生活方式和工作模式"})
print(f"翻译：{result['translation']}")
print(f"总结：{result['summary']}")
print("=" * 50)

# ============ 3. RunnableLambda  - 插入自定义的 Python 函数 ==============
# 在 LCEL 链中插入任意 Python 处理逻辑
def count_words(text: str) -> dict:
    """自定义函数：统计字数"""
    word_count = len(text)
    return {"original": text, "word_count": word_count}

def is_long_text(data: dict) -> dict:
    """自定义函数：判断是否为长文本"""
    data["is_long"] = data["word_count"] > 50
    return data

# 把普通函数包装成 Runnable
chain_with_lambda = (
    prompt
    | model
    | parser
    | RunnableLambda(count_words)   # 统计字数
    | RunnableLambda(is_long_text)  # 判断长短
)
result = chain_with_lambda.invoke({"text": "你好世界", "target_language": "英文"})
print(result)
print("=" * 50)

# =========== 4. RunnablePassthrough + 链组合 - 高级模式
# 场景：RAG 检索 — 需要同时传递"检索到的文档"和"原始问题"
# 但 prompt 需要两个变量：context 和 question

# 输入只有 {"context": "...", "question": "..."}
# 但我们想要直接把 question 透传下去

rag_prompt = ChatPromptTemplate.from_template(
    "根据以下资料回答问题：\n\n{context}\n\n问题：{question}"
)
rag_chain = (
    # 把 context 传给 prompt，把 question 原样透传
    RunnableParallel(
        context=lambda x: x["context"],  # 处理context
        question=RunnablePassthrough()   # 透传question
    )
    | rag_prompt
    | model
    | StrOutputParser()
)

result = rag_chain.invoke({
    "context": "Python 是一种解释性、面向对象的高级编程语言",
    "question": "Python 是什么类型的语言"
})
print(result)

# ========= 5. .pipe() - 另一种串联方式 ============
# prompt.pipe(model).pipe(parser) 等价于 prompt | model | parser
# 在需要动态构建链时更灵活
chain2 = prompt.pipe(model).pipe(parser)