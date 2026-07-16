# ===================================================================
# 概念：类型注解(Type Hints)  <---->  Java中的类型声明

# 语法：Python 类型注解。  写在变量名后，用冒号
# ===================================================================

# Java： String name = "张三";
name: str = "张三"

# Java：int age = 20;
age: int = 20

# Java：List<String> items = new ArrayList<>();
from typing import List
items: List[str] = ["apple", "banban"]

# Java：Map<String, Object> config = new HashMap<>();
from typing import Dict, Any
config: Dict[str, Any] = {"host": "localhost", "port": 8000}

# Java：Optional<String> maybeName = Optional.ofNullabel(null);
from typing import Optional
maybe_name: Optional[str] = None    # Python 3.10 前的写法
maybe_name2: str | None             # Python 3.10 + 以后可以写成 str | None\

"""
Python 的类型注解不会再运行时强制检查，
但是在IDE（VSCode/PyCharm）和FastAPI/Pydantic 会利用它们做自动补全和运行时验证
"""
