"""
    FastAPI是基于 Starletee（异步Web框架）和Pydantic（数据库验证）
    与Java对照：FastAPI ≈ SpringBoot + @Valid + Swagger
核心优势：
    高性能，基于异步 I/O，性能接近Node.js 和 Go
    类型提示：利用 Python 类型注解自动做数据验证
    自动文档：内置 Swagger UI 和 ReDoc，无需额外配置
    异步支持：原生 async/await，适合高并发场景
"""

"""
 第一个 FastAPI 应用
 运行方式：
    cd fastapi-starter
    python main.py
    或
    uvicorn main:app --reload

 访问：
    Swagger UI：http://127.0.0.1:8000/docs
    ReDoc: http://127.0.0.1:8000/redoc
    接口： http://127.0.0.1:8000/
"""

# 1. 导入 FastAPI 类  （↔ import org.springframework.boot.SpringApplication）
from fastapi import FastAPI

# 2. 导入 uvicorn （ASGI服务器  <--> Tomcat/Netty）
import uvicorn

# 3. 创建 FastAPI 应用实例 （SpringApplication.runU() 创建的 ApplicationContext）
# title 参数会显示在Swagger 文档顶部
# version 参数会显示在 Swagger 文档中
app = FastAPI(
    title="python 学习项目",
    description="第一个FastAPI 应用",
    version="0.1.0"
)

# 4. 定义路由 （ <--> @GetMapping("/")）
# @app.get("/") 这是pyhton 的装饰器语法 （<--> Java注解 @GetMapping("/")）
# 告诉 FastAPI：当有人 GET 访问 / 路径时，调用这个函数
@app.get("/")
def read_root():
    """
    根路径处理函数 -- 返回欢迎消息
    Java 对照：
        @GetMapping("/")
        public Map<String, String> readRoot() {
            return Map.of("Hello", "world")
        }
    """
    # FastAPI 会自动将 dict 序列化为 JSON 响应
    return {"Hello": "World", "message": "欢迎来到FastAPI！"}

# 5. 启动服务器
if __name__=="__main__":
    """
    uvicorn.run() 参数说明：
        "main:app"   - 格式为 "文件名：FastAPI实例名"
        host:        - 监听地址，0.0.0.0 表示所有网卡（局域网可访问）
        port         - 端口号
        reload       - 开启热重载（代码修改后自动重启，开发用，生产关闭）
        debug        - 开启调试模式
    """
    uvicorn.run(
        app="main:app",      # 指定模块和应用实例
        host="127.0.0.1",    # 只监听本机
        port=8080,           # 端口
        reload=True          # 热重载（类似于 SpringBoot DevTools）
    )

"""
启动方式：
 方式一：直接运行python 脚本
    cd fastapi-starter
    python main.py
 方式二：使用 uvicorn 命令
    cd fast-starter
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
 方式三：使用 fastapi 命令（开发模式）
    cd fastapi-starter
    fastapi def main.py
"""