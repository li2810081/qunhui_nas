"""
测试配置文件
提供测试所需的 fixtures 和配置
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "test_user",
        "password": "TestPassword123!",
        "description": "测试用户"
    }


@pytest.fixture
def sample_file_content():
    """示例文件内容"""
    return """这是一个测试文件
用于测试文件上传和下载功能
Hello, NAS API!
"""
