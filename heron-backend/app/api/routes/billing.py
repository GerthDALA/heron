from typing import Literal, Optional

import aiosqlite
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.services import billing_service, scan_service

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    plan: Literal["starter", "brand", "studio"]
    scan_id: Optional[str] = None


class CheckoutResponse(BaseModel):
    checkout_url: str


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    user: dict = Depends(get_current_user),
):
    try:
        url = billing_service.create_checkout_session(user, body.plan, body.scan_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Stripe error: {exc}")
    return CheckoutResponse(checkout_url=url)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    stripe_signature: str = Header(default="", alias="Stripe-Signature"),
    db: aiosqlite.Connection = Depends(get_db),
):
    payload = await request.body()
    event = billing_service.verify_webhook(payload, stripe_signature)
    # Stripe requires a 200 response in all cases; invalid events are logged and dropped.
    if event is None:
        return {"received": True}

    if event["type"] == "checkout.session.completed":
        scan_id = await billing_service.handle_checkout_completed(db, event)
        if scan_id:
            background_tasks.add_task(scan_service.run_full_scan, scan_id)
    elif event["type"] == "customer.subscription.deleted":
        await billing_service.handle_subscription_deleted(db, event)

    return {"received": True}
