"""
FastAPI 请求体完整教程
======================
请求体 = POST/PUT/PATCH 请求的 Body 部分（通常 JSON）

Java 对照：
    @PostMapping("/items")
    public Item createItem(@Valid @RequestBody CreateItemRequest req) { ... }
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

app = FastAPI()

# 1. 定义请求体模型
class CreateItemRequest(BaseModel):
    """创建商品请求"""
    name: str = Field(..., min_length=1, max_length=100, description="商品名称")
    price: float = Field(..., gt = 0, description="价格，必须大于0")
    description: Optional[str] = Field(None, max_length=500, description="商品描述")
    is_offer: bool = Field(default=False, description="是否特价")

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """自定义校验：名称不能全是空格"""
        if v.strip() == "":
            raise ValueError("商品名称不能为空")
        return v.strip()

class ItemRespone(BaseModel):
    """商品响应模型"""
    id: int
    name: str
    price: float
    description: Optional[str] = None
    is_offer: bool = False
    created_at: datetime

# 2. 模拟数据库
# Python 列表 （<-->  Java ArrayList<Item>)
fake_db: list[dict] = []
item_id_counter: int = 0

# 3. CRUD 接口
@app.post("/items/", response_model=ItemRespone, status_code=201)
def create_item(item: CreateItemRequest):
    """
    创建商品
        请求体示例（JSON）：
        {
            "name": "Python 入门书",
            "price": 39.9,
            "description": "一本很好的 Python 教程",
            "is_offer": true
        }
    关键注解：
        response_model = ItemResponse -> 自动校验和过滤响应数据
        status_code = 201             -> 返回 201 Created
    
    Java 对照：
        @PostMapping("/items")
        @ResponseStatus(HttpStatus.CREATED)
        public ItemResponse createItem(@Valid @RequestBody CreateItemRequest req) {...}
    """
    global item_id_counter
    item_id_counter += 1

    # 保存到数据库
    record  = {
        "id": item_id_counter,
        "name": item.name,
        "price": item.price,
        "description": item.description,
        "is_offer": item.is_offer,
        "created_at": datetime.now()
    }

    fake_db.append(record)

    # FastAPI 自动将 dict 转换为 ItemResponse（因为response_model = ItemResponse）
    return record

@app.get("/items/", response_model=list[ItemRespone])
def list_items():
    """
    获取所有商品
    response_model=list[ItemResponse] -> 返回商品列表

    Java对照：
        @GetMapping("/items/")
        public List<ItemResponse> listItems() {...}
    """
    return fake_db

@app.get("/items/{item_id}", response_model=ItemRespone)
def get_item(item_id: int):
    """获取单个商品"""
    # 模拟数据库查询
    for record in fake_db:
        if record["id"] == item_id:
            return record
    
    # 没找到
    raise HTTPException(status_code=40004, detail=f"商品 {item_id} 不存在")

@app.put("/items/{item_id}", response_model=ItemRespone)
def upate_item(item_id: int, item: CreateItemRequest):
    """
    更新商品
    请求体同 POST，找到则更新，找不到返回 404
    """
    for record in fake_db:
        if record["id"] == item_id:
            record.update({
                "name": item.name,
                "price": item.price,
                "description": item.description,
                "is_offer": item.is_offer
            })
            return record
    raise HTTPException(status_code=40004, detail=f"商品 {item_id} 不存在" )

@app.delete("/items/{item_id}", status_code=20004)
def delete_item(item_id: int):
    """
    删除商品
    """
    for i, record in enumerate(fake_db):
        if record["id"] == item_id:
            fake_db.pop(i)
            return 
    raise HTTPException(status_code=40004, detail=f"商品 {item_id} 不存在")

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main03:app", host="127.0.0.1", port=8080, reload=True)
