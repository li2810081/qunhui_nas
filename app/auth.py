"""
API 鉴权模块

提供基于 Token 和 IP 白名单的访问控制
"""
from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyQuery

from .config import settings


class TokenAuth:
    """Token 鉴权"""

    def __init__(self, require_token: bool = True):
        """
        初始化 Token 鉴权

        Args:
            require_token: 是否要求必须提供 token，如果为 False 则在未配置 token 时跳过验证
        """
        self.require_token = require_token

    async def __call__(self, request: Request) -> bool:
        """
        验证请求中的 token 参数

        Args:
            request: FastAPI 请求对象

        Returns:
            bool: 验证通过返回 True

        Raises:
            HTTPException: 验证失败时抛出 401 或 403 异常
        """
        # 如果没有配置 token，根据 require_token 决定是否跳过验证
        if not settings.token:
            if not self.require_token:
                # 允许无 token 访问（用于开发环境）
                return True
            else:
                # 生产环境建议配置 token
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Server configuration error: token not configured"
                )

        # 从查询参数中获取 token
        token = request.query_params.get("token")

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing token parameter. Please provide ?token=YOUR_TOKEN in the URL."
            )

        # 验证 token
        valid_tokens = [t.strip() for t in settings.token.split(",")]
        if token not in valid_tokens:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token"
            )

        return True


class IPWhitelist:
    """IP 白名单验证"""

    async def __call__(self, request: Request) -> bool:
        """
        验证请求来源 IP 是否在白名单中

        Args:
            request: FastAPI 请求对象

        Returns:
            bool: 验证通过返回 True

        Raises:
            HTTPException: IP 不在白名单中时抛出 403 异常
        """
        # 如果没有配置 IP 白名单，跳过验证
        if not settings.allow_ip:
            return True

        # 获取客户端 IP
        client_ip = self._get_client_ip(request)

        # 验证 IP
        allowed_ips = [ip.strip() for ip in settings.allow_ip.split(",")]
        if client_ip not in allowed_ips:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"IP {client_ip} is not allowed"
            )

        return True

    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实 IP

        支持代理头部（X-Forwarded-For, X-Real-IP）

        Args:
            request: FastAPI 请求对象

        Returns:
            str: 客户端 IP 地址
        """
        # 检查代理头部
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # 取第一个 IP（客户端 IP）
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 直接连接
        return request.client.host if request.client else "unknown"


class CompositeAuth:
    """组合鉴权（Token + IP 白名单）"""

    def __init__(self, require_token: bool = True, check_ip: bool = False):
        """
        初始化组合鉴权

        Args:
            require_token: 是否要求 token 验证
            check_ip: 是否检查 IP 白名单
        """
        self.token_auth = TokenAuth(require_token=require_token)
        self.ip_auth = IPWhitelist() if check_ip else None

    async def __call__(self, request: Request) -> bool:
        """
        执行组合鉴权

        Args:
            request: FastAPI 请求对象

        Returns:
            bool: 所有验证都通过返回 True

        Raises:
            HTTPException: 任一验证失败时抛出异常
        """
        # Token 验证
        await self.token_auth(request)

        # IP 白名单验证
        if self.ip_auth:
            await self.ip_auth(request)

        return True


# 预定义的鉴权依赖
optional_token_auth = TokenAuth(require_token=False)
require_token_auth = TokenAuth(require_token=True)
token_and_ip_auth = CompositeAuth(require_token=True, check_ip=True)
optional_token_and_ip_auth = CompositeAuth(require_token=False, check_ip=True)
