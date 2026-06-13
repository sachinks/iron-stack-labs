# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "super-secret-fallback-key-change-in-production"  # Secret key for JWT signing
    algorithm: str = "HS256"                                           # JWT signing algorithm
    access_token_expire_mins: int = 60                                 # 1 hour
    redis_url: str = "redis://localhost:6379"                          # Redis connection URL
    rate_limit_free: int = 10                                          # 10 requests per minute for free users
    rate_limit_pro: int = 60                                           # 60 requests per minute for pro users
    rate_limit_enterprise: int = 300                                   # 300 requests per minute for enterprise users
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"

try:
    settings = Settings()
except Exception as e:
    # Safe fallback instantiation if env configs fail
    settings = Settings(_env_file=None)

TIER_LIMITS = {
    "free": settings.rate_limit_free,
    "pro": settings.rate_limit_pro,
    "enterprise": settings.rate_limit_enterprise,
}
