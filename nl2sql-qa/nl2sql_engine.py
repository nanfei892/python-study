"""NL2SQL 核心引擎（⭐ 核心）"""
"""
Schema 提取 — NL2SQL 系统最关键的一步！
==========================================
LLM 需要知道数据库中有哪些表和字段，才能写出正确的 SQL。
这个函数的作用就是：读取数据库元数据 → 生成 LLM 可理解的 DDL 描述。

Java 对照：
    类似于读取 JDBC DatabaseMetaData → 拼成 System Prompt
"""
import sqlite3
from typing import List

def extract_schema(db_path: str) -> str:
    """
    提取 SQLite 数据库的完整 Schema

    从 sqlite_master 系统表读取所有用户表的 DDL
    并补充每条表的示例数据（帮助 LLM 理解字段含义）

    Args:
        db_path: SQLite 数据库文件路径

    Returns:
        格式化的 Schema 描述文本，可直接注入 System Prompt
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. 获取所有用户表名（排除 sqlite_ 系统表）
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'sqlite%'"
    )
    tables = [row[0] for row in cursor.fetchall()]

    schema_parts = []

    for table_name in tables:
        # 2. 获取表结构（DDL）
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        ddl = cursor.fetchone()[0]

        # 3. 获取字段信息（更清晰的格式）
        cursor.execute(f"PRAGMA table_info('{table_name}') ")
        columns = cursor.fetchall()
        # PRAGMA table_info 返回：(cid, name, type, notnull, dflt_value, pk)

        col_description = []
        for col in columns:
            cid, name, col_type, notnull, dflt_value, pk = col
            desc_parts = [f"{name} {col_type}"]
            if pk:
                desc_parts.append("PRIMARY KEY")
            if notnull:
                desc_parts.append("NOT NULL")
            if dflt_value is not None:
                desc_parts.append(f"DEFAULT {dflt_value}" )
            col_description.append(" ".join(desc_parts))

        # 4. 获取示例数据（前三条）
        try:
            cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 3")
            sample_rows = cursor.fetchall()
            col_names = [col[1] for col in columns]
            sample_lines = ["示例数据（前3条）"]
            for row in sample_rows:
                sample_lines.append(f"{dict(zip(col_names, row))}")
        except Exception:
            sample_lines = [" (无法获取示数据) "]

        # 5. 组合
        schema_parts.append(
            f"表名：{table_name}\n"
            f"字段：\n{chr(10).join(col_description)}\n"
            f"{chr(10).join(sample_lines)}\n"
            f"{'=' * 50}"
        )

    conn.close()

    return "\n\n".join(schema_parts)

if __name__=="__main__":
    # 测试 Schema 提取
    schema = extract_schema("sample_data.db")
    print(schema)