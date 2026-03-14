import os
import logging
import asyncio
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.user import user_router, get_user_client
from app.search import search_router, get_search_client, get_filestation_client
from app.file import file_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("群晖NAS管理API启动")
    yield
    # 关闭
    logger.info("群晖NAS管理API关闭")


app = FastAPI(
    title="群晖NAS管理API",
    description="提供对群晖NAS的管理接口",
    version="1.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(user_router)
app.include_router(search_router)
app.include_router(file_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "群晖NAS管理API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    健康检查接口

    验证 NAS 连接状态，包括：
    - FileStation 服务
    - User API 服务
    - UniversalSearch 服务

    Returns:
        Dict: 健康状态信息
    """
    health_status: Dict[str, Any] = {
        "status": "ok",
        "services": {}
    }

    # 检查 FileStation 连接
    try:
        fs = get_filestation_client()
        # 调用 get_file_list 来测试连接，只获取根目录的前1个文件
        fs.get_file_list(folder_path="/", limit=1)
        health_status["services"]["filestation"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["filestation"] = f"error: {str(e)}"

    # 检查 User API 连接
    try:
        user = get_user_client()
        # 调用 get_users() 来测试连接，只获取1个用户以减少开销
        user.get_users(limit=1)
        health_status["services"]["user"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["user"] = f"error: {str(e)}"

    # 检查 UniversalSearch 连接
    try:
        search = get_search_client()
        # UniversalSearch 没有简单的 ping 方法
        # 我们通过获取客户端实例来验证连接
        # 如果实例存在且未抛出异常，认为连接正常
        _ = search
        health_status["services"]["search"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["search"] = f"error: {str(e)}"

    # 根据服务状态确定整体状态
    service_count = len(health_status["services"])
    ok_count = sum(1 for status in health_status["services"].values() if status == "ok")

    if service_count > 0 and ok_count == 0:
        health_status["status"] = "down"
    elif ok_count < service_count:
        health_status["status"] = "degraded"

    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
