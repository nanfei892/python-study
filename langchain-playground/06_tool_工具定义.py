"""
LangChain Tool — 让 Agent 能调用外部函数
============================================
@tool 装饰器把普通 Python 函数变成 LLM 可调用的工具

Java 对照：`@tool` 装饰器 ≈ LangChain4j 的 `@Tool` 注解。方法签名一样，但 Python 用装饰器而非注解。
Java 对照：
    @Tool("计算两个数的和")
    public double add(double a, double b) { return a + b; }
"""
import math
from datetime import datetime

from langchain_core.tools import tool


# ========= 1. 基础 @tool 装饰器 ===========
@tool
def calculator(expression: str) -> str:
    """
    执行数学计算
    Args:
        expression: 数学表达式，如“2 + 3 * 4"、”sqrt(16)"、“sin(pi/2)"
    Returns:
        计算结果（字符串）
    """
    try:
        # eval() 执行字符串表达式（注意：生产环境需要做安全处理）
        # 这里限制只允许数学函数和数字
        allowed_names = {
            "abs": abs, "round": round, "max": max, "min": min,
            "sum": sum, "pow": pow, "sqrt": math.sqrt,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "pi": math.pi, "e": math.e
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"计算结果：{result}"
    except Exception as e:
        return f"计算出错：{str(e)}"

# ========== 2. 查询当前时间 ============
@tool
def get_current_time() -> str:
    """
    获取当前日期和时间。
    Returns:
        格式化当前日期时间字符串
    """
    now = datetime.now()
    return f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}，星期{['一', '二', '三', '四', '五', '六', '日'][now.weekday()]}"

# =========== 3. 带复杂参数的工具 ================
@tool
def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    在知识库中搜索相关内容。

    Args:
        query: 搜索查询
        top_k: 返回结果数量，默认 3

    Returns:
        搜索结果
    """
    # 模拟知识库数据
    knowledge = {
        "python": "Python 是一种解释型、面向对象的高级编程语言，由 Guido van Rossum 于 1991 年创建。",
        "fastapi": "FastAPI 是一个现代、高性能的 Python Web 框架，基于异步 I/O 和 Pydantic 数据验证。",
        "langchain": "LangChain 是一个用于构建 LLM 应用的框架，支持链式调用、Agent、RAG 等功能。",
        "docker": "Docker 是一个容器化平台，可以将应用及其依赖打包成容器，实现环境一致性。",
    }

    # 最简单的关键词匹配
    results = []
    for key, value in knowledge.items():
        if query.lower() in key.lower() or query.lower() in value.lower():
            results.append(f"- {key}: {value}")
        if not results:
            return f"未找到关于 '{query}' 的相关信息"
    return "\n".join(results[:top_k])

# =========== 4. 查看工具信息 ============
if __name__=="__main__":
    # 每个 @tool 函数都有一个 .name 和 .description 属性
    print(f"工具名：{calculator.name}")
    print(f"描述：{calculator.description}")
    print(f"参数：{calculator.args}")
    print()

    # 测试工具
    print(calculator.invoke("2 + 3 * 4"))
    print(get_current_time.invoke(""))
    print(search_knowledge_base.invoke({"query": "python"}))

