"""
日志配置 — Python logging 模块
===============================
使用标准的 logging 库（不需要额外安装）

Java 对照：
    SLF4J + Logback
"""

import logging
import sys

def setup_logging():
    """配置全局日志格式和级别"""
    # 1. 设置日志格式
    # %(asctime)s      - 时间戳
    # %(levelname)s    - 日志级别（DEBUG/INFO/WARNING/ERROR）
    # %(name)s         - logger 名称（通常是模块名）
    # %(message)s      - 日志消息
    log_format = logging.Formatter(
        "%(asctime)s  [%(levelname)s]  %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 2. 设置日志输入（控制台）
    console_hander = logging.StreamHandler(sys.stdout)
    console_hander.setFormatter(log_format)

    # 3. 设置根 logger 的级别
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_hander)

    # 4. 可以单独调整特定模块的日志级别
    # 注意：SQL 日志不要太吵，否则出问题方便排查
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger(__name__).info("✅️    日志系统已配置")

# 获取 logger 的标准方式（每个模块都用这个）
def get_logger(name: str) -> logging.Logger:
    """获取命名的 logger （推荐）"""
    return logging.getLogger(name)
