"""SQL 安全控制"""
"""
SQL 安全控制
=============
NL2SQL 系统的安全带 — 防止 LLM 生成危险的 SQL

核心原则：
    只允许 SELECT 和 PRAGMA 语句！
    其他的全部拦截。

Java 对照：
    类似于 SQL 防火墙 / 只读连接
"""
import re

# 危险 SQL 关键词黑名单
# 注意：检查的是“去除空白后的 SQL 头部”
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "CREATE", "TRUNCATE", "REPLACE", "GRANT", "REVOKE",
    "ATTACH", "DETACH", "VACUUM", "REINDEX"
]
def validate_sql(sql: str) -> tuple[bool, str]:
    """
    校验 SQL 是否安全

    Args:
        sql: LLM 生成的 SQL 语句

    Returns：
        （是否安全，原因说明）
    """
    # 1. 基本清理：去除注释和多余空白
    cleaned = sql.strip()

    # 去除单行注释
    cleaned = re.sub(r'--.*$', '', cleaned, flags=re.MULTILINE)
    # 去除多行注释
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

    # 2. 检查是否以 SELECT 或 PRAGMA 开头（不区分大小写）
    first_word = cleaned.strip().split()[0].upper() if cleaned.strip() else ""

    if first_word not in ("SELECT", "PRAGMA", "EXPLAIN", "WITH"):
        return False, f"只允许 SELECT/PRAGMA/EXPLAIN/WITH 查询， 检测到：{first_word}"

    # 3. 检查是否包含禁止关键词
    # 用单词边界匹配，避免误判（如 SELECT 中的 "INSERT" 不算）
    for keyword in FORBIDDEN_KEYWORDS:
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, cleaned, re.IGNORECASE):
            return False, f"SQL 中包含禁止的关键词：{keyword}"

    # 4. 限制返回行数（如果 SQL 中没有 LIMIT）
    if 'LIMIT' not in cleaned.upper():
        cleaned = cleaned.rstrip(";") + "LIMIT 20"    # 默认最多20条

    return True, cleaned

# 测试
if __name__=="__main__":
    safe_sql = "SELECT * FROM users WHERE city = '北京'"
    print(f"安全的 SQL：{validate_sql(safe_sql)}")

    dangerous_sql = "DROP TABLE users"
    print(f"危险的 SQL：{validate_sql(dangerous_sql)}")

    sneaky_sql = "SELECT * FROM users; DROP TABLE users"
    print(f"隐式危险：{validate_sql(sneaky_sql)}")
