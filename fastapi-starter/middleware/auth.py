"""
API Key 认证中间件
===================
在每个请求到达路由之前，检查 X-API-Key 请求头

Java 对照：
    Spring Security OncePerRequestFilter 或 @PreAuthorize
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config.settings import settings

# 方式一： 使用 FastAPI 的依赖注入（推荐 -- 只保持特定路由）
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """
    验证 API Key （用在需要认证的路由中）

    用法：
        @router.get("/admin")
        async def admin_only(api_key: str = Depends(verify_api_key)):
            return {"message": "欢迎管理员"}
    """
    if api_key != settings.api_key_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 API Key"
        )
    return api_key

# 方式二：全局中间件（保护所有）
class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    全局 API Key 认证中间件
    类似于 Spring Security Filter Chain 中的一个 Filter

    注意：这会保护所有请求！白名单路径再此配置
    """

    async def dispatch(self, request: Request, call_next):
        # 白名单：不需要认证的路径
        public_paths = ["/", "/docs", "/redoc", "/openapi.json"]

        if request.url.path in public_paths:
            return await call_next(request)

        # 检查 API Key
        api_key = request.headers.get(settings.api_key_header)
        if api_key != settings.api_key_value:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content = {"detail": "无效或缺失的 API Key"}
            )
        return await call_next(request)