"""开饭后端配置"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从 .env 读环境变量"""

    # ===== MiniMax API =====
    MiniMax_API_KEY: str
    MiniMax_BASE_URL: str = "https://api.minimaxi.com/v1"
    # 文本模型：统一用 MiniMax-M3（在 llm_client 对所有调用统一加 thinking 关闭）
    #   · M2.x 的 thinking 无法关闭（官方限制），每轮先输出一大段推理再作答，实测拖慢 ~5-10×
    #   · M3 支持 thinking disabled：同任务 9~12s → 1~4s，且输出干净（快 6-8 倍）
    MiniMax_TEXT_MODEL_MAIN: str = "MiniMax-M3"
    MiniMax_TEXT_MODEL_TUTORIAL: str = "MiniMax-M3"
    # 图像生成：已改用 DashScope z-image-turbo（见下方 DASHSCOPE 配置）
    # MiniMax image-01 生图已停用（2026-08-30），字段保留备查，代码注释在 image_gen.py
    # MiniMax_IMAGE_MODEL: str = "image-01"

    # ===== HTTP 服务 =====
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"
    MAX_REQUEST_BYTES: int = 20 * 1024 * 1024  # 20MB

    # ===== 阿里云百炼 DashScope（Z-Image-Turbo 主通道） =====
    # 菜品配图主通道（2026-08-30 起 MiniMax image-01 停用）。
    # 留空表示不启用生图 → 前端直接用占位图。
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ===== 生图 Mock（测试/演示用） =====
    # true 时 generate_dish_image 直接返回假 URL，不调真实 z-image-turbo API
    MOCK_IMAGE_GEN: bool = False

    # ===== JWT =====
    # JWT 签名密钥。若为空，main.py 启动时会自动生成并写入 .env（仅首次）。
    JWT_SECRET: str = ""
    JWT_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
