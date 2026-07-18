"""
Task ORM 模型 — 对应数据库中的 tasks 表
=========================================
使用 SQLAlchemy 2.0 的 DeclarativeBase 风格

Java 对照：
    @Entity
    @Table(name = "tasks")
    public class Task {
        @Id @GeneratedValue
        private Long id;
        ...
    }
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from config.database import Base
from datetime import datetime

# SQLAlchemy 2.0 推荐使用 Mapped + mapped_column 风格（类型安全）
class Task(Base):
    """任务模型"""
    # 表名 （<--> @Table(name = "tasks"）)
    __tablename__ = "tasks"

    # Mapped[int] 表示 Python 类型为 int
    # mapped_column(primary_key = True)  表述数据库列属性
    # 注意：SQLAlchemy 字段名默认用下划线，但数据库列名也可以自定义

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    #  Python 3.10 + 的写法，等价于 Optional[str]

    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    # server_default=func.now() -> 数据库层面的默认值（由 SQL 函数生成）
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 软删除标记
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    def __repr__(self) -> str:
        """对象的字符串表示（<--> Java中的 toString()"""
        return f"<Task(id={self.id}, title='{self.title}', completed={self.completed})"