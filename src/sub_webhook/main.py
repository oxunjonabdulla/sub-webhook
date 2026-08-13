from fastapi import FastAPI

from src.sub_webhook.routers import webhook

app = FastAPI(title="Subscription Webhook")
app.include_router(webhook.router)