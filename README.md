# Subscription Payment Webhook

A FastAPI service that processes subscription-payment webhooks from a bank.
Stack: FastAPI, PostgreSQL, SQLAlchemy (async), Alembic.

## Requirements

- Docker + Docker Compose
- Python 3.12
- [uv](https://docs.astral.sh/uv/) for dependency management

## Running

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Install dependencies
uv sync

# 3. Apply database migrations
uv run alembic upgrade head

# 4. Run the app
uv run uvicorn sub_webhook.main:app --reload
```

The API is then available at http://127.0.0.1:8000 (interactive docs at `/docs`).

> Note: if port 8000 is taken, run with `--port 8001`.

## Testing the webhook

```bash
# First call - processes the payment and activates the subscription
curl -X POST http://127.0.0.1:8000/webhook/payment \
  -H "Content-Type: application/json" \
  -d '{"payment_id": "abc-123", "user_id": 1, "amount": 4900, "status": "CONFIRMED"}'
# -> {"status": "processed", ...}

# Same call again (duplicate) - no double charge, no re-activation
curl -X POST http://127.0.0.1:8000/webhook/payment \
  -H "Content-Type: application/json" \
  -d '{"payment_id": "abc-123", "user_id": 1, "amount": 4900, "status": "CONFIRMED"}'
# -> {"status": "already_processed", ...}
```

(Requires a user with the given `user_id` to exist first.)

## query.sql

`query.sql` contains the standalone query for requirement 4: users with an
active subscription who have had no `meetings_attendance` records in the last
30 days. It assumes the `meetings_attendance (user_id, date)` table exists.

## Design decisions

- **Idempotency (requirement 2):** enforced at two layers. A `UNIQUE`
  constraint on `payments.payment_id` is the real guarantee — the database
  refuses a duplicate even if two identical webhooks arrive simultaneously.
  A fast-path `SELECT` handles the common case (a retry after the first
  webhook committed) and returns `already_processed` without hitting the
  constraint. The `IntegrityError` is caught as a backstop for the race case.

- **Atomicity (requirement 3):** the payment insert and the subscription
  activation are two separate writes that share one transaction and one
  `commit()`. The database can only end up in the "before" state or the
  "after" state — never "payment saved but no subscription." If the process
  crashes before commit, everything rolls back.

- **Duplicates return HTTP 200 (`already_processed`), not an error**, so the
  bank treats the payment as handled and stops retrying.

- **`amount` stored as an integer (minor units)**, like Stripe, to avoid
  floating-point rounding errors on money.

- **One subscription per user** (`UNIQUE(user_id)`), making activation a clean
  update-or-create.

- **Database URL comes from settings/environment**, not hardcoded in
  `alembic.ini`, keeping credentials out of source control.

## Assumptions

- The user already exists before a payment webhook arrives (the webhook does
  not create users).
- Duplicate webhooks are identical resends of the same `payment_id`, as stated
  in the task.
- "Active subscription" in query.sql means `status = 'active'` AND not expired.

## Time spent

~[FILL IN] hours, including learning async SQLAlchemy/Alembic properly.