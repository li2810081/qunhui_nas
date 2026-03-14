from synology_api.core_user import User
from synology_api.core_group import Group
from synology_api.exceptions import SynoConnectionError, LoginError, SynoBaseException
from .config import settings
from .auth import require_token_auth
from fastapi.routing import APIRouter
from fastapi import Depends, HTTPException
from typing import Dict
from pydantic import BaseModel, Field

user_router = APIRouter(
    prefix="/user",
    tags=["用户管理"],
    dependencies=[Depends(require_token_auth)]  # 全局应用 Token 鉴权
)

# 全局实例（单例）
_user_instance = None
_group_instance = None


def reset_user_client():
    """重置 User 客户端"""
    global _user_instance
    _user_instance = None


def reset_group_client():
    """重置 Group 客户端"""
    global _group_instance
    _group_instance = None


def get_user_client() -> User:
    """获取或创建 User 客户端"""
    global _user_instance
    if _user_instance is None:
        _user_instance = User(
            settings.dsm_host,
            settings.dsm_port,
            settings.nas_user,
            settings.nas_password
        )
    return _user_instance


def get_group_client() -> Group:
    """获取或创建 Group 客户端"""
    global _group_instance
    if _group_instance is None:
        _group_instance = Group(
            settings.dsm_host,
            settings.dsm_port,
            settings.nas_user,
            settings.nas_password
        )
    return _group_instance


def _user_exists(user_client: User, username: str) -> bool:
    """
    检查用户是否已存在

    Args:
        user_client: User 客户端实例
        username: 要检查的用户名

    Returns:
        bool: 用户是否存在
    """
    try:
        users = user_client.get_users()
        if isinstance(users, dict) and 'data' in users:
            user_list = users['data'].get('users', [])
            return any(u.get('name') == username for u in user_list)
    except Exception:
        # 如果检查失败，继续尝试创建
        pass
    return False


class UserInfo(BaseModel):
    username: str = Field(..., min_length=1, max_length=32, description="用户名")
    password: str = Field(..., min_length=1, max_length=32, description="密码")
    description: str = Field(..., min_length=1, max_length=32, description="描述")


class UserModifyInfo(BaseModel):
    username: str = Field(..., min_length=1, max_length=32, description="用户名")


class UserGroupInfo(BaseModel):
    username: str = Field(..., min_length=1, max_length=32, description="用户名")
    groupname: str = Field(..., min_length=1, max_length=32, description="组名")


@user_router.get("/list")
async def list_users() -> Dict:
    """
    获取系统中的用户列表

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Returns:
        Dict: 用户列表，包含所有系统用户的信息
    """
    user_client = get_user_client()

    try:
        return user_client.get_users()
    except (SynoConnectionError, LoginError):
        # 连接失效，重置并重试
        reset_user_client()
        user_client = get_user_client()
        try:
            return user_client.get_users()
        except Exception as retry_error:
            raise HTTPException(
                status_code=500,
                detail=f"连接失败，请检查 NAS 配置: {str(retry_error)}"
            )


