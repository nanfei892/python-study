"""
 DeepSeek API 异步客户端
 综合练习：async/await、Pydantic、httpx、异常处理、类型注解
 运行方式：
  先确保 venv 已激活，然后：
   cd fastapi-starter
   python llm_client.py

Java 对照:
 这个脚本相当于你写了 LLM 调用个工具类，
 类似于 Java 中用 WebClient 封装 OpenAI API 调用。
"""

import os
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 1. 加载 .env 文件中的环境变量
#    load_dotenv() 会从项目根目录的 .env 文件读取配置
#    类似于 Spring Boot 读取 application.properties
load_dotenv()

# 2. 用 dataclass 定义配置对象 （Java record / @ConfigurationProperties）
@dataclass
class LLMConfig:
    """LLM 配置"""
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-flash"
    max_tokens: int = 2048
    temperature: float = 0.7

# 从环境变量读取配置
# os.getenv("KEY", "默认值") 类似于Java的 System.genenv("KEY", "default")
config = LLMConfig(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
)

# 3. 用 Pydantic 定义请求/响应模型 （Java DTO）
class ChatMessage(BaseModel):
    """一条聊天消息"""
    role: str = Field(..., description="角色：system / user / assistant")
    content: str = Field(..., description="消息内容")

class ChatRequest(BaseModel):
    """发送给 API 的请求体"""
    model: str
    messages: List[ChatMessage]
    max_tokens: int = 2048
    temperatur: float = 0.7

class TokenUsage(BaseModel):
    """Token 用量信息"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatChoice(BaseModel):
    """API 返回的选择项"""
    message: ChatMessage

class ChatResponse(BaseModel):
    """API 返回的完整响应"""
    id: str = ""
    choices: List[ChatChoice] = []
    usage: Optional[TokenUsage] = None

# 4. 核心： 异步 LLM 客户端类
class DeepSeekClient:
    """
    DeepSeek API 客户端

    Java 对照：
        类似于你写的一个 @Service 类
        内部用 WebClient 调用 Deepseek API，
        返回 Mono<ChatResponse>
    """
    def __init__(self, config: LLMConfig):
        """
        构造器 - 类似于 Java 的 @Autowired 构造器注入
        Args:
            config: LLM 配置对象
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端（懒初始化）"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._client
    
    async def chat(
            self,
            messages: List[ChatMessage],
            temperature: Optional[float] = None
    ) -> ChatResponse:
        """
        发送聊天请求（非流式，一次性返回完整内容）
        Args:
            message: 消息列表
            temperature: 温度参数（0~2，越高月随机，不传就默认值）

        Returns:
            ChatResponse 对象
        
        Raises: 
            httpx.HTTPStatusError: API 返回错误状态码
            httpx.TimeoutException: 请求超时
        """
        client = await self._get_client()

        # 构造请求体
        request_body = ChatRequest(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperatur=temperature if temperature is not None else self.config.temperature
        )

        try:
            # 发送 POST 请求到 /chat/completions
            # 注意：base_url 已经包含了 https://api.deepseek.com，所以路径是 /chat/completions
            response = await client.post(
                "/chat/completions",
                json=request_body.model_dump(),    # model_dump() <--> Jackson   序列化
            )
            response.raise_for_status()

            # 解析响应 JSON 为 Pydantic 模型（model_validata <-> Jackson 反序列化）
            result = ChatResponse.model_validate(response.json())
            return result
        
        except httpx.HTTPStatusError as e:
            # HTTP 4xx/5xx 错误，
            print(f"[API 错误] HTTP {e.response.status_code}: {e.response.text}")
            raise
        except httpx.TimeoutException as e:
            print(f"[API 错误] 请求超时（30秒）")
            raise
        except Exception as e:
            print(f"[API 错误] 未知错误：{type(e).__name__}: {e}")
            raise
    
    async def chat_stram(self, messages: List[ChatMessage], temperature: Optional[float]=None):
        """
        发送聊天请求：流式。
        这是 python 的异步生成器(async generator):
         - yield 类似于 Java 中返回的 Flux<T>，逐条推送数据
         - 用 async for 消费，类似于 Flux.subscribe()
        """
        client = await self._get_client()

        request_body = ChatRequest(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperatur=temperature if temperature is not None else self.config.temperature
        )

        try:
            async with client.stream(
                "POST",
                "/chat/completions",
                json = {
                    **request_body.model_dump(),
                    "stream": True,   # 关键：开启流失输出
                },
            ) as response:
                response.raise_for_status()

                # 逐行读取 SSE（Server-Sent Events）流
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]    # 去掉 "data: " 前缀
                        if data == "[DONE]":
                            break

                        # 这里可以解析 JSON 并提取 delta.content
                        import json
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content   # 逐字产出
        except httpx.HTTPStatusError as e:
            print(f"[API错误] HTTP {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            print(f"[API错误] {type(e).__name__}: {e}")
            raise
    async def close(self):
        """关闭 HTTP 客户端，释放连接资源"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


# 5. 测试
async def main():
    """测试 Deepseek 客户端"""
    print("=" * 50)
    print("🚀 Deepseek 客户端测试")
    print("=" * 50)

    # 检查 API Key 是否配置
    if not config.api_key:
        print("\n ⚠️ 请现在 .env 文件中配置 DEEPSEEK_API_KEY！")
        print("访问 https://platform.deepseek.com/ 获取API Key")
        return
    
    # 创建客户端
    client = DeepSeekClient(config)
    try:
        #------ 测试1. 非流式调用------
        print(f"\n 📃 测试1：非流式调用")
        print("-" * 40)

        messages = [
            ChatMessage(role="system", content="你是一个 Python 编程助手，回答简洁明了。"),
            ChatMessage(role="user", content="用一句话解释 Python 的 async/await")
        ]

        response = await client.chat(messages)
        reploy = response.choices[0].message.content
        print(f"☁️  AI 回复：{reploy}")

        if response.usage:
            print(f"📊  Token 用量："
                  f"输入 {response.usage.prompt_tokens} + "
                  f"输出 {response.usage.completion_tokens} = "
                  f"总计 {response.usage.total_tokens}")

        # 测试2：流式调用
        print("\n 📃 2： 流式调用")
        print("-" * 40)

        messages2 = [
            ChatMessage(role="user", content="用一句话解释 Python 的类型注解。")
        ]

        print("☁️  AI 回复：", end="", flush=True)
        async for token in client.chat_stram(messages2):
            print(token, end="", flush=True)
        print()
    finally:
        await client.close()

    print("\n ✅️   测试完成！")

# python 的入口点判断（类似于 Java 的 public static void main)
if __name__ == "__main__":
    """
    __name__ == "__main__" 是Python惯用写法：
    - 直接运行此文件（python llm_client.py）时，__name__ 为 "__main__"，执行asyncio.run()
    - 被别人 import 时，__name__ 为模块名，不执行入口代码。

    Java 对照：
        if __name__ == "__main__"类似于：
        public static void main(String[] args){...}
    """
    asyncio.run(main())