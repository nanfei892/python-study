"""
 httpx.AsyncClient: Python 的异步 HTTP 客户端
 类似于 Java 的 WebClient (Spring WebFlux) 或 OkHttp

 需要安装 HTTPX
 安装命令：npm install httpx
"""
import httpx
import asyncio

async def call_api_example():
    """演示：用httpx 调用外部 API"""
    # 创建一个异步 HTTP 客户端 （类似于 WebClient.builder().build()）
    async with httpx.AsyncClient() as client:
        try:
            # GET请求 （类似 webClient.get().retrieve()）
            response = await client.get(
                "https://httpbin.org/json",
                timeout=10.0    # 10秒超时
            )
            # 检查 HTTP 状态码
            response.raise_for_status()    # 4xx/5xx，会抛异常。（类似于onStatus(HttpStatus::isError)
            # 解析JSON（response.json() 类似于 Jackson readValue()）
            data = response.json()
            print(f"请求成功！状态码：{response.status_code}")
            print(f"相应数据：{data}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP错误： {e}")
        except httpx.TimeoutException:
            print("请求超时！")
        except Exception as e:
            print(f"未知错误：{e}")

asyncio.run(call_api_example())


