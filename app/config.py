from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openai_api_key: str = "placeholder"
    primo_api_key: str
    primo_api_host: str
    primo_api_limit: str
    max_results_to_llm: int
    ai_platform: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_default_region: str
    aws_bedrock_model_id: str
    llm_do_response_formatting: str
    libcal_refresh_time: int = 86400
    libcal_client_id: int
    libcal_client_secret: str
    libcal_token_api_route: str
    libcal_hours_api_route: str

    model_config = SettingsConfigDict(env_file = '.env')

settings = Settings()

