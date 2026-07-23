"""NL2SQL 核心引擎（⭐ 核心）"""


"""
NL2SQL 核心引擎
=================
这是整个系统的核心！将 LangChain、Schema 提取、安全控制、错误重试串联起来。

数据流：
    用户问题 → Schema 注入 Prompt → LLM 生成 SQL
    → 安全校验 → 执行 SQL → 返回结果
    →（失败）→ 错误信息回传 LLM → 重新生成 SQL（最多 3 次）
"""

import re
import sqlite3
import logging

from typing import List, AsyncIterator

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from security import validate_sql
from prompt_templates import (SYSTEM_PROMPT, USER_PROMPT, FEW_SHOT_EXAMPLES, SQL_FIX_PROMPT)

logger = logging.getLogger(__name__)
"""
Schema 提取 — NL2SQL 系统最关键的一步！
==========================================
LLM 需要知道数据库中有哪些表和字段，才能写出正确的 SQL。
这个函数的作用就是：读取数据库元数据 → 生成 LLM 可理解的 DDL 描述。

Java 对照：
    类似于读取 JDBC DatabaseMetaData → 拼成 System Prompt
"""


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
                desc_parts.append(f"DEFAULT {dflt_value}")
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


class NL2SQLEngine:
    """
    NL2SQL 引擎：
    使用方法：
        engine = NL2SQLEngine(db_path="sample_data.db")
        result = await engine.query("北京有多少用户")
    """

    def __init__(self,
                 db_path: str,
                 model_name: str = "deepseek-v4-flash",
                 api_key: str = "",
                 max_retries: int = 3
                 ):
        """
        Args:
            db_path: 业务数据库路径
            model_name: LLM 模型名称
            api_key: API Key
            max_retries: SQL   错误后最大重试次数
        """
        self.db_path = db_path
        self.max_retries = max_retries
        self.model = ChatOpenAI(
            model=model_name,
            base_url="https://api.deepseek.com",
            api_key=api_key,
            temperature=0  # 生成的 SQL 需要确定性
        )

        # 预加载 Schema（启动时提取一次，缓存起来）
        self.schema = extract_schema(db_path)
        logger.info(f"Schema 已加载，共{len(self.schema)} 字符")

    # 组合系统提示词
    def _build_system_prompt(self) -> str:
        """构建包含 Schema + Few-shot 的 System Prompt"""
        prompt = SYSTEM_PROMPT.format(schema=self.schema)
        prompt += "\n" + FEW_SHOT_EXAMPLES
        return prompt

    # 执行 SQL 查询
    def _execute_sql(self, sql: str) -> dict:
        """
        执行 SQL 查询
        Returns:
            {"success" : True, "data": [...], "columns": [...]}
            或
            {"success": False, "error": "..."}
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 让结果可以通过列名访问

        try:
            cursor = conn.cursor()
            cursor.execute(sql)

            # 获取列名
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # 获取所有数据
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]

            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": len(data)
            }
        except sqlite3.Error as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            conn.close()

    # 执行 NL2SQL 查询（非流式）
    async def query(self, question: str) -> dict:
        """
        执行 NL2SQL 查询（非流式）
        Args:
            question: 用户问题
        Returns:
            {
                "question": "...",
                "sql": "...",
                "success": True/False,
                "data": [...],
                "columns": [...],
                "retires": 0
            }
        """
        system_prompt = self._build_system_prompt()

        # 构建消息
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=USER_PROMPT.format(question=question))
        ]

        retries = 0
        last_sql = ""

        while retries <= self.max_retries:
            # 调用 LLM
            response = self.model.invoke(messages)
            raw_output = response.content

            # 从 LLM 输出中提取 SQL
            sql = self._extract_sql_from_output(raw_output)
            if not sql:
                return {
                    "question": question,
                    "sql": "",
                    "success": False,
                    "error": "无法从 LLM 输出中提取 SQL 语句",
                    "raw_output": raw_output
                }
            last_sql = sql

            # 安全检查
            is_safe, safe_sql = validate_sql(sql)
            if not is_safe:
                return {
                    "question": question,
                    "sql": sql,
                    "success": False,
                    "error": f"SQL 安全校验未通过：{safe_sql}"
                }

            # 执行 SQL
            result = self._execute_sql(safe_sql)

            if result["success"]:
                return {
                    "question": question,
                    "sql": safe_sql,
                    "success": True,
                    "data": result["data"],
                    "columns": result["columns"],
                    "row_count": result["row_count"],
                    "retries": retries
                }

            # SQL 执行失败 -> 错误修正重试
            retries += 1
            if retries <= self.max_retries:
                logger.warning(f"SQL 执行失败（第 {retries} 次重试）：{result['error']}")
                # 把错误信息作为新消息加入对话（让 LLM 知道哪里错误）
                fix_prompt = SQL_FIX_PROMPT.format(
                    question=question,
                    sql=safe_sql,
                    error=result["error"],
                    schema=self.schema
                )
                messages.append(AIMessage(content=raw_output))
                messages.append(HumanMessage(content=fix_prompt))

        # 重试全部失败
        return {
            "question": question,
            "sql": last_sql,
            "success": False,
            "error": f"SQL 执行失败（已重试{self.max_retries}次）"
        }

    # 从 LLM 输出中提取 SQL
    def _extract_sql_from_output(self, output: str) -> str:
        """
        从 LLM 输出中提取 SQL 语句
        LLM 可能输出:
            "SQL: SELECT * FROM users"
            或
            "```sql\nSELECT * FROM users\n```"

        Returns:
            纯 SQL 语句，或空字符串
        """
        # 策略 1：提取 ```sql ... ``` 代码块
        code_block_match = re.search(r'```sql\s*(.*?)\s*```', output, re.DOTALL | re.IGNORECASE)
        if code_block_match:
            return code_block_match.group(1).strip()

        # 策略 2： 提取 ``` ... ``` 通用代码块
        code_block_match = re.search(r'```\s*(.*?)\s*```', output, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # 策略 3：查找以 SELECT 开头的行
        for line in output.split('\n'):
            stripped = line.strip()
            if stripped.upper().startswith('SELECT') or stripped.upper().startswith('WITH'):
                # 找到 SELECT 语句，取从这行开始到分号或结尾
                sql_start = output.index(stripped)
                sql_text = output[sql_start:]
                # 截取到分号
                semicolon_pos = sql_text.find(';')
                if semicolon_pos > 0:
                    return sql_text[:semicolon_pos].strip()
                return sql_text.strip()

        # 策略 4：如果输出以 "SQL:" 或 "SQL：" 开头
        for prefix in ["SQL:", "SQL：", "sql:", "sql："]:
            if prefix in output:
                idx = output.index(prefix)
                return output[idx + len(prefix):].strip().split('\n')[0]

        return ""

    # 执行 NL2SQL 查询（流式）
    async def query_stream(self, question: str) -> AsyncIterator[str]:
        """
        流式执行 NL2SQL 查询 - 适用于 SSE 场景
        每执行一步就产出一条 SSE 事件：
            1. generating_sql: 正在生成 SQL
            2. sql_generated: SQL 已生成
            3. executing: 正在执行
            4. result: 查询结果
            5. error: 错误信息
        """
        import json
        # 1. 生成 SQL
        yield f"data: {json.dumps({'type': 'generating_sql', 'message': '正在理解您的问题...'}, ensure_ascii=False)}\n\n"

        system_prmpt = self._build_system_prompt()
        messages = [
            SystemMessage(content=system_prmpt),
            HumanMessage(content=USER_PROMPT.format(question=question))
        ]

        response = self.model.invoke(messages)
        sql = self._extract_sql_from_output(response.content)

        if not sql:
            yield f"data: {json.dumps({'type': 'error', 'message': '无法理解您的问题，请换一种问法'}, ensure_ascii=False)}\n\n"
            return

        # 2. SQL 生成完成
        yield f"data: {json.dumps({'type': 'sql_generated', 'sql': sql}, ensure_ascii=False)}\n\n"

        # 3. 安全检查
        is_safe, safe_sql = validate_sql(sql)
        if not is_safe:
            yield f"data: {json.dumps({'type': 'error', 'message': f"SQL 安全检查未通过：{safe_sql}"}, ensure_ascii=False)}\n\n"
            return

        # 4. 执行查询
        yield f"data: {json.dumps({'type': 'executing', 'message': '正在查询数据库...'}, ensure_ascii=False)}\n\n"

        # 支持重试
        result = {}
        for attempt in range(self.max_retries + 1):
            result = self._execute_sql(safe_sql)

            if result["success"]:
                yield f"data: {json.dumps({'type': 'result', 'data': result['data'], 'columns': result['columns'], 'row_count': result['row_count'], 'sql': safe_sql}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            if attempt < self.max_retries:
                yield f"data: {json.dumps({'type': 'retrying', 'message': f"查询出错，正在尝试修正（第{attempt + 1}次）..."}, ensure_ascii=False)}\n\n"

                fix_prompt = SQL_FIX_PROMPT.format(
                    question=question,
                    sql=safe_sql,
                    error=result['error'],
                    schema=self.schema
                )
                messages.append(AIMessage(content=response.content))
                messages.append(HumanMessage(content=fix_prompt))
                response = self.model.invoke(messages)
                new_sql = self._extract_sql_from_output(response.content)
                if new_sql:
                    _, safe_sql = validate_sql(new_sql)

        yield f"data: {json.dumps({'type': 'error', 'message': f'查询失败：{result.get("error", "未知错误")}'}, ensure_ascii=False)}\n\n"
