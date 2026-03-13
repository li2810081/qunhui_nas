# 群晖 NAS 管理 API (Qunhui NAS Manager)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

一个基于 FastAPI 的群晖 (Synology) NAS 管理服务，提供用户管理、文件操作和搜索功能的 RESTful API。

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [API 文档](#-api-接口) • [测试](#-测试)

</div>

## ✨ 功能特性

### 👤 用户管理
- ✅ 创建用户（支持自定义描述）
- ✅ 启用/禁用用户
- ✅ 删除用户
- ✅ 获取用户列表
- ✅ 添加用户到组

### 📁 文件管理
- ✅ 上传文件（支持 multipart/form-data）
- ✅ 下载文件（自动识别 MIME 类型）
- ✅ 文件搜索（使用 Universal Search API）

### 🔐 安全机制
- **Token 认证**：所有 API 请求需携带有效的 Token
- **IP 白名单**：支持 IP 地址限制（可选）
- **会话管理**：使用单例模式管理 NAS 连接
- **代理支持**：自动识别 X-Forwarded-For 和 X-Real-IP 头

## 📋 项目结构

```
qunhui_nas/
├── app/
│   ├── __init__.py
│   ├── auth.py          # Token 和 IP 鉴权模块
│   ├── config.py        # 配置管理
│   ├── file.py          # 文件管理 API
│   ├── search.py        # 搜索 API
│   └── user.py          # 用户管理 API
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # 测试配置
│   ├── test_api.py      # API 测试套件
│   └── README.md        # 测试文档
├── main.py              # 应用入口
├── .env.example         # 环境变量示例
├── docker-compose.yml   # Docker 部署配置
├── pyproject.toml       # 项目依赖配置
└── README.md            # 项目文档
```

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

1. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/qunhui_nas.git
   cd qunhui_nas
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的 NAS 配置
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

   服务将在 `http://localhost:8000` 启动

### 方式二：本地运行 (使用 UV)

1. **安装 uv**
   ```bash
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   # Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **安装依赖**
   ```bash
   uv pip install -e ".[test]"
   ```

3. **运行服务**
   ```bash
   uv run main.py
   ```

   服务将在 `http://localhost:8000` 启动

## ⚙️ 配置说明

### 环境变量

在 `.env` 文件中配置以下项：

| 变量名 | 必需 | 说明 | 示例 |
|:---|:---:|:---|:---|
| `DSM_HOST` | ✅ | NAS 的 IP 地址或主机名 | `192.168.1.10` |
| `DSM_PORT` | ✅ | DSM API 端口 | `5001` |
| `NAS_USER` | ✅ | NAS 用户名 | `admin` |
| `NAS_PASSWORD` | ✅ | NAS 密码 | `your_password` |
| `TOKEN` | ✅ | API 认证 Token | `my_secret_token` |
| `ALLOW_IP` | ❌ | IP 白名单（逗号分隔） | `127.0.0.1,192.168.1.0/24` |

### 配置示例

```bash
# .env 文件示例
DSM_HOST=192.168.1.100
DSM_PORT=5001
NAS_USER=admin
NAS_PASSWORD=SecurePassword123!
TOKEN=your_api_token_here
ALLOW_IP=127.0.0.1,192.168.1.0/24
```

## 🔌 API 接口

### 认证方式

所有 API 请求需通过 URL 参数携带 Token：

```
?token=YOUR_TOKEN
```

**错误响应：**
- `401 Unauthorized` - 缺少 Token
- `403 Forbidden` - Token 无效

### 用户管理 API

#### 1. 获取用户列表
```http
GET /user/list?token=YOUR_TOKEN
```

**响应示例：**
```json
{
  "data": {
    "users": [
      {"name": "admin"},
      {"name": "user1"}
    ],
    "total": 2
  },
  "success": true
}
```

#### 2. 创建用户
```http
POST /user/create?token=YOUR_TOKEN
Content-Type: application/x-www-form-urlencoded
```

**参数：**
| 参数 | 类型 | 必需 | 说明 |
|:---|:---:|:---:|:---|
| username | string | ✅ | 用户名 |
| password | string | ✅ | 密码 |
| description | string | ❌ | 用户描述 |

**示例：**
```bash
curl -X POST "http://localhost:8000/user/create?token=YOUR_TOKEN" \
  -d "username=newuser" \
  -d "password=SecurePass123!" \
  -d "description=新用户"
```

#### 3. 启用/禁用用户
```http
POST /user/enable?token=YOUR_TOKEN&username=testuser
POST /user/disable?token=YOUR_TOKEN&username=testuser
```

#### 4. 删除用户
```http
POST /user/delete?token=YOUR_TOKEN&username=testuser
```

#### 5. 添加用户到组
```http
POST /user/add_to_group?token=YOUR_TOKEN&username=testuser&groupname=users
```

### 文件管理 API

#### 1. 上传文件
```http
POST /drive/upload?token=YOUR_TOKEN
Content-Type: multipart/form-data
```

**参数：**
| 参数 | 类型 | 必需 | 说明 |
|:---|:---:|:---:|:---|
| dest_path | string | ✅ | 目标路径（如 `/home`） |
| file | file | ✅ | 要上传的文件 |

**示例 (curl)：**
```bash
curl -X POST "http://localhost:8000/drive/upload?token=YOUR_TOKEN" \
  -F "file=@/path/to/local/file.txt" \
  -F "dest_path=/home"
```

**示例 (Python)：**
```python
import requests

files = {'file': open('local_file.txt', 'rb')}
data = {'dest_path': '/home'}
response = requests.post(
    'http://localhost:8000/drive/upload',
    params={'token': 'YOUR_TOKEN'},
    files=files,
    data=data
)
```

**响应示例：**
```json
{
  "success": true,
  "message": "上传成功",
  "filename": "file.txt",
  "dest_path": "/home"
}
```

#### 2. 下载文件
```http
GET /drive/download/{file_path}?token=YOUR_TOKEN
```

**示例：**
```bash
# 使用 curl 下载
curl -O "http://localhost:8000/drive/download/home/test.txt?token=YOUR_TOKEN"

# 使用 wget 下载
wget "http://localhost:8000/drive/download/home/test.txt?token=YOUR_TOKEN" \
  -O downloaded_file.txt
```

### 搜索 API

#### 1. 搜索文件
```http
GET /search/?token=YOUR_TOKEN&query=keyword
```

**参数：**
| 参数 | 类型 | 必需 | 说明 |
|:---|:---:|:---:|:---|
| query | string | ✅ | 搜索关键词 |

**响应示例：**
```json
{
  "data": {
    "hits": [
      {
        "SYNOMDPath": "/volume1/home/document.txt",
        "SYNOMDFSName": "document.txt",
        "SYNOMDFSSize": "1024"
      }
    ],
    "total": 1
  },
  "success": true
}
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试类
pytest tests/test_api.py::TestUserAPI -v

# 运行特定测试方法
pytest tests/test_api.py::TestUserAPI::test_create_user -v

# 显示详细输出
pytest tests/ -v -s

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

### 测试覆盖

| 测试类 | 测试内容 | 数量 |
|:---|:---|:---:|
| TestUserAPI | 用户管理测试 | 4 |
| TestFileAPI | 文件上传下载测试 | 3 |
| TestSearchAPI | 搜索功能测试 | 1 |
| TestAuth | 鉴权测试 | 2 |
| TestHealthCheck | 健康检查 | 2 |
| TestIntegration | 集成测试 | 1 |

**总计：13 个测试用例**

## 📚 API 文档

启动服务后访问交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 安全建议

1. **保护 Token**
   - 不要在代码中硬编码 Token
   - 使用环境变量管理敏感信息
   - 定期更换 Token

2. **使用 HTTPS**
   - 生产环境必须使用 HTTPS
   - 配置 SSL 证书

3. **IP 白名单**
   - 配置 `ALLOW_IP` 限制访问来源
   - 只允许可信的 IP 地址访问

4. **最小权限原则**
   - 为 NAS 用户分配最小必要权限
   - 定期审计用户权限

5. **日志监控**
   - 监控 API 访问日志
   - 及时发现异常访问

## ❓ 常见问题

### Q: 如何生成安全的 Token？

A: 使用随机字符串生成器：

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32

# Linux
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
```

### Q: 上传文件大小有限制吗？

A: 限制由 NAS 的 DSM API 和 FastAPI 配置决定。默认情况下，FastAPI 支持 100MB 以下的文件。

### Q: 支持批量操作吗？

A: 目前不支持批量操作，需要多次调用 API。

### Q: 如何处理密码强度错误？

A: 群晖 NAS 要求密码包含：
- 至少 8 个字符
- 大写字母
- 小写字母
- 数字

示例：`SecurePass123!`

### Q: API 返回的错误码有哪些？

A: 常见错误码：

| 状态码 | 说明 |
|:---:|:---|
| 200 | 成功 |
| 401 | 缺少 Token |
| 403 | Token 无效或 IP 不在白名单 |
| 404 | 文件或资源不存在 |
| 500 | 服务器内部错误 |

## 🛠️ 开发指南

### 本地开发

```bash
# 1. 克隆项目
git clone <repo-url>
cd qunhui_nas

# 2. 创建虚拟环境
uv venv

# 3. 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 4. 安装依赖
uv pip install -e ".[test]"

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 6. 运行服务
uv run main.py

# 7. 运行测试
pytest tests/ -v
```

### 代码风格

本项目遵循以下代码规范：
- PEP 8 编码规范
- 使用类型注解
- 编写文档字符串
- 保持测试覆盖率 > 80%

## 📝 更新日志

### v1.0.0 (2025-03-13)
- ✨ 初始版本发布
- ✅ 用户管理 API
- ✅ 文件上传下载 API
- ✅ 文件搜索 API
- ✅ Token 鉴权机制
- ✅ IP 白名单支持
- ✅ 完整的测试套件

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

- 提交 Issue: [GitHub Issues](https://github.com/your-repo/qunhui_nas/issues)

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️**

Made with ❤️ by [Your Name]
</div>
