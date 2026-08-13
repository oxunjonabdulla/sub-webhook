from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.sub_webhook.database import get_db
from src.sub_webhook.models import Payment, Subscription
from src.sub_webhook.schemas import WebhookPayload

router = APIRouter(tags=["webhook"])

SUBSCRIPTION_DAYS = 30

@router.post("/webhook/payment")
async def payment_webhook(payload: WebhookPayload, db: AsyncSession = Depends(get_db)):
    # 1) IDEMPOTENCY (fast path): already processed this payment_id?
    existing = await db.scalar(
        select(Payment).where(Payment.payment_id == payload.payment_id)
    )
    if existing is not None:
        return {"status": "already_processed", "payment_id": payload.payment_id}

    # 2) Record payment + (if CONFIRMED) activate subscription — ONE transaction
    db.add(
        Payment(
            payment_id=payload.payment_id,
            user_id=payload.user_id,
            amount=payload.amount,
            status=payload.status
        )
    )

    if payload.status == "CONFIRMED":
        sub = await db.scalar(
            select(Subscription).where(Subscription.user_id == payload.user_id)
        )
        expires = datetime.now(timezone.utc) + timedelta(days=SUBSCRIPTION_DAYS)
        if sub is None:
            db.add(Subscription(
                user_id=payload.user_id, status="active", expires_at=expires
            ))
        else:
            sub.status = "active"
            sub.expires_at = expires

    # 3) ATOMICITY: single commit -> both writes land together, or neither
    try:
        await db.commit()
    except IntegrityError:
        # race: a concurrent duplicate slipped past the check; unique blocked it
        await db.rollback()
        return {"status": "already_processed", "payment_id": payload.payment_id}
    
    return {"status": "processed", "payment_id": payload.payment_id}













