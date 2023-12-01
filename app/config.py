from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openai_api_key: str
    primo_api_key: str
    primo_api_host: str
    primo_api_limit: str
    max_results_to_llm: int
    ai_platform: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_default_region: str
    aws_bedrock_model_id: str

    model_config = SettingsConfigDict(env_file = '.env')

settings = Settings()