@user_router.post("/create")
async def create_user(user_info: UserInfo) -> Dict:
    """
    新增用户

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        user_info: 用户信息

    Returns:
        Dict: 创建结果

    Raises:
        HTTPException: 用户已存在时返回 409 Conflict
    """
    user_client = get_user_client()

    # 检查用户是否已存在
    if _user_exists(user_client, user_info.username):
        raise HTTPException(
            status_code=409,  # 409 Conflict
            detail=f"用户 '{user_info.username}' 已存在"
        )

    try:
        result = user_client.create_user(
            name=user_info.username,
            password=user_info.password,
            description=user_info.description
        )

        # 检查创建结果
        if isinstance(result, dict) and not result.get('success'):
            # 可能的错误码：用户已存在（尽管我们已经检查过，但仍可能有竞态条件）
            error_code = result.get('error_code')
            error_msg = result.get('error_message', '')

            # 5500 通常是用户已存在的错误码（根据 synology_api 文档）
            if error_code in [5500, 5501, 5502] or 'already exists' in str(error_msg).lower():
                raise HTTPException(
                    status_code=409,
                    detail=f"用户 '{user_info.username}' 已存在"
                )

            # 其他错误
            raise HTTPException(
                status_code=400,
                detail=f"创建用户失败: {error_msg or '未知错误'} (错误码: {error_code})"
            )

        return result

    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except (SynoConnectionError, LoginError):
        # 连接失效，重置并重试
        reset_user_client()
        user_client = get_user_client()
        try:
            # 重试前再次检查用户是否存在
            if _user_exists(user_client, user_info.username):
                raise HTTPException(
                    status_code=409,
                    detail=f"用户 '{user_info.username}' 已存在"
                )

            result = user_client.create_user(
                name=user_info.username,
                password=user_info.password,
                description=user_info.description
            )

            if isinstance(result, dict) and not result.get('success'):
                error_code = result.get('error_code')
                error_msg = result.get('error_message', '')

                if error_code in [5500, 5501, 5502] or 'already exists' in str(error_msg).lower():
                    raise HTTPException(
                        status_code=409,
                        detail=f"用户 '{user_info.username}' 已存在"
                    )

                raise HTTPException(
                    status_code=400,
                    detail=f"创建用户失败: {error_msg or '未知错误'} (错误码: {error_code})"
                )

            return result

        except HTTPException:
            raise
        except Exception as retry_error:
            raise HTTPException(
                status_code=500,
                detail=f"连接失败，请检查 NAS 配置: {str(retry_error)}"
            )
    except SynoBaseException as e:
        raise HTTPException(
            status_code=500,
            detail=f"NAS API 错误: {str(e)}"
        )


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
    user_client = get_user_client()

    try:
        return user_client.modify_user(
            user_modify_info.username,
            user_modify_info.username,
            expire="normal"
        )
    except (SynoConnectionError, LoginError):
        # 连接失效，重置并重试
        reset_user_client()
        user_client = get_user_client()
        try:
            return user_client.modify_user(
                user_modify_info.username,
                user_modify_info.username,
                expire="normal"
            )
        except Exception as retry_error:
            raise HTTPException(
                status_code=500,
                detail=f"连接失败，请检查 NAS 配置: {str(retry_error)}"
            )


@user_router.post("/disable")
async def disable_user(user_modify_info: UserModifyInfo) -> Dict:
    """
    禁用用户,修改过期时间为当前时间

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        user_modify_info: 用户修改信息

    Returns:
        Dict: 操作结果
    """
    user_client = get_user_client()

    try:
        return user_client.modify_user(
            user_modify_info.username,
            user_modify_info.username,
            expire="now"
        )
    except (SynoConnectionError, LoginError):
        # 连接失效，重置并重试
        reset_user_client()
        user_client = get_user_client()
        try:
            return user_client.modify_user(
                user_modify_info.username,
                user_modify_info.username,
                expire="now"
            )
        except Exception as retry_error:
            raise HTTPException(
                status_code=500,
                detail=f"连接失败，请检查 NAS 配置: {str(retry_error)}"
            )


@user_router.post("/delete")
async def delete_user(user_modify_info: UserModifyInfo) -> Dict:
    """
    删除用户

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        user_modify_info: 用户修改信息

    Returns:
        Dict: 操作结果
    """
    user_client = get_user_client()

    try:
        return user_client.delete_user(user_modify_info.username)
    except (SynoConnectionError, LoginError):
        # 连接失效，重置并重试
        reset_user_client()
        user_client = get_user_client()
        try:
            return user_client.delete_user(user_modify_info.username)
        except Exception as retry_error:
            raise HTTPException(
                status_code=500,
                detail=f"连接失败，请检查 NAS 配置: {str(retry_error)}"
            )


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
    group_client = get_group_client()

    try:
        return group_client.add_users(
            user_group_info.groupname,
            [user_group_info.username]
        )
    except (SynoConnectionError, LoginError):
        # 连接失效，重置并重试
        reset_group_client()
        group_client = get_group_client()
        try:
            return group_client.add_users(
                user_group_info.groupname,
                [user_group_info.username]
            )
        except Exception as retry_error:
            raise HTTPException(
                status_code=500,
                detail=f"连接失败，请检查 NAS 配置: {str(retry_error)}"
            )
