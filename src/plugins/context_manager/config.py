from pydantic import BaseModel, Field

class Config(BaseModel):
    default_context_length: int = Field(default=15)
