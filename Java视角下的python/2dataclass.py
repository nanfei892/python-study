"""
 Python dataclasses: 自动生成 __init__、__repr__、__eq__
 类似于 Java 14+ 的 record 类型

"""
from dataclasses import dataclass
from typing import Optional

# Java record:
# public record User(String name, int age, String email){}

@dataclass
class User:
    """用户数据类 - 自动生成构造器、toString、equals"""
    name: str
    age: int
    email: Optional[str] = None     # 可选字段，默认None

    def is_adult(self) -> bool:
        """自定义方法：判断是否成年"""
        return self.age >= 18

# ========= 使用示例 =============
user1 = User("zhangsan", 25, "zhangsan@example.com")
user2 = User(name="李四", age=16)    # email 有默认值 None

print(user1)
print(f"zhangsan成年了吗？ 回答 {user1.is_adult()}")   # True
print(f"李四成年了吗？ 回答 {user2.is_adult()}")   # False


"""
// 与Java 21 的等价写法
public record User(String name, int age, String email) {

    public User(String name, int age) {
        this(name, age, null);
    }

    public boolean isAdult() {
        return age >= 18;
    }
}

"""