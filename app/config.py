"""
配置管理模块
从环境变量加载应用程序配置
"""
import os
import logging
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """应用程序配置类"""

    # 允许的TOKEN列表
    token: List[str] = Field(default_factory=list)

    # 允许访问的IP列表
    allow_ip: List[str] = Field(default_factory=list)

    # 允许访问的文件路径列表
    allow_file_path: List[str] = Field(default_factory=list)

    # SSH密码
    nas_password: str = Field(default="")

    # NAS主机地址
    nas_host: str = Field(default="")

    # SSH用户名
    nas_user: str = Field(default="root")

    # SSH端口
    nas_port: int = Field(default=22)

    # Sudo密码（与SSH密码相同）
    sudo_password: str = Field(default="")

    # 默认邮箱域名
    mail_domain: str = Field(default="username.qunhui.com")

    @classmethod
    def load_from_env(cls) -> "Settings":
        """
        从环境变量加载配置
        """
        logger.info("正在加载环境变量配置...")
        load_dotenv()

        # 解析TOKEN列表
        token_str = os.getenv("TOKEN", "")
        tokens = [t.strip() for t in token_str.split(",") if t.strip()] if token_str else []

        # 解析允许的IP列表
        allow_ip_str = os.getenv("ALLOW_IP", "")
        allow_ips = [ip.strip() for ip in allow_ip_str.split(",") if ip.strip()] if allow_ip_str else []

        # 解析允许的文件路径列表
        allow_path_str = os.getenv("ALLOW_FILE_PATH", "")
        allow_paths = [p.strip() for p in allow_path_str.split(",") if p.strip()] if allow_path_str else []

        # 创建设置对象
        settings = cls(
            token=tokens,
            allow_ip=allow_ips,
            allow_file_path=allow_paths,
            nas_password=os.getenv("NAS_PASSWORD", ""),
            nas_host=os.getenv("NAS_HOST", ""),
            nas_user=os.getenv("NAS_USER", "root"),
            nas_port=int(os.getenv("NAS_PORT", "22")),
            sudo_password=os.getenv("SUDO_PASSWORD", os.getenv("NAS_PASSWORD", "")),
            mail_domain=os.getenv("MAIL_DOMAIN", "username.qunhui.com"),
        )

        logger.info(f"配置加载完成 - TOKEN数量: {len(tokens)}, 允许IP数量: {len(allow_ips)}, "
                   f"允许路径数量: {len(allow_paths)}, NAS主机: {settings.nas_host}, "
                   f"默认邮箱域名: {settings.mail_domain}")

        return settings


# 全局配置实例
settings = Settings.load_from_env()
