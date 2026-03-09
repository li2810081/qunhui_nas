"""
NAS操作模块
使用SSH连接到Synology NAS,执行用户管理和文件操作
"""
import asyncio
import logging
import time
from typing import Optional, Tuple
import asyncssh
from .config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class NASConnectionError(Exception):
    """SSH连接错误"""
    pass


class NASCommandError(Exception):
    """命令执行错误"""
    pass


class NASWeakPasswordError(NASCommandError):
    """密码强度不足"""
    pass


class NASClient:
    """NAS SSH客户端"""

    def __init__(self):
        """初始化SSH客户端"""
        self._conn: Optional[asyncssh.SSHClientConnection] = None

    async def connect(self) -> asyncssh.SSHClientConnection:
        """
        建立SSH连接（使用密码认证）
        """
        if self._conn is not None:
            try:
                await self._conn.wait_closed()
                self._conn = None
            except:
                self._conn = None

        try:
            # 检查连接是否活跃
            if self._conn:
                try:
                    # 尝试发送心跳或检查连接状态
                    # asyncssh没有直接的ping方法，通过检查_transport来判断
                    if self._conn._transport is None or self._conn._transport.is_closing():
                        self._conn = None
                except Exception:
                    self._conn = None

            if self._conn is None:
                logger.info(f"正在连接NAS: {settings.nas_host}:{settings.nas_port}")

                # 检查密码是否配置
                if not settings.nas_password:
                    logger.error("SSH密码未配置")
                    raise NASConnectionError("SSH密码未配置")

                # 使用密码认证建立连接
                # 设置 connect_timeout 以防止连接挂起
                self._conn = await asyncssh.connect(
                    host=settings.nas_host,
                    port=settings.nas_port,
                    username=settings.nas_user,
                    password=settings.nas_password,
                    known_hosts=None,  # 生产环境应该验证主机密钥
                    login_timeout=10,  # 登录超时 10秒
                    keepalive_interval=30 # 保持连接活跃
                )
                logger.info("SSH连接建立成功")
            
            return self._conn
        except Exception as e:
            logger.error(f"SSH连接失败: {e}")
            self._conn = None # 确保连接失败时重置
            raise NASConnectionError(f"无法连接到NAS: {e}")

    async def execute_command(
        self,
        command: str,
        use_sudo: bool = False,
        max_retries: int = 0
    ) -> Tuple[str, str, int]:
        """
        执行命令并返回输出

        Args:
            command: 要执行的命令
            use_sudo: 是否使用sudo执行命令
            max_retries: 最大重试次数（默认0，不重试）

        Returns:
            (stdout, stderr, exit_code) 元组
        """
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            start_time = time.time()
            try:
                # 确保连接有效
                if self._conn is None:
                    await self.connect()
                
                # 如果需要使用sudo，添加-S选项从标准输入读取密码
                if use_sudo:
                    if not settings.sudo_password:
                        logger.error("Sudo密码未配置")
                        raise NASCommandError("Sudo密码未配置")
                    # 将命令替换为sudo -S版本
                    if command.startswith("sudo "):
                        # 如果已经是sudo命令，在sudo后添加-S
                        command = command.replace("sudo ", "sudo -S ", 1)
                    else:
                        command = f"sudo -S {command}"
                    logger.info(f"执行命令(使用sudo): {command}")
                    if retry_count > 0:
                        logger.info(f"第 {retry_count} 次重试...")
                    # 通过stdin输入密码，增加超时时间到90秒
                    result = await self._conn.run(
                        command,
                        check=False,
                        input=f"{settings.sudo_password}\n",
                        timeout=90
                    )
                else:
                    logger.info(f"执行命令: {command}")
                    result = await self._conn.run(command, check=False, timeout=90)

                elapsed_time = time.time() - start_time
                logger.info(f"命令执行完成, 退出码: {result.exit_status}, 耗时: {elapsed_time:.2f}秒")

                # 转换输出为字符串类型
                stdout_str = str(result.stdout) if result.stdout is not None else ""
                stderr_str = str(result.stderr) if result.stderr is not None else ""
                exit_status_int = int(result.exit_status) if result.exit_status is not None else 0

                if stdout_str:
                    logger.info(f"命令stdout输出: {stdout_str}")
                if stderr_str:
                    logger.warning(f"命令stderr输出: {stderr_str}")

                return stdout_str, stderr_str, exit_status_int

            except asyncio.TimeoutError:
                last_error = f"命令执行超时（90秒）"
                logger.warning(f"{last_error}，命令: {command}")
                retry_count += 1
                if retry_count <= max_retries:
                    logger.info(f"准备重试...")
                    await asyncio.sleep(1)  # 重试前等待1秒
                continue

            except Exception as e:
                last_error = str(e)
                logger.error(f"命令执行异常: {e}")
                if retry_count < max_retries:
                    retry_count += 1
                    logger.info(f"准备重试...")
                    await asyncio.sleep(1)
                    continue
                else:
                    raise NASCommandError(f"命令执行失败: {e}")

        # 所有重试都失败
        raise NASCommandError(f"命令执行失败，已重试 {max_retries} 次: {last_error}")

    async def close(self):
        """关闭SSH连接"""
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()
            logger.info("SSH连接已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()


# 全局NAS客户端实例
nas_client = NASClient()


async def check_user_exists(username: str) -> bool:
    """
    检查用户是否存在
    
    Args:
        username: 用户名
        
    Returns:
        bool: 用户是否存在
    """
    # synouser --get username
    # 如果用户存在，返回信息；如果不存在，通常会报错或返回特定信息
    cmd = f"/usr/syno/sbin/synouser --get {username}"
    # 这里不需要 sudo，普通权限通常也可以查询，或者使用 sudo 保险
    stdout, stderr, exit_code = await nas_client.execute_command(cmd, use_sudo=True)
    
    if exit_code == 0:
        return True
    return False


async def get_user_info(username: str) -> dict:
    """
    获取用户信息
    
    Args:
        username: 用户名
        
    Returns:
        dict: 包含 fullname, email, expired 等信息的字典
    """
    cmd = f"/usr/syno/sbin/synouser --get {username}"
    stdout, stderr, exit_code = await nas_client.execute_command(cmd, use_sudo=True)
    
    if exit_code != 0:
        raise NASCommandError(f"获取用户信息失败: {stderr}")

    # 解析输出
    info = {}
    for line in stdout.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key == "User gecos": # Full Name
                # 移除 [ ]
                if value.startswith('[') and value.endswith(']'):
                    info['fullname'] = value[1:-1]
            elif key == "User email":
                if value.startswith('[') and value.endswith(']'):
                    info['email'] = value[1:-1]
            elif key == "User expire":
                # [0] or [1]
                if value.startswith('[') and value.endswith(']'):
                    # 只有当内容是数字时才转换
                    val_content = value[1:-1]
                    if val_content.isdigit():
                        info['expired'] = int(val_content)
    
    return info


async def create_user(username: str, password: str, groups: list,fullname:str=None,mail:str=None) -> dict:
    """
    创建用户并分配用户组
    
    Args:
        username: 用户名
        password: 密码
        groups: 用户组列表
    
    Returns:
        操作结果字典
    """
    logger.info(f"开始创建用户: {username}, 用户组: {groups}")
    
    # 1. 检查用户是否已存在
    if await check_user_exists(username):
        logger.info(f"用户 {username} 已存在，跳过创建步骤，直接更新用户组")
        # 即使跳过创建，也继续执行后面的用户组分配逻辑，确保用户组配置正确
    else:
        # 使用Synology DSM命令创建用户（使用完整路径）
        # synouser --add <username> <password> "<fullname>" <expired> <mail> <privilege>
        # 注意：参数中的空格和特殊字符需要正确转义
        fullname = fullname or username.replace('"', '\\"')
        mail = mail or f"{username}@{settings.mail_domain}"
        
        # 使用单引号包裹密码，并转义密码中的单引号
        password_escaped = password.replace("'", "'\\''")
        
        # synouser --add [username pwd "full name" expired{0|1} mail privilege]
        # 传递 0 作为 privilege
        cmd = f"/usr/syno/sbin/synouser --add {username} '{password_escaped}' \"{fullname}\" 0 \"{mail}\" 0"
        logger.info(f"执行命令: {cmd}")
        stdout, stderr, exit_code = await nas_client.execute_command(cmd, use_sudo=True)
    
        if exit_code != 0:
            if "0x1C00" in stderr or "0x1c00" in stderr:
                logger.error(f"创建用户失败: 密码强度不足 {stderr}")
                raise NASWeakPasswordError(f"创建用户失败: 密码强度不足，请使用包含大小写字母、数字和符号的复杂密码 (synoerr=[0x1C00])")
            logger.error(f"创建用户失败: {stderr}")
            raise NASCommandError(f"创建用户失败: {stderr}")

    # 分配用户组
    for group in groups:
        # 修正：synogroup 命令应该是 --memberadd (注意帮助信息中是 memberadd)
        # 但根据用户提供的输出，Usage 显示的是 --memberadd，但也提示了 unrecognized option '--member_add'
        # synogroup --memberadd groupname user1 user2 ...
        # 注意：参数顺序是 groupname username
        cmd = f"/usr/syno/sbin/synogroup --memberadd {group} {username}"
        logger.info(f"执行命令: {cmd}")
        try:
            # 对 synogroup 命令启用重试（最多重试2次），提高成功率
            stdout, stderr, exit_code = await nas_client.execute_command(
                cmd,
                use_sudo=True,
                max_retries=2
            )
            if exit_code != 0:
                logger.warning(f"添加用户到组 {group} 失败: {stderr}")
            else:
                logger.info(f"成功将用户 {username} 添加到组 {group}")
        except Exception as e:
            logger.warning(f"添加用户到组 {group} 时发生异常: {e}")
            # 继续处理其他组，不中断整个流程

    logger.info(f"用户 {username} 创建成功")
    return {"success": True, "username": username, "groups": groups}


async def enable_user(username: str) -> dict:
    """
    启用用户

    Args:
        username: 用户名

    Returns:
        操作结果字典
    """
    logger.info(f"启用用户: {username}")
    
    # 1. 检查用户是否存在
    if not await check_user_exists(username):
        logger.error(f"启用用户失败: 用户 {username} 不存在")
        raise NASCommandError(f"用户 {username} 不存在")

    # 2. 获取用户现有信息以保留 fullname 和 email
    try:
        user_info = await get_user_info(username)
    except Exception as e:
        logger.warning(f"获取用户信息失败: {e}，将使用默认值")
        user_info = {}
    
    fullname = user_info.get('fullname', username)
    email = user_info.get('email', "")
    
    # 3. 使用 synouser --modify 启用用户 (expired=0)
    # 语法: synouser --modify username "full name" expired{0|1} mail
    # 注意：help信息中没有 password 参数！
    # --modify username "full name" expired{0|1} mail
    # 这意味着我们不需要密码就可以修改这些信息！太棒了！
    
    # 转义 fullname
    fullname_escaped = fullname.replace('"', '\\"')
    
    cmd = f"/usr/syno/sbin/synouser --modify {username} \"{fullname_escaped}\" 0 \"{email}\""
    stdout, stderr, exit_code = await nas_client.execute_command(cmd, use_sudo=True)

    if exit_code != 0:
        logger.error(f"启用用户失败: {stderr}")
        raise NASCommandError(f"启用用户失败: {stderr}")

    logger.info(f"用户 {username} 已启用")
    return {"success": True, "username": username, "status": "enabled"}


async def disable_user(username: str) -> dict:
    """
    禁用用户

    Args:
        username: 用户名

    Returns:
        操作结果字典
    """
    logger.info(f"禁用用户: {username}")
    
    # 1. 检查用户是否存在
    if not await check_user_exists(username):
        logger.error(f"禁用用户失败: 用户 {username} 不存在")
        raise NASCommandError(f"用户 {username} 不存在")

    # 2. 获取用户现有信息以保留 fullname 和 email
    try:
        user_info = await get_user_info(username)
    except Exception as e:
        logger.warning(f"获取用户信息失败: {e}，将使用默认值")
        user_info = {}
    
    fullname = user_info.get('fullname', username)
    email = user_info.get('email', "")

    # 3. 使用 synouser --modify 禁用用户 (expired=1)
    # 转义 fullname
    fullname_escaped = fullname.replace('"', '\\"')

    cmd = f"/usr/syno/sbin/synouser --modify {username} \"{fullname_escaped}\" 1 \"{email}\""
    stdout, stderr, exit_code = await nas_client.execute_command(cmd, use_sudo=True)

    if exit_code != 0:
        logger.error(f"禁用用户失败: {stderr}")
        raise NASCommandError(f"禁用用户失败: {stderr}")

    logger.info(f"用户 {username} 已禁用")
    return {"success": True, "username": username, "status": "disabled"}


async def read_file(file_path: str) -> dict:
    """
    读取文件内容

    Args:
        file_path: 文件路径

    Returns:
        操作结果字典
    """
    logger.info(f"读取文件: {file_path}")

    # 验证路径是否被允许
    if settings.allow_file_path:
        allowed = False
        for allowed_path in settings.allow_file_path:
            if file_path.startswith(allowed_path):
                allowed = True
                break
        if not allowed:
            logger.error(f"路径访问被拒绝: {file_path}")
            raise NASCommandError(f"路径访问被拒绝: {file_path}")

    cmd = f"cat {file_path}"
    stdout, stderr, exit_code = await nas_client.execute_command(cmd)

    if exit_code != 0:
        logger.error(f"读取文件失败: {stderr}")
        raise NASCommandError(f"读取文件失败: {stderr}")

    logger.info(f"文件读取成功: {file_path}")
    return {"success": True, "file_path": file_path, "content": stdout}


async def write_file(file_path: str, content: str) -> dict:
    """
    写入文件内容

    Args:
        file_path: 文件路径
        content: 文件内容

    Returns:
        操作结果字典
    """
    logger.info(f"写入文件: {file_path}")

    # 验证路径是否被允许
    if settings.allow_file_path:
        allowed = False
        for allowed_path in settings.allow_file_path:
            if file_path.startswith(allowed_path):
                allowed = True
                break
        if not allowed:
            logger.error(f"路径访问被拒绝: {file_path}")
            raise NASCommandError(f"路径访问被拒绝: {file_path}")

    # 使用echo命令写入文件（需要注意特殊字符）
    # 使用printf来更好地处理特殊字符
    cmd = f"printf '%s' '{content}' > {file_path}"
    stdout, stderr, exit_code = await nas_client.execute_command(cmd)

    if exit_code != 0:
        logger.error(f"写入文件失败: {stderr}")
        raise NASCommandError(f"写入文件失败: {stderr}")

    logger.info(f"文件写入成功: {file_path}")
    return {"success": True, "file_path": file_path}
