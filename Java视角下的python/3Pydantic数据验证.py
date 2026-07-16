"""
Pydantic 是 Python 生态中最重要的 数据验证库
FastAPI 用它做请求/响应校验。

Pydantic v2: 数据校验 + 序列化
类似于 Java 中的 @Valid 注解 + Jackson 序列化

注意 需要安装 pydantic。
执行安装命令：pip intall pydantic
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class CreateUserRequest(BaseModel):
    """创建用户的请求体模型（Java DTO + @Valid）"""
    name: str = Field(..., min_length=2, max_length=20, description="用户名")
    age: int = Field(..., gt=0, lt=150, description="年龄")
    email: str = Field(..., description="邮箱")
    bio: Optional[str] = Field(default=None, max_length=200, description="个人简介")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """自定义校验器：邮箱必须包含@  （Java @Email 注解）"""
        if "@" not in v:
            raise ValueError("邮箱格式不正确，必须包含 '@' ")

class UserResponse(BaseModel):
    """返回给客户端的用户模型  （Java VO）"""
    id: int
    name: str
    age: int
    email: str
    created_at: datetime

# ------------ 使用示例 --------------
# 1. 通过合法数据创建（相当于 Spring 自动做 @Valid 校验）
try:
    user = CreateUserRequest(
        name = "张三",
        age = 25,
        email = "zhangsan@example.com"
    )
    print(f"校验通过：{user.model_dump()}")    
    # .model_dump()  <---> Jackson ObejctMapper.writeValueAsString()
except Exception as e:
    print(f"校验失败：{e}")

# 2. 通过非法数据创建 (Pydantic 自动抛出 ValidationError)
try:
    user = CreateUserRequest(
        name = "张",        # 太短
        age = -1,           # -1
        email = "zhangexample.com"    # 没有 @
    )
except Exception as e:
    print(f"校验失败：{e}")
    # 输出类似： 3 validation errors fro CreateUserRequest

"""
// Java 的等价写法（Spring Boot）
public record CreateUserRequest(
    @NotBlank
    @Size(min = 2, max = 20)
    String name,
    
    @Min(1)
    @Max(150)
    int age, 

    @Email
    String email,

    @Size(max = 200)
    String bio        // nullable
){}
"""