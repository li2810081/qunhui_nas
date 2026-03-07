"""
FastAPI Webhook服务
接收hook请求，调用nas.py中的函数执行相应操作
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from app.nas import (
    create_user,
    enable_user,
    disable_user,
    read_file,
    write_file,
    logger as nas_logger,
    NASWeakPasswordError,
)
from app.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# ===== 应用生命周期管理 =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 60)
    logger.info("群晖NAS管理API服务启动中...")
    logger.info("=" * 60)
    logger.info(f"版本: 1.0.0")
    logger.info(f"NAS主机: {settings.nas_host}")
    logger.info(f"允许的TOKEN数量: {len(settings.token)}")
    logger.info(f"允许的IP数量: {len(settings.allow_ip)}")
    logger.info(f"允许的文件路径数量: {len(settings.allow_file_path)}")
    logger.info("=" * 60)

    yield

    logger.info("=" * 60)
    logger.info("群晖NAS管理API服务关闭中...")
    logger.info("=" * 60)


# ===== 创建FastAPI应用 =====

app = FastAPI(
    title="群晖NAS管理API",
    description="通过SSH管理Synology NAS的Webhook服务",
    version="1.0.0",
    lifespan=lifespan
)


# ===== 数据模型 =====

class UserCreateRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=1, max_length=32, description="用户名")
    password: str = Field(..., min_length=4, max_length=64, description="密码")
    groups: list[str] = Field(default=[], description="用户组列表")


class UserOperationRequest(BaseModel):
    """用户操作请求"""
    username: str = Field(..., min_length=1, max_length=32, description="用户名")


class FileReadRequest(BaseModel):
    """读取文件请求"""
    file_path: str = Field(..., min_length=1, description="文件路径")


class FileWriteRequest(BaseModel):
    """写入文件请求"""
    file_path: str = Field(..., min_length=1, description="文件路径")
    content: str = Field(..., description="文件内容")


# ===== TOKEN验证依赖 =====

def validate_token(token: str) -> str:
    """
    验证TOKEN是否有效

    Args:
        token: URL参数中的token

    Returns:
        验证通过返回token值

    Raises:
        HTTPException: token无效时抛出401错误
    """
    if not settings.token:
        logger.warning("TOKEN配置为空，跳过验证")
        return token

    if token not in settings.token:
        logger.warning(f"无效的TOKEN: {token}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的TOKEN"
        )

    logger.info(f"TOKEN验证成功")
    return token


class APIResponse(BaseModel):
    """统一API响应"""
    success: bool
    message: str
    data: Optional[dict] = None


# ===== 安全中间件 =====

import socket
from functools import lru_cache
import time

@lru_cache(maxsize=32)
def resolve_hostname(hostname: str, ttl_hash=None) -> str:
    """解析主机名 IP，带简单 TTL 缓存（通过 ttl_hash 控制失效）"""
    try:
        # 尝试将主机名/容器名解析为 IP
        ip = socket.gethostbyname(hostname)
        logger.debug(f"解析主机名 {hostname} -> {ip}")
        return ip
    except socket.error:
        # 解析失败则原样返回（可能是 IP 本身）
        return hostname

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """安全验证中间件"""

    # 1. 提取客户端IP
    client_ip = request.client.host
    logger.info(f"收到请求: {request.method} {request.url.path} 来自IP: {client_ip}")

    # 2. IP白名单验证
    if settings.allow_ip:
        # 使用当前时间戳（整分钟）作为 TTL hash，实现每分钟刷新一次 DNS 缓存
        ttl_hash = int(time.time() / 60)
        
        allowed = False
        if client_ip in settings.allow_ip:
            allowed = True
        else:
            # 尝试解析白名单中的主机名
            for allow_item in settings.allow_ip:
                resolved_ip = resolve_hostname(allow_item, ttl_hash)
                if client_ip == resolved_ip:
                    allowed = True
                    break
        
        if not allowed:
            logger.warning(f"IP访问被拒绝: {client_ip} (允许列表: {settings.allow_ip})")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "IP地址不在允许列表中"}
            )
        logger.info(f"IP验证通过: {client_ip}")

    # 3. 处理请求
    response = await call_next(request)

    logger.info(f"请求处理完成: {request.method} {request.url.path} - 状态码: {response.status_code}")
    return response


# ===== 异常处理器 =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理异常: {type(exc).__name__} - {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "服务器内部错误"}
    )


# ===== API端点 =====

@app.get("/", tags=["基础"])
async def root():
    """根路径"""
    return {"message": "群晖NAS管理API", "version": "1.0.0"}


@app.get("/health", tags=["基础"])
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "qunhui-nas"}


@app.post("/user/create", tags=["用户管理"])
async def api_create_user(
    request: UserCreateRequest,
    token: str = Query(..., description="访问令牌")
):
    """创建用户并分配用户组"""
    # 验证token
    validate_token(token)

    logger.info(f"创建用户请求: {request.username}")

    try:
        result = await create_user(
            username=request.username,
            password=request.password,
            groups=request.groups
        )
        return APIResponse(
            success=True,
            message="用户创建成功",
            data=result
        )
    except NASWeakPasswordError as e:
        logger.error(f"创建用户失败(密码强度): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/user/enable", tags=["用户管理"])
async def api_enable_user(
    request: UserOperationRequest,
    token: str = Query(..., description="访问令牌")
):
    """启用用户"""
    # 验证token
    validate_token(token)

    logger.info(f"启用用户请求: {request.username}")

    try:
        result = await enable_user(request.username)
        return APIResponse(
            success=True,
            message="用户启用成功",
            data=result
        )
    except Exception as e:
        logger.error(f"启用用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/user/disable", tags=["用户管理"])
async def api_disable_user(
    request: UserOperationRequest,
    token: str = Query(..., description="访问令牌")
):
    """禁用用户"""
    # 验证token
    validate_token(token)

    logger.info(f"禁用用户请求: {request.username}")

    try:
        result = await disable_user(request.username)
        return APIResponse(
            success=True,
            message="用户禁用成功",
            data=result
        )
    except Exception as e:
        logger.error(f"禁用用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/file/read", tags=["文件操作"])
async def api_read_file(
    request: FileReadRequest,
    token: str = Query(..., description="访问令牌")
):
    """读取文件内容"""
    # 验证token
    validate_token(token)

    logger.info(f"读取文件请求: {request.file_path}")

    try:
        result = await read_file(request.file_path)
        return APIResponse(
            success=True,
            message="文件读取成功",
            data=result
        )
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/file/write", tags=["文件操作"])
async def api_write_file(
    request: FileWriteRequest,
    token: str = Query(..., description="访问令牌")
):
    """写入文件内容"""
    # 验证token
    validate_token(token)

    logger.info(f"写入文件请求: {request.file_path}")

    try:
        result = await write_file(request.file_path, request.content)
        return APIResponse(
            success=True,
            message="文件写入成功",
            data=result
        )
    except Exception as e:
        logger.error(f"写入文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===== 启动命令 =====

if __name__ == "__main__":
    import uvicorn
    logger.info("启动群晖NAS管理API服务...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
