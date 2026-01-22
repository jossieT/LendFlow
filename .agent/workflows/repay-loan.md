---
description: how to repay a loan
---

To record or process a repayment for a loan, follow these steps:

### Via API (Standard Flow)

1. **Initiate Payment**:
   Send a `POST` request to `/api/payments/payments/` with the following payload:
   ```json
   {
       "loan": <loan_id>,
       "amount": "100.00",
       "payment_method": "STRIPE",
       "idempotency_key": "unique_string_for_this_transaction"
   }
   ```
2. **Process Webhook**:
   Once the payment is confirmed by the provider, the provider's webhook should hit:
   `POST /api/payments/webhooks/<provider>/`
   (e.g., `/api/payments/webhooks/stripe/`)

   The system will automatically allocate the funds using the Waterfall Strategy:
   **Penalty -> Interest -> Principal**.

### Via Django Admin (Manual Adjustment)

If you need to manually record a repayment or adjust a payment status:

1. **Navigate to Payments**: Go to **Payments** -> **Payments**.
2. **Update Status**:
   - Open a `PENDING` payment.
   - Change status to `COMPLETED`.
   - Click **Save**.
3. **Trigger Allocation**:
   - On the same Payment page, click the **Process Allocation** button (top right).
   - Alternatively, the `save_model` logic in Admin may trigger an audit log for the status change.

### Verification

- Check the **Repayment Allocations** inline on the Payment page to see how funds were split.
- Check the **Status History** on the Loan to see the balance reduction.
