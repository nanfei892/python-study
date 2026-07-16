"""
 Python 异常处理：tyr/except/else/finally
 Java 异常处理：try/catch/finally
"""

def divide(a: int, b: int) -> float:
    """安全除法，演示异常处理"""
    try:
        result = a / b
    except ZeroDivisionError:
        print("错误：除数不能为 0！")     # 捕获特定异常
        return 0.0
    except TypeError as e:
        print(f"类型错误：{e}")
        return 0.0
    except Exception as e:
        print(f"未知错误：{e}")
        return 0.0
    else:
        print("计算成功！")       # try 无异常时执行（Java中没有）
    finally:
        print("清理工作完成")