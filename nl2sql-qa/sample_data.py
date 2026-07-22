"""示例数据生成"""
"""
生成示例业务数据库
===================
模拟一个电商系统的数据库：
    users     — 用户表
    products  — 商品表
    orders    — 订单表
    order_items — 订单明细表

运行此脚本即创建 sample_data.db 并填充测试数据
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "sample_data.db")


def create_sample_database():
    """创建示例数据库并插入测试数据"""

    # 删除旧数据库（重新生成）
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ============================================
    # 创建表
    # ============================================

    # 用户表
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            city VARCHAR(50),
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vip_level INTEGER DEFAULT 0
        )
    """)

    # 商品表
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            category VARCHAR(50) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 订单表
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 订单明细表
    cursor.execute("""
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # ============================================
    # 插入测试数据
    # ============================================

    # 用户数据（10 条）
    users = [
        ("张三", "zhangsan@example.com", "13800001001", "北京", "2026-01-15", 2),
        ("李四", "lisi@example.com", "13800001002", "上海", "2026-02-20", 1),
        ("王五", "wangwu@example.com", "13800001003", "广州", "2026-03-10", 0),
        ("赵六", "zhaoliu@example.com", "13800001004", "深圳", "2026-03-15", 3),
        ("孙七", "sunqi@example.com", "13800001005", "杭州", "2026-04-01", 1),
        ("周八", "zhouba@example.com", "13800001006", "成都", "2026-04-20", 0),
        ("吴九", "wujiu@example.com", "13800001007", "武汉", "2026-05-05", 2),
        ("郑十", "zhengshi@example.com", "13800001008", "南京", "2026-05-15", 0),
        ("钱十一", "qianshiyi@example.com", "13800001009", "北京", "2026-06-01", 1),
        ("陈十二", "chenshier@example.com", "13800001010", "上海", "2026-06-10", 0),
    ]
    cursor.executemany(
        "INSERT INTO users (username, email, phone, city, registered_at, vip_level) VALUES (?,?,?,?,?,?)",
        users,
    )

    # 商品数据（15 条）
    products = [
        ("Python 编程入门", "图书", 59.00, 100, "适合初学者的 Python 教程"),
        ("机械键盘 K8", "外设", 399.00, 50, "Cherry 青轴，87 键"),
        ("27寸 4K 显示器", "外设", 2499.00, 20, "IPS 面板，Type-C 接口"),
        ("无线鼠标 M3", "外设", 149.00, 80, "人体工学设计，蓝牙 5.0"),
        ("数据线 USB-C", "配件", 29.00, 200, "1m 长度，支持快充"),
        ("笔记本电脑支架", "配件", 89.00, 60, "铝合金材质，可折叠"),
        ("TypeScript 实战", "图书", 69.00, 80, "前端进阶必读"),
        ("机械键盘 K2", "外设", 349.00, 40, "红轴，84 键紧凑设计"),
        ("32寸 曲面屏", "外设", 1899.00, 15, "2K 分辨率，165Hz 刷新率"),
        ("蓝牙耳机 E3", "配件", 299.00, 70, "主动降噪，续航 30 小时"),
        ("Java 核心技术", "图书", 99.00, 50, "Java 开发者必读经典"),
        ("电竞椅 Pro", "家具", 1299.00, 10, "人体工学，透气网布"),
        ("桌面台灯", "家具", 199.00, 45, "LED 护眼，无极调光"),
        ("USB 集线器", "配件", 59.00, 90, "7 口 USB 3.0"),
        ("移动硬盘 1TB", "存储", 399.00, 35, "USB 3.2，轻薄便携"),
    ]
    cursor.executemany(
        "INSERT INTO products (name, category, price, stock, description) VALUES (?,?,?,?,?)",
        products,
    )

    # 订单数据（20 条）
    orders = [
        (1, 458.00, "completed", "2026-07-01"),
        (1, 2499.00, "completed", "2026-07-02"),
        (2, 548.00, "completed", "2026-07-03"),
        (3, 69.00, "pending", "2026-07-05"),
        (4, 2798.00, "completed", "2026-07-06"),
        (5, 328.00, "shipped", "2026-07-07"),
        (6, 2499.00, "completed", "2026-07-08"),
        (2, 448.00, "pending", "2026-07-09"),
        (7, 59.00, "completed", "2026-07-09"),
        (1, 399.00, "shipped", "2026-07-10"),
        (8, 99.00, "completed", "2026-07-10"),
        (4, 1299.00, "pending", "2026-07-11"),
        (3, 408.00, "completed", "2026-07-12"),
        (5, 1899.00, "cancelled", "2026-07-12"),
        (9, 548.00, "completed", "2026-07-13"),
        (2, 199.00, "shipped", "2026-07-13"),
        (6, 458.00, "completed", "2026-07-14"),
        (10, 2499.00, "pending", "2026-07-14"),
        (1, 89.00, "completed", "2026-07-15"),
        (7, 1399.00, "completed", "2026-07-15"),
    ]
    cursor.executemany(
        "INSERT INTO orders (user_id, total_amount, status, created_at) VALUES (?,?,?,?)",
        orders,
    )

    # 订单明细（部分订单有明细）
    order_items = [
        (1, 1, 1, 59.00), (1, 4, 1, 149.00), (1, 6, 1, 29.00), (1, 10, 1, 299.00),
        (2, 3, 1, 2499.00),
        (3, 2, 1, 399.00), (3, 4, 1, 149.00),
        (4, 7, 1, 69.00),
        (5, 3, 1, 2499.00), (5, 10, 1, 299.00),
        (6, 4, 1, 149.00), (6, 10, 1, 299.00),
        (7, 3, 1, 2499.00),
        (8, 2, 1, 399.00), (8, 8, 1, 349.00),
        (9, 5, 1, 29.00), (9, 14, 1, 59.00),
        (10, 15, 1, 399.00),
        (11, 11, 1, 99.00),
        (12, 12, 1, 1299.00),
        (13, 4, 1, 149.00), (13, 11, 1, 99.00), (13, 7, 1, 69.00),
        (14, 9, 1, 1899.00),
        (15, 2, 1, 399.00), (15, 4, 1, 149.00),
        (16, 13, 1, 199.00),
        (17, 1, 1, 59.00), (17, 2, 1, 399.00),
        (18, 3, 1, 2499.00),
        (19, 6, 1, 89.00),
        (20, 11, 1, 99.00), (20, 12, 1, 1299.00),
    ]
    cursor.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?,?,?,?)",
        order_items,
    )

    conn.commit()
    conn.close()

    print(f"✅ 示例数据库已创建：{DB_PATH}")
    print(f"   - users 表：{len(users)} 条数据")
    print(f"   - products 表：{len(products)} 条数据")
    print(f"   - orders 表：{len(orders)} 条数据")
    print(f"   - order_items 表：{len(order_items)} 条数据")


if __name__ == "__main__":
    create_sample_database()