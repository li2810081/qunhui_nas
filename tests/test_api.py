"""
群晖NAS管理API接口测试
测试用户管理、文件上传、搜索和下载功能
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from app.config import settings


def get_token_params() -> dict:
    """获取包含 token 的参数"""
    if settings.token:
        return {"token": settings.token.split(",")[0].strip()}
    return {}


class TestUserAPI:
    """用户管理API测试"""

    @pytest.mark.asyncio
    async def test_create_user(self):
        """测试新增用户"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            params = {
                "username": "test_user_123",
                "password": "TestPassword123!",
                "description": "测试用户"
            }
            params.update(get_token_params())

            response = await client.post("/user/create", params=params)
            print(f"新增用户响应: {response.status_code}")
            print(f"响应内容: {response.json()}")
            assert response.status_code in [200, 201]  # 根据实际API调整

    @pytest.mark.asyncio
    async def test_enable_user(self):
        """测试启用用户"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            params = {"username": "test_user_123"}
            params.update(get_token_params())

            response = await client.post("/user/enable", params=params)
            print(f"启用用户响应: {response.status_code}")
            print(f"响应内容: {response.json()}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_users(self):
        """测试获取用户列表"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            params = get_token_params()
            response = await client.get("/user/list", params=params)
            print(f"用户列表响应: {response.status_code}")
            print(f"响应内容: {response.json()}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_user(self):
        """测试删除用户"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            params = {"username": "test_user_123"}
            params.update(get_token_params())

            response = await client.post("/user/delete", params=params)
            print(f"删除用户响应: {response.status_code}")
            print(f"响应内容: {response.json()}")
            assert response.status_code == 200


class TestFileAPI:
    """文件管理API测试"""

    @pytest.mark.asyncio
    async def test_upload_file(self):
        """测试上传文件"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 准备测试文件
            test_content = "这是测试文件内容\nHello, NAS!\n测试上传功能".encode('utf-8')
            test_filename = "test_upload.txt"
            dest_path = "/home"  # 可以根据需要修改目标路径

            # 使用 multipart/form-data 上传文件
            files = {"file": (test_filename, test_content, "text/plain")}
            data = {"dest_path": dest_path}
            # 添加 token 参数到 URL
            params = get_token_params()

            response = await client.post(
                "/drive/upload",
                params=params,
                files=files,
                data=data
            )
            print(f"上传文件响应: {response.status_code}")
            print(f"响应内容: {response.json()}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_download_file(self):
        """测试下载文件"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 下载已上传的测试文件
            file_path = "/home/test_upload.txt"
            params = get_token_params()

            response = await client.get(f"/drive/download{file_path}", params=params)
            print(f"下载文件响应: {response.status_code}")
            if response.status_code == 200:
                print(f"文件内容长度: {len(response.content)} 字节")
                print(f"文件内容: {response.content.decode('utf-8', errors='ignore')}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_upload_and_download(self):
        """测试上传后下载完整流程"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 上传文件
            test_content = "集成测试文件内容\nUpload & Download Test".encode('utf-8')
            test_filename = "test_integration.txt"
            dest_path = "/home"

            print("\n=== 步骤1: 上传文件 ===")
            files = {"file": (test_filename, test_content, "text/plain")}
            data = {"dest_path": dest_path}
            params = get_token_params()

            upload_response = await client.post(
                "/drive/upload",
                params=params,
                files=files,
                data=data
            )
            print(f"上传响应: {upload_response.status_code}")
            print(f"上传结果: {upload_response.json()}")
            assert upload_response.status_code == 200

            # 2. 下载文件
            print("\n=== 步骤2: 下载文件 ===")
            file_path = f"{dest_path}/{test_filename}"
            download_response = await client.get(f"/drive/download{file_path}", params=params)
            print(f"下载响应: {download_response.status_code}")
            if download_response.status_code == 200:
                downloaded_content = download_response.content
                print(f"下载内容长度: {len(downloaded_content)} 字节")
                print(f"下载内容: {downloaded_content.decode('utf-8', errors='ignore')}")
                assert downloaded_content == test_content


class TestSearchAPI:
    """搜索API测试"""

    @pytest.mark.asyncio
    async def test_search_files(self):
        """测试搜索文件（UniversalSearch）"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 使用 POST 方法，JSON 请求体
            json_data = {"keyword": "test", "limit": 10}
            params = get_token_params()

            response = await client.post("/search/", params=params, json=json_data)
            print(f"搜索文件响应: {response.status_code}")
            print(f"响应内容: {response.json()}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_file_search(self):
        """测试文件搜索（FileStation）"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 使用 POST 方法，JSON 请求体
            json_data = {
                "keyword": "test",
                "folder_path": "/home",
                "recursive": True,
                "limit": 10
            }
            params = get_token_params()

            response = await client.post("/search/file", params=params, json=json_data)
            print(f"文件搜索响应: {response.status_code}")
            print(f"响应内容: {response.json()}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_file_search_with_extension(self):
        """测试带扩展名过滤的文件搜索"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            json_data = {
                "keyword": "test",
                "folder_path": "/home",
                "extension": "txt",
                "limit": 10
            }
            params = get_token_params()

            response = await client.post("/search/file", params=params, json=json_data)
            print(f"扩展名搜索响应: {response.status_code}")
            print(f"响应内容: {response.json()}")
            assert response.status_code == 200


class TestAuth:
    """鉴权测试"""

    @pytest.mark.asyncio
    async def test_auth_without_token(self):
        """测试无 token 访问应该返回 401"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 如果配置了 token，则测试无 token 访问
            if settings.token:
                response = await client.get("/user/list")
                print(f"无 token 访问响应: {response.status_code}")
                assert response.status_code == 401
            else:
                # 如果没有配置 token，跳过此测试
                pytest.skip("未配置 token，跳过鉴权测试")

    @pytest.mark.asyncio
    async def test_auth_with_invalid_token(self):
        """测试使用无效 token 访问应该返回 403"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 如果配置了 token，则测试无效 token 访问
            if settings.token:
                response = await client.get("/user/list", params={"token": "invalid_token_12345"})
                print(f"无效 token 访问响应: {response.status_code}")
                assert response.status_code == 403
            else:
                # 如果没有配置 token，跳过此测试
                pytest.skip("未配置 token，跳过鉴权测试")


class TestHealthCheck:
    """健康检查测试"""

    @pytest.mark.asyncio
    async def test_root(self):
        """测试根路径"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            print(f"根路径响应: {response.status_code}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health(self):
        """测试健康检查"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            print(f"健康检查响应: {response.status_code}")
            assert response.status_code == 200


# 集成测试：完整的用户和文件操作流程
class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """测试完整的工作流程：创建用户、上传文件、搜索、下载、删除用户"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token_params = get_token_params()

            # 1. 创建用户
            print("\n=== 步骤1: 创建用户 ===")
            params = {
                "username": "integration_test_user",
                "password": "TestPass123!",
                "description": "集成测试用户"
            }
            params.update(token_params)
            user_response = await client.post("/user/create", params=params)
            print(f"创建用户: {user_response.status_code} - {user_response.json()}")
            assert user_response.status_code in [200, 201]

            # 2. 启用用户
            print("\n=== 步骤2: 启用用户 ===")
            params = {"username": "integration_test_user"}
            params.update(token_params)
            enable_response = await client.post("/user/enable", params=params)
            print(f"启用用户: {enable_response.status_code} - {enable_response.json()}")
            assert enable_response.status_code == 200

            # 3. 上传文件
            print("\n=== 步骤3: 上传文件 ===")
            test_content = "集成测试文件内容\nIntegration Test File".encode('utf-8')
            test_filename = "integration_test.txt"
            dest_path = "/home"

            files = {"file": (test_filename, test_content, "text/plain")}
            data = {"dest_path": dest_path}

            upload_response = await client.post(
                "/drive/upload",
                params=token_params,
                files=files,
                data=data
            )
            print(f"上传文件: {upload_response.status_code} - {upload_response.json()}")
            assert upload_response.status_code == 200

            # 4. 下载文件
            print("\n=== 步骤4: 下载文件 ===")
            file_path = f"{dest_path}/{test_filename}"
            download_response = await client.get(f"/drive/download{file_path}", params=token_params)
            print(f"下载文件: {download_response.status_code}")
            if download_response.status_code == 200:
                downloaded_content = download_response.content
                print(f"文件内容: {downloaded_content.decode('utf-8', errors='ignore')}")
                assert downloaded_content == test_content

            # 5. 搜索文件
            print("\n=== 步骤5: 搜索文件 ===")
            json_data = {"keyword": "integration", "limit": 10}
            search_response = await client.post("/search/", params=token_params, json=json_data)
            print(f"搜索文件: {search_response.status_code}")
            print(f"搜索结果数量: {search_response.json().get('data', {}).get('total', 0)}")
            assert search_response.status_code == 200

            # 6. 删除用户
            print("\n=== 步骤6: 删除用户 ===")
            params = {"username": "integration_test_user"}
            params.update(token_params)
            delete_response = await client.post("/user/delete", params=params)
            print(f"删除用户: {delete_response.status_code} - {delete_response.json()}")
            assert delete_response.status_code == 200

            print("\n=== 集成测试完成 ===")


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v", "-s"])
