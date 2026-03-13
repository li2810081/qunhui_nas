import os
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Response, Depends, Form
from synology_api.filestation import FileStation
from .config import settings
from .auth import require_token_auth

file_router = APIRouter(
    prefix="/drive",
    tags=["文件管理"],
    dependencies=[Depends(require_token_auth)]  # 全局应用 Token 鉴权
)

# 全局 FileStation 实例（单例）
_nas_instance = None

def get_nas_client():
    """获取或创建 FileStation 客户端"""
    global _nas_instance
    if _nas_instance is None:
        _nas_instance = FileStation(
            settings.dsm_host,
            settings.dsm_port,
            settings.nas_user,
            settings.nas_password
        )
    return _nas_instance

@file_router.post("/upload")
async def upload(
    dest_path: str = Form("/"),
    file: UploadFile = File(...),
    nas: FileStation = Depends(get_nas_client)
):
    """
    上传文件到 NAS

    Args:
        dest_path: 目标路径，例如 "/home" 或 "/home/subfolder"
        file: 要上传的文件

    Returns:
        上传结果
    """
    # 读取文件内容
    content = await file.read()

    # 获取原始文件名
    filename = file.filename or "unnamed_file"

    # 创建临时目录并使用原始文件名
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, filename)

    try:
        # 写入临时文件
        with open(temp_file_path, 'wb') as f:
            f.write(content)

        # 确保目标路径格式正确
        if not dest_path.startswith("/"):
            dest_path = "/" + dest_path

        # 使用 FileStation API 上传
        result = nas.upload_file(
            dest_path=dest_path,
            file_path=temp_file_path,
            create_parents=True,
            overwrite=True
        )

        # 检查上传是否成功
        if isinstance(result, dict) and result.get('success'):
            return {
                "success": True,
                "message": "上传成功",
                "filename": filename,
                "dest_path": dest_path,
                "result": result
            }
        else:
            return {
                "success": False,
                "message": "上传可能失败，请检查",
                "filename": filename,
                "dest_path": dest_path,
                "result": result
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"上传出错: {str(e)}",
            "filename": filename,
            "dest_path": dest_path
        }
    finally:
        # 清理临时文件和目录
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass

@file_router.get("/download/{file_path:path}")
async def download(file_path: str, nas: FileStation = Depends(get_nas_client)):
    """
    从 NAS 下载文件

    Args:
        file_path: 文件路径，例如 "/home/test.txt"

    Returns:
        文件内容
    """
    # 创建临时目录用于下载
    temp_dir = tempfile.mkdtemp()
    temp_file_name = Path(file_path).name or "download"
    temp_file_path = os.path.join(temp_dir, temp_file_name)

    try:
        # 确保路径格式正确
        if not file_path.startswith("/"):
            file_path = "/" + file_path

        # 使用 FileStation API 下载文件到临时位置
        result = nas.get_file(
            path=file_path,
            mode="download",
            dest_path=temp_dir
        )

        if result is not None:
            # get_file 返回非 None 表示有错误
            return Response(
                content=f"下载失败: {result}".encode('utf-8'),
                status_code=500,
                media_type="text/plain"
            )

        # 读取下载的文件内容
        if not os.path.exists(temp_file_path):
            # 尝试查找目录中的文件（可能是使用原始文件名）
            files = os.listdir(temp_dir)
            if files:
                temp_file_path = os.path.join(temp_dir, files[0])
            else:
                return Response(
                    content=f"下载后找不到文件".encode('utf-8'),
                    status_code=404,
                    media_type="text/plain"
                )

        with open(temp_file_path, 'rb') as f:
            file_content = f.read()

        # 获取文件扩展名以确定 MIME 类型
        suffix = Path(file_path).suffix.lower()
        mime_types = {
            ".txt": "text/plain; charset=utf-8",
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".mp4": "video/mp4",
            ".mp3": "audio/mpeg",
            ".zip": "application/zip",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        media_type = mime_types.get(suffix, "application/octet-stream")

        return Response(content=file_content, media_type=media_type)

    except Exception as e:
        return Response(
            content=f"下载失败: {str(e)}".encode('utf-8'),
            status_code=500,
            media_type="text/plain"
        )
    finally:
        # 清理临时文件和目录
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            if os.path.exists(temp_dir):
                # 清理目录中的所有文件
                for f in os.listdir(temp_dir):
                    fp = os.path.join(temp_dir, f)
                    if os.path.isfile(fp):
                        os.unlink(fp)
                os.rmdir(temp_dir)
        except:
            pass
