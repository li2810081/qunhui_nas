# SSH 密钥配置说明

## 密钥文件配置

从安全角度考虑，本项目使用 SSH 私钥文件而不是将私钥直接存储在环境变量中。

### 配置步骤

1. **生成 SSH 密钥对**（如果还没有）

```bash
# 生成 ED25519 密钥（推荐）
ssh-keygen -t ed25519 -f ~/.ssh/nas_key -C "nas_manager"

# 或生成 RSA 密钥
ssh-keygen -t rsa -b 4096 -f ~/.ssh/nas_key -C "nas_manager"
```

2. **将公钥添加到 Synology NAS**

```bash
# 复制公钥到 NAS
ssh-copy-id -i ~/.ssh/nas_key.pub abc@nas242

# 或手动添加公钥内容到 NAS 的 ~/.ssh/authorized_keys
cat ~/.ssh/nas_key.pub | ssh abc@nas242 "cat >> ~/.ssh/authorized_keys"
```

3. **配置 .env 文件**

```bash
# Windows 示例（使用默认的 id_rsa）
RSA_PRIVATE_KEY_FILE=C:\Users\your_username\.ssh\id_rsa

# Linux/Mac 示例（使用默认的 id_rsa）
RSA_PRIVATE_KEY_FILE=/home/your_username/.ssh/id_rsa

# 或者使用自定义密钥文件
# RSA_PRIVATE_KEY_FILE=C:\Users\your_username\.ssh\nas_key
```

**注意**：
- 如果使用默认的 `id_rsa`，确保该文件存在
- Windows 路径使用反斜杠 `\` 或正斜杠 `/` 都可以
- Linux/Mac 路径使用正斜杠 `/`

4. **测试 SSH 连接**

```bash
# 测试密钥是否可以连接
ssh -i ~/.ssh/nas_key abc@nas242
```

5. **启动应用**

```bash
uv run python main.py
```

## 安全注意事项

- ✅ **私钥文件权限**：确保私钥文件只有当前用户可读（Windows: 600, Linux/Mac: 400）
- ✅ **不要提交私钥**：`.gitignore` 已配置排除所有密钥文件
- ✅ **使用密钥密码**：生产环境建议使用带密码保护的密钥
- ✅ **定期轮换**：定期更换 SSH 密钥对
- ❌ **不要共享私钥**：私钥文件绝对不要分享给他人

## 故障排查

### 私钥文件不存在
```
错误: SSH私钥文件不存在: /path/to/key.pem
解决: 检查 .env 中的 RSA_PRIVATE_KEY_FILE 路径是否正确
```

### 私钥格式错误
```
错误: 无法加载SSH私钥: Missing PEM footer
解决: 确保密钥文件是完整的 PEM 格式（包含 BEGIN 和 END 标记）
```

### 权限被拒绝
```
错误: Permission denied (publickey)
解决:
1. 确认公钥已添加到 NAS 的 authorized_keys
2. 检查 NAS SSH 配置允许公钥认证
3. 验证使用的用户名正确
```

## 支持的密钥格式

- **RSA**: 最低 2048 位，推荐 4096 位
- **ED25519**: 推荐，更安全且更快速
- **ECDSA**: 支持 NIST P-256/P-384/P-521

示例密钥文件格式：
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZWQy
...（密钥内容）...
AAECAwQF
-----END OPENSSH PRIVATE KEY-----
```
