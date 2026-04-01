from pydantic import BaseModel, Field


class SSOLoginUrlResponse(BaseModel):
    authorize_url: str = Field(..., description="Casdoor 登录跳转地址")
    state: str = Field(..., description="后端签名的状态值")


class SSOExchangeRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Casdoor 授权码")
    state: str = Field(..., min_length=1, description="后端签名的状态值")


class SSOExchangeResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    redirect_to: str = "/books"
    is_new_user: bool = False
