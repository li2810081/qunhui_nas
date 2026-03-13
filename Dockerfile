# 使用 Python 3.13 基础镜像
FROM python:3.13-slim

# 安装 uv（使用官方推荐的方式）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 设置环境变量
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1
# 配置 UV 国内镜像源加速
ENV UV_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# 设置工作目录
WORKDIR /app

# 复制依赖配置文件
COPY pyproject.toml uv.lock ./

# 安装依赖（保留 --no-dev，移除 --no-install-project）
RUN uv sync --frozen --no-dev

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "main.py"]
