# SUDO 免密配置指南

## 问题说明

`abc` 用户需要执行 Synology 管理命令，但这些命令需要 root 权限。

错误信息：
```
sh: /usr/syno/sbin/synouser: Permission denied
```

## 解决方案：配置 Sudo 免密执行

### 步骤 1：SSH 登录到 NAS

```bash
ssh abc@nas242
```

输入密码后登录。

### 步骤 2：切换到 root 用户

```bash
sudo -i
```

需要输入 `abc` 用户的密码。

### 步骤 3：使用 visudo 编辑 sudoers

```bash
visudo
```

**⚠️ 重要提示：**
- ✅ 必须使用 `visudo` 命令编辑
- ❌ 不要直接编辑 /etc/sudoers 文件
- ✅ visudo 会自动验证语法，防止配置错误

### 步骤 4：添加免密规则

在 visudo 打开的编辑器中，滚动到文件末尾，添加以下内容：

```bash
# 允许 abc 用户免密执行 Synology 管理命令
abc ALL=(ALL) NOPASSWD: /usr/syno/sbin/synouser
abc ALL=(ALL) NOPASSWD: /usr/syno/sbin/synogroup
```

### 步骤 5：保存并退出

- 按 `ESC` 键
- 输入 `:wq` （冒号 + w + q）
- 按 `Enter` 键

### 步骤 6：验证配置

退出 root，回到 abc 用户：

```bash
exit
```

测试是否能免密执行命令：

```bash
sudo /usr/syno/sbin/synouser --help
```

如果能看到帮助信息，说明配置成功！

### 步骤 7：重启应用程序

```bash
# 在 Windows 上停止当前运行的应用 (Ctrl+C)
# 然后重新启动
cd e:\qunhui_nas
uv run python main.py
```

## 测试命令

### 测试用户创建

```bash
curl -X POST "http://localhost:8000/user/create?token=test_token_1" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123","groups":["users"]}'
```

### 测试用户启用

```bash
curl -X POST "http://localhost:8000/user/enable?token=test_token_1" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser"}'
```

### 测试用户禁用

```bash
curl -X POST "http://localhost:8000/user/disable?token=test_token_1" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser"}'
```

## 常见问题

### 问题 1：visudo 命令不存在

```bash
# 确保 PATH 包含 sbin
export PATH=$PATH:/usr/sbin:/usr/bin:/bin
visudo
```

### 问题 2：仍然提示需要密码

检查 sudoers 配置：

```bash
sudo -l
```

应该看到类似输出：
```
User abc may run the following commands on nas242:
    (ALL) NOPASSWD: /usr/syno/sbin/synouser
    (ALL) NOPASSWD: /usr/syno/sbin/synogroup
```

### 问题 3：语法错误

如果保存时出现语法错误，选择：
- `e` - 重新编辑
- `x` - 退出不保存

然后重新检查配置语法。

## 完整的 sudoers 示例

```
# /etc/sudoers
#
# This file MUST be edited with the 'visudo' command as root.
#

Defaults env_reset
Defaults mail_badpass
Defaults secure_path="/usr/sbin:/usr/bin:/sbin:/bin"

# User privilege specification
root ALL=(ALL:ALL) ALL

# Allow members of group sudo to execute any command
%sudo ALL=(ALL:ALL) ALL

# 允许 abc 用户免密执行 Synology 管理命令
abc ALL=(ALL) NOPASSWD: /usr/syno/sbin/synouser
abc ALL=(ALL) NOPASSWD: /usr/syno/sbin/synogroup

# See sudoers(5) for more information on "#include" directives:
#includedir /etc/sudoers.d
```

## 安全建议

1. ✅ 只授予必要的命令权限（最小权限原则）
2. ✅ 定期审查 sudoers 配置
3. ✅ 监控 sudo 使用日志：`sudo journalctl -u ssh`
4. ✅ 使用强密码保护 abc 账户
5. ✅ 限制 SSH 访问来源 IP（已在 .env 中配置）
