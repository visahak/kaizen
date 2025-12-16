from pydantic_settings import BaseSettings, SettingsConfigDict

class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='KAIZEN_')
    tips_model: str = "openai/gpt-4o"
    conflict_resolution_model: str = "openai/gpt-4o"

# to reload settings call llm_settings.__init__()
llm_settings = LLMSettings()