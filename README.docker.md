# Docker 部署指南

## 快速开始

### 1. 构建镜像

```bash
docker build -t 192.168.2.251:5000/qunhuiinas:latest .
```

### 2. 推送镜像到私有仓库

```bash
docker push 192.168.2.251:5000/qunhuiinas:latest
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env 填写实际配置
```

### 4. 启动服务

```bash
docker-compose up -d
```

## 心跳配置详解

### 为什么需要心跳？

群晖 DSM 的会话有一定超时时间（通常为几分钟到十几分钟）。如果长时间没有 API 调用，会话会失效，导致后续请求失败。

心跳机制通过定期调用健康检查接口，保持 NAS 会话活跃。

### 方案对比

| 方案 | 优点 | 缺点 | 推荐场景 |
|:---|:---|:---|:---|
| **Docker HEALTHCHECK** | 原生支持，自动重启 | 依赖 Docker 守护进程 | 生产环境 ✅ |
| **独立心跳服务** | 更灵活，可精确控制 | 额外容器资源 | 特殊需求 |

### 方案 1: Docker HEALTHCHECK（推荐）

#### Dockerfile 配置

```dockerfile
# 每5分钟检查一次，超时10秒
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

#### docker-compose.yml 配置

```yaml
services:
  api:
    image: 192.168.2.251:5000/qunhuiinas:latest
    healthcheck:
      interval: 5m      # 每5分钟检查一次
      timeout: 10s      # 超时时间10秒
      retries: 3        # 连续失败3次才认为不健康
      start_period: 30s # 容器启动后30秒才开始检查
      test:
        - "CMD"
        - "curl"
        - "-f"
        - "http://localhost:8000/health"
```

#### 参数说明

| 参数 | 说明 | 推荐值 |
|:---|:---|:---|
| `interval` | 检查间隔 | 5m（5分钟） |
| `timeout` | 单次检查超时 | 10s |
| `retries` | 连续失败次数 | 3 |
| `start_period` | 启动宽限期 | 30s |

#### 心跳间隔建议

根据 NAS 会话超时时间设置：

| NAS 会话超时 | 推荐心跳间隔 | 说明 |
|:---|:---|:---|
| 15 分钟 | 5 分钟 | 超时的 1/3 |
| 30 分钟 | 10 分钟 | 超时的 1/3 |
| 1 小时 | 20 分钟 | 超时的 1/3 |

### 方案 2: 独立心跳服务

适用于需要更精细控制的场景。

```yaml
services:
  api:
    image: 192.168.2.251:5000/qunhuiinas:latest
    # ... 其他配置

  heartbeat:
    image: curlimages/curl:latest
    network_mode: host
    restart: unless-stopped
    command: >
      sh -c "
      while true; do
        curl -s http://localhost:8000/health > /dev/null 2>&1 || true;
        sleep 300;
      done
      "
    depends_on:
      api:
        condition: service_healthy
```

## 监控和维护

### 查看容器健康状态

```bash
# 查看所有容器状态
docker ps

# 查看具体健康状态
docker inspect --format='{{.State.Health.Status}} <container_id>'

# 输出示例：
# healthy   - 健康
# unhealthy - 不健康
# starting  - 启动中
```

### 查看健康检查日志

```bash
# 查看最近5次健康检查结果
docker inspect --format='{{json .State.Health}}' <container_id> | jq

# 查看健康检查输出
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' <container_id>
```

### 手动触发健康检查

```bash
# 进入容器
docker exec -it <container_id> sh

# 执行健康检查命令
curl -f http://localhost:8000/health
```

## 故障排查

### 容器显示 unhealthy

1. **检查网络连接**
   ```bash
   docker exec -it <container_id> ping ${DSM_HOST}
   ```

2. **检查环境变量**
   ```bash
   docker exec -it <container_id> env | grep -E "DSM_|NAS_|TOKEN"
   ```

3. **查看应用日志**
   ```bash
   docker logs <container_id>
   ```

4. **测试健康检查接口**
   ```bash
   curl http://localhost:8000/health
   ```

### 会话仍然超时

如果心跳正常但会话仍然超时：

1. **增加心跳频率**
   ```yaml
   healthcheck:
     interval: 3m  # 从 5m 改为 3m
   ```

2. **检查 NAS 配置**
   - DSM 会话超时设置
   - 网络连接稳定性

3. **查看健康检查日志**
   ```bash
   docker inspect --format='{{range .State.Health.Log}}{{.Start}} - {{.Output}}{{end}}' <container_id>
   ```

## 生产环境建议

1. **使用私有镜像仓库**
   ```yaml
   image: your-registry.com/qunhuiinas:latest
   ```

2. **配置资源限制**
   ```yaml
   services:
     api:
       deploy:
         resources:
           limits:
             cpus: '0.5'
             memory: 512M
   ```

3. **启用日志驱动**
   ```yaml
   services:
     api:
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   ```

4. **配置重启策略**
   ```yaml
   restart: unless-stopped  # 已配置
   ```

5. **监控告警**
   - 集成 Prometheus + Grafana
   - 使用健康检查状态触发告警
