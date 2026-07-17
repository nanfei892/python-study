"""
FastAPI 查询参数
查询参数 = URL ? 后面的 key=value，多组用 & 分隔
Java 对照：
    @GetMapping("/search")
    public Result search(@RequestParam String keyword, 
                         @RequestParam(defaultValue="1") int page){...}

"""
from fastapi import FastAPI, Query
from typing import Optional, List

app = FastAPI()

# 1. 基础查询参数
@app.get("/search")
def search(keyword: str, page: int = 1):
    """
    基础搜索接口

    访问：/search?keyword=Python → {"keyword": "Python", "page": 1}
    访问：/search?keyword=Python&page=3 → {"keyword": "Python", "page": 3}
    访问：/search → 422 错误（keyword 是必填的！）
    """
    return {"keyword": keyword, "page": page}

# 2. 可选查询参数
@app.get("/items/")
def list_items(category: Optional[str] = None,      # 可选参数，默认 None 
               limit: int = 10):                     # 有默认值的参数也是可选参数      
    """
    商品列表接口 — 带可选筛选条件

    访问：/items/ → {"category": null, "limit": 10}
    访问：/items/?category=electronics&limit=5 → {"category": "electronics", "limit": 5}

    如果参数有默认值 → 可选
    如果参数没有默认值 → 必填
    """
    return {"category": category, "limit": limit}

# 3. Query 高级验证
@app.get("/users/")
def list_users(
    # age 参数：大于0，小于150
    age: int = Query(..., gt=0, lt=150, description="年龄"),
    # name 参数：最短 2 个字符，最长 20 个字符
    name: str = Query(None, min_length=2, max_length=20, description="用户名"),
    # 多值参数：可以传多次
    tags: List[str] = Query([], description="标签列表")
):
    """
    用户列表接口 — 演示 Query 的各种验证功能

    正常访问：/users/?age=25&name=张三&tags=python&tags=java
    异常访问：/users/?age=-1 → 422 错误（gt=0 限制）
    异常访问：/users/?age=25&name=张 → 422 错误（min_length=2）

    Query 常用参数：
        ...         - 必填（省略号）
        gt=0        - greater then 大于 0
        lt=150      - less then  小于 150
        ge=10       - greater or equal   大于等于 10
        le=10       - less or equal   小于等于 10
        min_length  - 最小长度 
        max_length  - 最大长度 
        regex="^..."   - 正则表达式
        desription    - 文档描述
        deprecated=True   - 标记为已弃用
    """
    return {"age": age, "name": name, "tags": tags}

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main02:app", host="127.0.0.1", port=8080, reload=True)