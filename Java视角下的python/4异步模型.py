"""
 Python 的异步模型和 Java 的 CompletableFuture 思路很相似，但语法简洁
 Python async/await: 异步 I/O 的核心语法
 类似于 Java 的 CompletableFuture + thenCompose()
"""

import asyncio
import time

# 模拟一个异步的 I/O 操作 （比如，调API、查数据库）
async def fetch_user(user_id: int) -> dict:
    """模拟异步获取用户信息"""
    print(f"[{time.strftime('%H:%M:%S')}] 开始获取用户 {user_id}")
    await asyncio.sleep(1)    # 模拟 1 秒 I/O 延迟(不阻塞主线程！)
    print(f"[{time.strftime('%H:%M:%S')}] 用户 {user_id} 获取完成")
    return {"id": user_id, "name": f"用户{user_id}"}

async def main():
    """主函数，展示并发获取多个用户"""
    # 1.顺序执行，一个个获取
    print("=========== 顺序执行 ================")
    start = time.time()
    user1 = await fetch_user(1)
    user2 = await fetch_user(2)
    user3 = await fetch_user(3)
    print(f"顺序执行耗时：{time.time() - start:.2f} 秒")   # 约3秒

    # 并发执行
    print("=========== 并发执行 ===========")
    start = time.time()
    results = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3)
    )
    print(f"并发执行耗时：{time.time() - start:.2f} 秒")    # 约1秒
    print(f"所有结果：{results}")

# 运行主函数
asyncio.run(main())

"""
Java 中等价写法
顺序：future1.thenCompose(r1 -> futrue2).thenCompose(r2 -> future3)
并发：CompletabelFuture.allOf(future1, future2, future3).join()

核心区别：
 Python 的 async/await 是语言级支持，写起来像同步代码；
 Java 用 CompletableFuture 链式调用
"""
