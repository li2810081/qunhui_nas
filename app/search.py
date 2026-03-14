"""
搜索 API 模块
提供文件搜索功能
"""
import asyncio
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from synology_api.universal_search import UniversalSearch
from synology_api.filestation import FileStation
from synology_api.exceptions import (
    UniversalSearchError,
    SynoBaseException,
    SynoConnectionError,
    LoginError
)

from .config import settings
from .auth import require_token_auth

search_router = APIRouter(
    prefix="/search",
    tags=["搜索管理"],
    dependencies=[Depends(require_token_auth)]  # 全局应用 Token 鉴权
)

# 全局 UniversalSearch 实例（单例）
_search_instance = None

# 全局 FileStation 实例（单例）
_filestation_instance = None


def reset_search_client():
    """重置 UniversalSearch 客户端"""
    global _search_instance
    _search_instance = None


def reset_filestation_client():
    """重置 FileStation 客户端"""
    global _filestation_instance
    _filestation_instance = None


def get_search_client() -> UniversalSearch:
    """获取或创建 UniversalSearch 客户端"""
    global _search_instance
    if _search_instance is None:
        _search_instance = UniversalSearch(
            settings.dsm_host,
            settings.dsm_port,
            settings.nas_user,
            settings.nas_password
        )
    return _search_instance


def get_filestation_client() -> FileStation:
    """获取或创建 FileStation 客户端"""
    global _filestation_instance
    if _filestation_instance is None:
        _filestation_instance = FileStation(
            settings.dsm_host,
            settings.dsm_port,
            settings.nas_user,
            settings.nas_password,
            interactive_output=False  # 返回字典格式而不是字符串
        )
    return _filestation_instance


