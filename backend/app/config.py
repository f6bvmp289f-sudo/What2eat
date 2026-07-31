"""开饭后端配置"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从 .env 读环境变量"""

    # ===== MiniMax API =====
    MiniMax_API_KEY: str
    MiniMax_BASE_URL: str = "https://api.minimaxi.com/v1"
    # 文本模型：分两个用途
    #   - 方案生成（输出结构化 JSON 菜谱）：M2.5 足够，更快
    #   - 教程生成（详细步骤，文本质量要求高）：M2.7 更好
    MiniMax_TEXT_MODEL_MAIN: str = "MiniMax-M2.5-highspeed"
    MiniMax_TEXT_MODEL_TUTORIAL: str = "MiniMax-M2.7-highspeed"
    # 图像生成模型（image-01 真实摄影风格；image-01-live 更快但卡通风格）
    MiniMax_IMAGE_MODEL: str = "image-01"

    # ===== HTTP 服务 =====
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"
    MAX_REQUEST_BYTES: int = 20 * 1024 * 1024  # 20MB

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
