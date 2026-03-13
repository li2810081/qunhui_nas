# API 接口测试说明

本目录包含群晖NAS管理API的接口测试。

## 测试内容

### 1. 用户管理测试 (`TestUserAPI`)
- ✅ 新增用户 - `test_create_user`
- ✅ 启用用户 - `test_enable_user`
- ✅ 获取用户列表 - `test_list_users`
- ✅ 删除用户 - `test_delete_user`

### 2. 文件管理测试 (`TestFileAPI`)
- ✅ 上传文件 - `test_upload_file`
- ✅ 下载文件 - `test_download_file`
- ✅ 列出文件 - `test_list_files`

### 3. 搜索测试 (`TestSearchAPI`)
- ✅ 搜索文件 - `test_search_files`

### 4. 集成测试 (`TestIntegration`)
- ✅ 完整工作流程测试 - `test_complete_workflow`
  - 创建用户 → 启用用户 → 上传文件 → 下载文件 → 搜索文件 → 删除用户

## 运行测试

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定测试类
```bash
# 只测试用户管理
pytest tests/test_api.py::TestUserAPI -v

# 只测试文件管理
pytest tests/test_api.py::TestFileAPI -v

# 只测试搜索
pytest tests/test_api.py::TestSearchAPI -v

# 只运行集成测试
pytest tests/test_api.py::TestIntegration -v
```

### 运行特定测试方法
```bash
pytest tests/test_api.py::TestUserAPI::test_create_user -v
```

### 显示详细输出
```bash
pytest tests/test_api.py -v -s
```

### 生成测试报告
```bash
# 生成 HTML 报告
pytest tests/test_api.py --html=report.html

# 生成覆盖率报告
pytest tests/test_api.py --cov=app --cov-report=html
```

## 环境要求

在运行测试前，请确保：

1. 安装依赖：
```bash
pip install pytest pytest-asyncio pytest-cov pytest-html httpx
```

2. 配置 `.env` 文件：
```env
# NAS SSH 配置
nas_host=your_nas_ip
nas_port=22
nas_user=your_username
nas_password=your_password
sudo_password=your_sudo_password

# 文件路径配置
allow_file_path=/volume1/test

# 认证配置
token=your_test_token

# DSM API 配置
dsm_host=your_nas_ip
dsm_port=5001
```

## 注意事项

1. **文件操作需要配置**：文件上传/下载测试需要配置 `allow_file_path` 和 `token`
2. **测试数据隔离**：建议使用测试专用用户，避免影响生产数据
3. **清理测试数据**：测试完成后会自动删除创建的测试用户
4. **SSH 连接**：确保能够通过 SSH 连接到 NAS

## 测试输出示例

```
tests/test_api.py::TestUserAPI::test_create_user PASSED
tests/test_api.py::TestUserAPI::test_enable_user PASSED
tests/test_api.py::TestUserAPI::test_list_users PASSED
tests/test_api.py::TestUserAPI::test_delete_user PASSED
tests/test_api.py::TestFileAPI::test_upload_file PASSED
tests/test_api.py::TestFileAPI::test_download_file PASSED
tests/test_api.py::TestSearchAPI::test_search_files PASSED
tests/test_api.py::TestIntegration::test_complete_workflow PASSED

=== 8 passed in 5.23s ===
```

## 故障排查

### 测试失败
1. 检查 `.env` 配置是否正确
2. 确认 NAS 服务可访问
3. 检查 SSH 连接是否正常
4. 查看详细错误信息：`pytest tests/ -v -s`

### 权限问题
文件操作需要 sudo 权限，确保配置了正确的 `sudo_password`

### 跳过测试
如果配置不完整，某些测试会被自动跳过（使用 `pytest.skip`）
