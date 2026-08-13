from pydantic import BaseModel, Field

class WebhookPayload(BaseModel):
    payment_id: str
    user_id: int
    amount: int = Field(ge=0)
    status: str