def with_auto_retry(client_reset_func: Callable):
    """
    装饰器：自动重试连接错误

    当检测到连接或认证错误时，重置客户端并重试一次
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (SynoConnectionError, LoginError) as e:
                # 重置客户端并重试
                client_reset_func()
                try:
                    return await func(*args, **kwargs)
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
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"操作失败: {str(e)}"
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (SynoConnectionError, LoginError) as e:
                # 重置客户端并重试
                client_reset_func()
                try:
                    return func(*args, **kwargs)
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
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"操作失败: {str(e)}"
                )

        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 请求模型
class SearchRequest(BaseModel):
    """通用搜索请求"""
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    limit: int = Field(100, ge=1, le=1000, description="返回结果数量限制")


class FileSearchRequest(BaseModel):
    """文件搜索请求"""
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    folder_path: str = Field("/", description="搜索路径")
    recursive: bool = Field(True, description="是否递归搜索")
    extension: Optional[str] = Field(None, description="文件扩展名，如 'txt,pdf'")
    filetype: Optional[str] = Field(None, description="文件类型: file, dir, all")
    limit: int = Field(100, ge=1, le=1000, description="返回结果数量限制")


@search_router.post("/")
async def search_items(request: SearchRequest) -> Dict[str, Any]:
    """
    通用搜索（使用 UniversalSearch）

    需要 token 鉴权，通过 URL参数 ?token=YOUR_TOKEN 传递

    Args:
        request: 搜索请求，包含 keyword 和 limit

    Returns:
        Dict: 搜索结果，包含匹配的文件列表

    Raises:
        HTTPException: 搜索失败时抛出
    """
    search_client = get_search_client()

    try:
        # 直接使用关键词，不进行额外处理
        result = search_client.search(request.keyword)

        # 处理返回结果
        if isinstance(result, dict):
            # 如果指定了限制且结果中有 hits，截取结果
            if 'data' in result and isinstance(result['data'], dict):
                hits = result['data'].get('hits', [])
                if request.limit and len(hits) > request.limit:
                    result['data']['hits'] = hits[:request.limit]
                    result['data']['total'] = len(hits[:request.limit])

            return result
        else:
            return {"success": True, "data": result}

    except UniversalSearchError as e:
        raise HTTPException(
            status_code=400,
            detail=f"搜索请求失败: {e}"
        )
    except (SynoConnectionError, LoginError):
        # 重置客户端并重试一次
        reset_search_client()
        search_client = get_search_client()
        try:
            result = search_client.search(request.keyword)
            if isinstance(result, dict):
                if 'data' in result and isinstance(result['data'], dict):
                    hits = result['data'].get('hits', [])
                    if request.limit and len(hits) > request.limit:
                        result['data']['hits'] = hits[:request.limit]
                        result['data']['total'] = len(hits[:request.limit])
                return result
            else:
                return {"success": True, "data": result}
        except Exception as retry_error:
            raise HTTPException(
                status_code=500,
                detail=f"连接已失效，重试失败: {str(retry_error)}"
            )
    except SynoBaseException as e:
        raise HTTPException(
            status_code=500,
            detail=f"NAS API 错误: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索时发生错误: {str(e)}"
        )


@search_router.post("/file")
async def search_files(request: FileSearchRequest) -> Dict[str, Any]:
    """
    文件搜索（使用 FileStation）

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        request: 文件搜索请求

    Returns:
        Dict: 搜索结果，包含匹配的文件列表

    Raises:
        HTTPException: 搜索失败时抛出
    """
    file_station = get_filestation_client()
    taskid = None

    try:
        # 构建搜索参数
        search_args = {
            "folder_path": request.folder_path,
            "pattern": request.keyword,
            "recursive": request.recursive
        }

        # 添加可选参数
        if request.extension:
            search_args["extension"] = request.extension
        if request.filetype:
            search_args["filetype"] = request.filetype

        # 1. 启动搜索任务
        start_result = file_station.search_start(**search_args)

        if not isinstance(start_result, dict):
            raise HTTPException(
                status_code=500,
                detail="搜索启动失败：返回格式错误"
            )

        taskid = str(start_result.get('taskid', ''))

        if not taskid:
            raise HTTPException(
                status_code=500,
                detail="搜索启动失败：未获取到任务ID"
            )

        # 2. 等待搜索完成并获取结果
        max_wait_time = 30  # 最多等待30秒
        start_time = time.time()
        items = []

        while time.time() - start_time < max_wait_time:
            try:
                result = file_station.get_search_list(task_id=taskid, limit=request.limit)

                if isinstance(result, dict) and 'data' in result:
                    items = result['data'].get('items', [])

                    # 如果有结果或搜索完成，退出循环
                    if items or result['data'].get('finished', False):
                        break
                else:
                    # 格式异常也退出
                    break

            except Exception:
                # 获取结果时可能任务还未完成，稍后重试
                pass

            # 等待一小段时间后重试
            await asyncio.sleep(0.5)

        # 3. 截取结果到指定数量
        if request.limit and len(items) > request.limit:
            items = items[:request.limit]

        return {
            "success": True,
            "taskid": taskid,
            "total": len(items),
            "data": {
                "items": items,
                "finished": True
            }
        }

    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except (SynoConnectionError, LoginError):
        # 重置客户端并重试一次
        reset_filestation_client()
        file_station = get_filestation_client()
        try:
            # 重新执行搜索逻辑
            search_args = {
                "folder_path": request.folder_path,
                "pattern": request.keyword,
                "recursive": request.recursive
            }
            if request.extension:
                search_args["extension"] = request.extension
            if request.filetype:
                search_args["filetype"] = request.filetype

            start_result = file_station.search_start(**search_args)
            if not isinstance(start_result, dict):
                raise HTTPException(status_code=500, detail="搜索启动失败：返回格式错误")

            taskid = str(start_result.get('taskid', ''))
            if not taskid:
                raise HTTPException(status_code=500, detail="搜索启动失败：未获取到任务ID")

            max_wait_time = 30
            start_time = time.time()
            items = []

            while time.time() - start_time < max_wait_time:
                try:
                    result = file_station.get_search_list(task_id=taskid, limit=request.limit)
                    if isinstance(result, dict) and 'data' in result:
                        items = result['data'].get('items', [])
                        if items or result['data'].get('finished', False):
                            break
                    else:
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.5)

            if request.limit and len(items) > request.limit:
                items = items[:request.limit]

            return {
                "success": True,
                "taskid": taskid,
                "total": len(items),
                "data": {"items": items, "finished": True}
            }
        except Exception as retry_error:
            raise HTTPException(
                status_code=500,
                detail=f"连接已失效，重试失败: {str(retry_error)}"
            )
    except SynoBaseException as e:
        raise HTTPException(
            status_code=500,
            detail=f"NAS API 错误: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件搜索时发生错误: {str(e)}"
        )
    finally:
        # 4. 清理搜索任务
        if taskid:
            try:
                file_station.stop_search_task(taskid=taskid)
            except Exception:
                # 停止任务失败不影响结果返回
                pass


@search_router.get("/suggest")
async def search_suggestions(
    query: str = Query(..., description="搜索关键词", min_length=1),
    limit: int = Query(10, description="建议数量", ge=1, le=50)
) -> Dict[str, Any]:
    """
    获取搜索建议（保留 GET 接口以兼容性）

    需要 token 鉴权，通过 URL 参数 ?token=YOUR_TOKEN 传递

    Args:
        query: 搜索关键词
        limit: 返回建议数量

    Returns:
        Dict: 搜索建议
    """
    if not query:
        return {"suggestions": []}

    search_client = get_search_client()

    try:
        result = search_client.search(query)

        suggestions = []
        if isinstance(result, dict) and 'data' in result:
            hits = result['data'].get('hits', [])
            for hit in hits[:limit]:
                # 提取文件名或路径作为建议
                name = hit.get('SYNOMDFSName') or hit.get('SYNOMDPath', '')
                if name:
                    suggestions.append({
                        'name': name,
                        'path': hit.get('SYNOMDPath', ''),
                        'type': 'file' if hit.get('SYNOMDIsDir') != 'y' else 'folder'
                    })

        return {"suggestions": suggestions}

    except (SynoConnectionError, LoginError):
        # 重置客户端并重试一次
        reset_search_client()
        search_client = get_search_client()
        try:
            result = search_client.search(query)
            suggestions = []
            if isinstance(result, dict) and 'data' in result:
                hits = result['data'].get('hits', [])
                for hit in hits[:limit]:
                    name = hit.get('SYNOMDFSName') or hit.get('SYNOMDPath', '')
                    if name:
                        suggestions.append({
                            'name': name,
                            'path': hit.get('SYNOMDPath', ''),
                            'type': 'file' if hit.get('SYNOMDIsDir') != 'y' else 'folder'
                        })
            return {"suggestions": suggestions}
        except Exception:
            # 重试失败，返回空列表
            return {"suggestions": []}
    except Exception:
        # 其他异常返回空列表
        return {"suggestions": []}
