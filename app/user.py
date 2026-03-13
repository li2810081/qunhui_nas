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

from pydantic import BaseModel, Field
class UserInfo(BaseModel):
    username: str = Field(..., min_length=1, max_length=32, description="用户名")
    password: str = Field(..., min_length=1, max_length=32, description="密码")
    description: str = Field(..., min_length=1, max_length=32, description="描述")

class UserModifyInfo(BaseModel):
    username: str = Field(..., min_length=1, max_length=32, description="用户名")

# 新增用户
@user_router.post("/create")
async def create_user(user_info: UserInfo) -> Dict:
    """
    新增用户

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        user_info: 用户信息

    Returns:
        Dict: 创建结果
    """
    user_info_dict = user_info.model_dump()
    return user.create_user(**user_info_dict)


# 启用用户
@user_router.post("/enable")
async def enable_user(user_modify_info: UserModifyInfo) -> Dict:
    """
    启用用户,修改过期时间为永久

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        user_modify_info: 用户修改信息

    Returns:
        Dict: 操作结果
    """
    username=user_modify_info.username
    return user.modify_user(username,username, expire="normal")

# 禁用用户
@user_router.post("/disable")
async def disable_user(user_modify_info: UserModifyInfo) -> Dict:
    """
    禁用用户,修改过期时间为当前时间

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        username: 用户名

    Returns:
        Dict: 操作结果
    """
    username = user_modify_info.username
    return user.modify_user(username, username, expire="now")

# 删除用户
@user_router.post("/delete")
async def delete_user(user_modify_info: UserModifyInfo) -> Dict:
    """
    删除用户

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        username: 用户名

    Returns:
        Dict: 操作结果
    """
    username = user_modify_info.username
    return user.delete_user(username)

class UserGroupInfo(BaseModel):
    username: str = Field(..., min_length=1, max_length=32, description="用户名")
    groupname: str = Field(..., min_length=1, max_length=32, description="组名")

# 添加用户到组
@user_router.post("/add_to_group")
async def add_user_to_group(user_group_info: UserGroupInfo) -> Dict:
    """
    添加用户到组

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        user_group_info: 用户组信息

    Returns:
        Dict: 操作结果
    """
    username = user_group_info.username
    groupname = user_group_info.groupname
    
    return group.add_users(groupname, [username])