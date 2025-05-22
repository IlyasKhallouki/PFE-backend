from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "barbie"               
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    DATABASE_URL: str = "mysql://root:password@localhost:3306/chatdb"

    class Config:
        env_file = ".env"

settings = Settings()
