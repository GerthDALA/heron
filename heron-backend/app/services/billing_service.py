"""Stripe checkout session creation and webhook handling."""

import logging

import aiosqlite
import stripe

from app.config import get_settings

logger = logging.getLogger("heron.billing")

# Monthly prices in EUR cents
PLAN_PRICES = {
    "starter": 29000,
    "brand": 89000,
    "studio": 240000,
}

PLAN_LABELS = {
    "starter": "Heron Starter",
    "brand": "Heron Brand",
    "studio": "Heron Studio",
}


def create_checkout_session(user: dict, plan: str, scan_id: str | None = None) -> str:
    """Create a Stripe hosted checkout session; returns its URL."""
    settings = get_settings()
    stripe.api_key = settings.STRIPE_SECRET_KEY
    metadata = {"user_id": user["id"], "plan": plan}
    if scan_id:
        metadata["scan_id"] = scan_id

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=user["email"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "unit_amount": PLAN_PRICES[plan],
                "recurring": {"interval": "month"},
                "product_data": {"name": PLAN_LABELS[plan]},
            },
            "quantity": 1,
        }],
        metadata=metadata,
        success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
    )
    return session.url


def verify_webhook(payload: bytes, signature: str) -> dict | None:
    """Validate the Stripe signature; returns the event dict or None."""
    settings = get_settings()
    try:
        return stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        logger.warning("Invalid Stripe webhook signature: %s", exc)
        return None


async def handle_checkout_completed(db: aiosqlite.Connection, event: dict) -> str | None:
    """Upgrade the user's plan; returns the scan_id to (re)generate, if any."""
    session = event["data"]["object"]
    metadata = session.get("metadata") or {}
    user_id = metadata.get("user_id")
    plan = metadata.get("plan")
    scan_id = metadata.get("scan_id")
    if user_id and plan in PLAN_PRICES:
        await db.execute(
            "UPDATE users SET plan = ?, stripe_customer_id = ? WHERE id = ?",
            (plan, session.get("customer"), user_id),
        )
        if scan_id:
            # Claim an unowned (freemium) scan so the paying user can access
            # the full report; never reassign a scan another user owns.
            await db.execute(
                "UPDATE scans SET user_id = ?, is_freemium = 0 "
                "WHERE id = ? AND user_id IS NULL",
                (user_id, scan_id),
            )
        await db.commit()
    return scan_id


async def handle_subscription_deleted(db: aiosqlite.Connection, event: dict) -> None:
    """Downgrade the user back to 'free'."""
    subscription = event["data"]["object"]
    customer_id = subscription.get("customer")
    if customer_id:
        await db.execute(
            "UPDATE users SET plan = 'free' WHERE stripe_customer_id = ?",
            (customer_id,),
        )
        await db.commit()
