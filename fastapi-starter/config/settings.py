"""
应用配置 - 使用pydantic-settings 管理所有配置
从 .env 文件和环境变量中读取配置

Java对照：
    @ConfigurationProperties(prefix = "app")
    public record AppConfig(String dbUrl, ...) {}


需要安装 pydantic-settings
pip install pydantic-setting     # 配置管理
"""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """应用配置类，自动从 .env 和 环境变量读取"""
    
    # 数据库配置
    # 格式： sqlite + aiosqlite:///路径(aiosqlite 是 asyncic 的 SQLite 驱动)
    database_url: str = "sqlite+aiosqlite:///.fastapi_starter.db"

    # API 配置
    api_key_header: str = "X-API-Key"      # API Key 放在哪个请求头
    api_key_value: str = "my-secret-key"   # 默认 API Key（生产环境中改！）

    # 服务器配置
    host: str = "127.0.0.1"
    port: int = 8080
    debug: bool = True

    # 分页默认值
    defalut_page_size: int = 10
    max_page_size: int = 100

    # model_config 告诉 pydantic-settings 从哪里读取
    model_config = SettingsConfigDict(
        env_file=".env",        # 从 .env 文件读取
        env_file_encoding="utf-8",
        case_sensitive=False        # 环境变量名 不区分大小写
    )

# 创建全局配置单例（类似于 Spring 容器管理的 Bean）
settings = Settings()