"""
全局异常处理 — 统一的错误响应格式
===================================
不让任何未捕获的异常直接暴露给客户端

Java 对照：
    @ControllerAdvice + @ExceptionHandler
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

def register_exception_handlers(app: FastAPI):
    """
    注册全局异常处理器
    用法：在 main_task.py 中调用 register_exception_handlers(app)
    """
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        处理 HTTPExcetion（401、404、422等）
        统一响应格式
        """
        logger.warning(f"HTTP {exc.status_code}: {exc.detail} | {request.method} {request.url}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "code": exc.status_code,
                "message": exc.detail
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """处理参数校验错误"""
        logger.warning(f"参数校验错误：{exc} | {request.method} {request.url}")
        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "code": 422,
                "message": str(exc)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        兜底处理：捕获所有未处理的异常
        不能在生产环境中暴漏详细信息！
        """
        logger.error(f"未处理异常：{type(exc).__name__}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "code": 500,
                "message": "服务器内部错误" if not app.debug else str(exc)
            }
        )
