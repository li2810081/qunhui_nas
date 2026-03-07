# Synology NAS 权限配置指南

## 问题说明

当使用非 root 用户运行管理命令时，会遇到权限错误：

```
sh: /usr/syno/sbin/synouser: Permission denied
```

## 解决方案对比

### 方案 1：使用 root 用户（推荐⭐）

**优点：**
- ✅ 最简单，无需额外配置
- ✅ 直接拥有所有管理权限
- ✅ 避免 sudo 配置问题

**操作步骤：**

1. 修改 `.env` 文件：
   ```bash
   NAS_USER=root
   ```

2. 确保 root 用户可以 SSH 登录：
   ```bash
   # 测试 root 登录
   ssh root@nas242
   ```

3. 如果 root 无法 SSH 登录，需要在 NAS 上启用：
   - 登录 DSM 管理界面
   - 控制面板 → 终端机 & SNMP
   - 启用 SSH 服务
   - 允许 root 用户登录（可能需要在 DSM 中设置）

---

### 方案 2：配置 sudo（复杂）

**警告：** 此方案配置较复杂，容易出错，不推荐新手使用。

#### 步骤 1：登录 NAS

```bash
ssh abc@nas242
```

#### 步骤 2：切换到 root 用户

```bash
sudo -i
```

#### 步骤 3：使用 visudo 编辑 sudoers

```bash
visudo
```

**⚠️ 重要提示：**
- ❌ 不要直接在命令行输入 sudoers 配置
- ❌ 不要用普通文本编辑器编辑 /etc/sudoers
- ✅ 必须使用 `visudo` 命令编辑
- ✅ visudo 会自动验证语法，防止配置错误

#### 步骤 4：添加 sudo 规则

在 visudo 打开的编辑器中，添加以下行（在文件末尾）：

```bash
# 允许 abc 用户免密执行 synouser 和 synogroup
abc ALL=(ALL) NOPASSWD: /usr/syno/sbin/synouser
abc ALL=(ALL) NOPASSWD: /usr/syno/sbin/synogroup
```

#### 步骤 5：保存并退出

- 按 `ESC` 键
- 输入 `:wq` （冒号+w+q）
- 按 `Enter` 键

#### 步骤 6：测试 sudo 配置

```bash
# 退出 root，回到 abc 用户
exit

# 测试是否能免密执行命令
sudo /usr/syno/sbin/synouser --help
```

如果能看到帮助信息，说明配置成功！

---

## synouser 命令格式说明

### 正确的命令格式

```bash
/usr/syno/sbin/synouser --add <username> <password> "<fullname>" <expired> <mail>
```

**参数说明：**
- `username`: 用户名
- `password`: 密码（避免特殊字符）
- `fullname`: 全名（用引号包围）
- `expired`: 过期时间（0 = 永不过期，1 = 已过期）
- `mail`: 邮箱地址（可以为空字符串）

**示例：**

```bash
# 正确的命令
/usr/syno/sbin/synouser --add testuser password123 "Test User" 0 "testuser@example.com"

# 简化的命令（无邮箱）
/usr/syno/sbin/synouser --add testuser password123 "Test User" 0 ""
```

### 错误示例

❌ **错误的命令：**
```bash
# 缺少引号
/usr/syno/sbin/synouser --add testuser password123 Test User 0 testuser@local

# 使用单引号（在某些 shell 中会有问题）
/usr/syno/sbin/synouser --add testuser password123 'Test User' 0 'testuser@local'
```

✅ **正确的命令：**
```bash
# 使用双引号包围全名
/usr/syno/sbin/synouser --add testuser password123 "Test User" 0 ""
```

---

## 测试命令

### 测试用户创建

```bash
# 使用 root 用户
/usr/syno/sbin/synouser --add testuser pass123 "Test User" 0 ""

# 或使用 sudo（如果已配置）
sudo /usr/syno/sbin/synouser --add testuser pass123 "Test User" 0 ""
```

### 测试用户启用/禁用

```bash
# 启用用户
/usr/syno/sbin/synouser --set_enable testuser 1

# 禁用用户
/usr/syno/sbin/synouser --set_enable testuser 0
```

### 查看用户列表

```bash
/usr/syno/sbin/synouser --list
```

---

## 常见问题排查

### 问题 1：visudo 命令不存在

**解决方案：**
```bash
# 确保 PATH 包含 sbin
export PATH=$PATH:/usr/sbin:/usr/bin:/bin

# 然后运行 visudo
visudo
```

### 问题 2：权限仍然被拒绝

**检查步骤：**
```bash
# 1. 确认 sudo 配置
sudo -l

# 2. 测试具体命令
sudo /usr/syno/sbin/synouser --help

# 3. 如果仍然失败，使用 root 用户
su -
```

### 问题 3：SSH 密钥无权限访问

**解决方案：**
```bash
# 修复 .env 配置，使用 root
NAS_USER=root
```

---

## 推荐配置

**对于生产环境，推荐使用方案 1（root 用户）：**

```bash
# .env 文件配置
TOKEN=your_secure_token_here
ALLOW_IP=127.0.0.1,192.168.1.100
ALLOW_FILE_PATH=/volume1/docker
RSA_PRIVATE_KEY_FILE=C:\Users\yourname\.ssh\nas242
NAS_HOST=nas242
NAS_USER=root
NAS_PORT=22
```

**安全建议：**
1. 使用强随机 TOKEN
2. 限制 ALLOW_IP 到特定 IP
3. 使用强密码保护的 SSH 密钥
4. 定期更换 TOKEN 和 SSH 密钥
5. 监控日志文件，及时发现异常访问

---

## 应用程序启动测试

配置完成后，启动应用：

```bash
uv run python main.py
```

查看启动日志，确认：
- ✅ SSH 连接成功
- ✅ 权限验证通过
- ✅ 可以正常执行管理命令

如果看到以下日志，说明配置成功：
```
2026-03-06 xx:xx:xx - app.nas - INFO - SSH连接建立成功
2026-03-06 xx:xx:xx - app.nas - INFO - 命令执行完成, 退出码: 0
```
