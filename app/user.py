from synology_api.core_user import User
from synology_api.core_group import Group
from .config import settings
from .auth import require_token_auth
from fastapi.routing import APIRouter
from fastapi import Depends
from typing import Dict

user_router = APIRouter(
    prefix="/user",
    tags=["用户管理"],
    dependencies=[Depends(require_token_auth)]  # 全局应用 Token 鉴权
)

user = User(settings.dsm_host,settings.dsm_port,settings.nas_user, settings.nas_password)
group = Group(settings.dsm_host,settings.dsm_port,settings.nas_user, settings.nas_password)

@user_router.get("/list")
async def list_users() -> Dict:
    """
    获取系统中的用户列表

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Returns:
        Dict: 用户列表，包含所有系统用户的信息
    """
    return user.get_users()

# 新增用户
@user_router.post("/create")
async def create_user(username: str, password: str, description: str = None) -> Dict:
    """
    新增用户

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        username: 用户名
        password: 密码
        description: 用户描述

    Returns:
        Dict: 创建结果
    """
    return user.create_user(username, password, description)

# 启用用户
@user_router.post("/enable")
async def enable_user(username: str) -> Dict:
    """
    启用用户,修改过期时间为永久

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        username: 用户名

    Returns:
        Dict: 操作结果
    """
    return user.modify_user(username,username, expire="never")

# 禁用用户
@user_router.post("/disable")
async def disable_user(username: str) -> Dict:
    """
    禁用用户,修改过期时间为当前时间

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        username: 用户名

    Returns:
        Dict: 操作结果
    """
    return user.modify_user(username, username, expire="now")

# 删除用户
@user_router.post("/delete")
async def delete_user(username: str) -> Dict:
    """
    删除用户

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        username: 用户名

    Returns:
        Dict: 操作结果
    """
    return user.delete_user(username)


# 添加用户到组
@user_router.post("/add_to_group")
async def add_user_to_group(username: str, groupname: str) -> Dict:
    """
    添加用户到组

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        username: 用户名
        groupname: 组名

    Returns:
        Dict: 操作结果
    """
    return group.add_users(groupname, [username])