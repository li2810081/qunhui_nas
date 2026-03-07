# 群晖 NAS 管理 API (Qunhui NAS Manager)

这是一个基于 FastAPI 的 Webhook 服务，旨在通过 HTTP 请求安全地管理群晖 (Synology) NAS。它通过 SSH 连接到 NAS 执行命令，支持用户管理和文件操作。

## ✨ 功能特性

*   **用户管理**：
    *   创建用户（自动分配用户组，支持幂等性：用户存在时自动跳过创建仅更新组）。
    *   启用/禁用用户。
    *   自动生成用户邮箱（支持自定义域名）。
*   **文件操作**：
    *   读取指定路径的文件内容。
    *   向指定路径写入文件内容。
*   **安全机制**：
    *   **Token 认证**：请求必须携带有效的 Token。
    *   **IP 白名单**：支持 IP 地址限制，**支持 Docker 容器名/主机名**（自动解析）。
    *   **路径限制**：文件操作仅限配置的允许路径。
*   **部署灵活**：支持本地运行和 Docker 容器化部署。

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

1.  **克隆项目**
    ```bash
    git clone <your-repo-url>
    cd qunhui_nas
    ```

2.  **配置环境变量**
    复制示例配置文件并修改：
    ```bash
    cp env.example .env
    ```
    编辑 `.env` 文件，填入你的 NAS SSH 信息和 Token。

3.  **启动服务**
    ```bash
    docker-compose up -d
    ```
    服务将在端口 `8000` 启动。

### 方式二：本地运行 (使用 UV)

本项目使用 [uv](https://github.com/astral-sh/uv) 进行依赖管理。

1.  **安装 uv**
    ```bash
    # Windows (PowerShell)
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    # Linux/macOS
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **配置环境**
    ```bash
    cp env.example .env
    # 编辑 .env 文件
    ```

3.  **运行服务**
    ```bash
    uv run main.py
    ```

## ⚙️ 配置说明

在 `.env` 文件或 Docker 环境变量中配置以下项：

| 变量名 | 说明 | 示例 / 默认值 |
| :--- | :--- | :--- |
| `NAS_HOST` | NAS 的 IP 地址或主机名 | `192.168.1.10` |
| `NAS_PORT` | SSH 端口 | `22` |
| `NAS_USER` | SSH 用户名 (需有 sudo 权限) | `admin_user` |
| `NAS_PASSWORD` | SSH 密码 | `your_password` |
| `SUDO_PASSWORD` | Sudo 密码 (通常同 SSH 密码) | `your_password` |
| `TOKEN` | API 认证 Token (逗号分隔支持多个) | `my_secret_token_123` |
| `ALLOW_IP` | 允许访问的 IP 或主机名 (逗号分隔) | `127.0.0.1,my-web-app` (Docker环境下留空则允许所有) |
| `ALLOW_FILE_PATH` | 允许读写的文件路径前缀 | `/volume1/docker/configs` |
| `MAIL_DOMAIN` | 创建用户时的默认邮箱域名后缀 | `company.com` (生成 user@company.com) |

## 🔌 API 接口

所有请求需携带 Query 参数 `token`。

### 1. 创建用户
**POST** `/user/create?token=YOUR_TOKEN`

```json
{
  "username": "zhangsan",
  "password": "Password123!",
  "groups": ["users", "administrators"]
}
```
> **注意**：如果用户已存在，将跳过创建步骤，直接确保用户被添加到指定的组中。

### 2. 禁用用户
**POST** `/user/disable?token=YOUR_TOKEN`

```json
{
  "username": "zhangsan"
}
```

### 3. 启用用户
**POST** `/user/enable?token=YOUR_TOKEN`

```json
{
  "username": "zhangsan"
}
```

### 4. 读写文件
**POST** `/file/read` 或 `/file/write`
(需在 `ALLOW_FILE_PATH` 允许范围内)

## 🛠️ 开发与调试

*   **本地调试**：推荐直接使用 `uv run main.py`，可以在终端看到实时日志。
*   **Docker 调试**：
    ```bash
    docker-compose logs -f
    ```
*   **密码强度错误 (0x1C00)**：Synology 对密码强度有默认要求（通常包含大小写字母和数字），请确保传递的密码符合 NAS 的安全策略。

## ⚠️ 注意事项

*   **SSH 权限**：配置的 `NAS_USER` 必须具有 SSH 登录权限，并且在 NAS 上有执行 `sudo` 的权限（通常是管理员组）。
*   **安全风险**：本服务拥有较高的系统权限，请务必保护好 `TOKEN`，并建议通过 `ALLOW_IP` 限制仅允许可信来源访问。
