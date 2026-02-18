from pydantic import BaseModel, Field

class Config(BaseModel):
    llm_api_key: str = Field(default="")
    llm_base_url: str = Field(default="https://api-inference.modelscope.cn/v1/")
    llm_model_name: str = Field(default="moonshotai/Kimi-K2.5")
    default_context_length: int = Field(default=15)
