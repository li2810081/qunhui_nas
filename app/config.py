from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # 应用配置
    app_name: str = "FastAPI Application"
    debug: bool = False

    # 认证配置
    token: str = ""
    allow_ip: str = ""

    # SSH 配置
    nas_host: str = ""
    nas_port: int = 22
    nas_user: str = ""
    nas_password: str = ""
    sudo_password: str = ""

    # 文件路径配置
    allow_file_path: str = ""

    # 邮箱域名配置
    mail_domain: str = "qunhui.com"

    # DSM API 配置（用于用户管理）
    dsm_host: str = ""
    dsm_port: str = "5001"
    dsm_https: bool = True

    # 健康检查配置
    health_check_enabled: bool = True
    health_check_timeout: int = 5  # 秒

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()