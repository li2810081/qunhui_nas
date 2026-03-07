# 快速开始指南

## 使用现有的 id_rsa 密钥

如果您已经有一个 `id_rsa` 密钥文件（通常位于 `~/.ssh/` 目录），可以直接使用它。

### Windows 配置示例

1. **找到您的密钥文件**
   ```powershell
   # 查看默认 SSH 密钥位置
   dir C:\Users\your_username\.ssh\
   ```

2. **编辑 .env 文件**
   ```bash
   # 将路径修改为您的实际路径
   RSA_PRIVATE_KEY_FILE=C:\Users\your_username\.ssh\id_rsa
   ```

3. **确保密钥文件权限正确**
   ```powershell
   # 设置只有您能访问（在文件属性 -> 安全 中设置）
   icacls "C:\Users\your_username\.ssh\id_rsa" /inheritance:r
   icacls "C:\Users\your_username\.ssh\id_rsa" /grant:r "$env:USERNAME:F"
   ```

### Linux/Mac 配置示例

1. **找到您的密钥文件**
   ```bash
   ls -la ~/.ssh/id_rsa
   ```

2. **编辑 .env 文件**
   ```bash
   # 将路径修改为您的实际路径
   RSA_PRIVATE_KEY_FILE=/home/your_username/.ssh/id_rsa
   # 或使用 $HOME 变量
   # RSA_PRIVATE_KEY_FILE=$HOME/.ssh/id_rsa
   ```

3. **确保密钥文件权限正确**
   ```bash
   chmod 600 ~/.ssh/id_rsa
   ```

### 将公钥添加到 NAS

```bash
# 复制公钥到 NAS
ssh-copy-id -i ~/.ssh/id_rsa.pub abc@nas242

# 或手动添加
cat ~/.ssh/id_rsa.pub | ssh abc@nas242 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys'
```

### 测试连接

```bash
# 测试 SSH 连接
ssh -i ~/.ssh/id_rsa abc@nas242

# 如果连接成功，启动应用
uv run python main.py
```

### 完整 .env 配置示例

```bash
# 连接TOKEN
TOKEN=test_token_1,test_token_2

# 允许访问的IP
ALLOW_IP=127.0.0.1,192.168.1.1

# 允许访问的文件路径
ALLOW_FILE_PATH=/volume1/docker,/volume1/homes

# SSH私钥文件路径
RSA_PRIVATE_KEY_FILE=C:\Users\yourname\.ssh\id_rsa

# NAS连接配置
NAS_HOST=nas242
NAS_USER=abc
NAS_PORT=22
```

### 故障排查

**问题：权限被拒绝**
```
Permission denied (publickey)
```
**解决方案**：
1. 确认公钥已添加到 NAS
2. 检查密钥文件权限是否正确
3. 验证 .env 中的路径是否正确

**问题：找不到密钥文件**
```
SSH私钥文件不存在: C:\Users\...\.ssh\id_rsa
```
**解决方案**：
1. 检查密钥文件是否存在
2. 确认路径拼写正确
3. 尝试使用绝对路径

**问题：密钥格式错误**
```
无法加载SSH私钥: Missing PEM footer
```
**解决方案**：
1. 确保密钥文件完整（包含 BEGIN 和 END 标记）
2. 检查文件是否被意外修改或损坏
