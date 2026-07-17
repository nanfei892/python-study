"""
FastAPI 路径参数，类似于 SpringBoot中的 @PathVariable
Java 对照：
    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id){...}
"""

from fastapi import FastAPI
app = FastAPI()

#示例 1. 基础路径参数
@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    获取单个用户
        访问：/users/123 -> {"user_id": 123}
        访问：/users/abc -> 422 错误，应为user_id 有类型验证，必须为int
    Java 对照：
        @GetMapping("/users/{id}")
        public User getUser(@PathVariable Long id){...}
    """
    return {"user_id": user_id}


# 示例 2. 多个路径参数
@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(user_id: int, post_id: int):
    """
    注意：函数参数名必须与路径中的 {变量名} 一致
    """
    return {"user_id": user_id, "post_id": post_id}

# 示例 3. 路径参数 + 类型转换
@app.get("/products/{product_id}")
def get_product(product_id: int):
    """
    获取商品信息 — 演示 FastAPI 自动类型转换
    访问 /products/100 → {"product_id": 100, "type": "int"}
    访问 /products/abc → 422 Unprocessable Entity（自动校验！）
    这就是 Pydantic + 类型注解的威力 —— 不用手写 if (!id.matches("\\d+"))
    """
    return {"procuct_id": product_id, "type": str(type(product_id).__name__)}

# 示例 4. 枚举类型路径参数
from enum import Enum

class Color(str, Enum):
    """颜色枚举 - 限制参数只能是特定值"""
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

@app.get("/colors/{color}")
def get_color(color: Color):
    """
    获取颜色信息 — 枚举类型自动校验

    访问 /colors/red   → {"color": "red", "message": "有效的颜色"}
    访问 /colors/yellow → 422 错误（不在枚举中！）

    Java 对照：
        @GetMapping("/colors/{color}")
        public Map<String, String> getColor(@PathVariable Color color) { ... }
    """
    return {"color": color.value, "message": "颜色有效！"}

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main01:app", host="127.0.0.1", port=8080, reload=True)