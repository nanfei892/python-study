""" 配置管理 """
"""
NL2SQL 项目配置
参考 Day 2 的 pydantic-settings 模式
"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

load_dotenv()

class Settings(BaseSettings):
    """应用配置"""
    # 数据库
    database_url: str = "sqlite+aiosqlite:///./nl2sql.db"
    sample_db_url:str = "sqlite:///./sample_data.db"        # 示例业务数据（同步连接）

    # DeepSeek
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY")
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_base_url: str = "https://api.deepseek.com"

    # 服务器
    host: str = "127.0.0.1"
    port: int = 8080

    model_config = SettingsConfigDict(
        env_file=".env",           # 相对于项目根目录
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()