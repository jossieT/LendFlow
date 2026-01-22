---
description: how to edit loan status
---

To edit the status of a loan or loan application, follow these steps:

### Via Django Admin (Recommended for Staff/Admins)

1. **Access the Admin Portal**: Navigate to `/admin/` in your browser and log in with a staff account.
2. **Locate the Record**:
   - For pending applications: Go to **Loan Applications** -> **Loan applications**.
   - For active loans: Go to **Loans** -> **Loans**.
3. **Select the Item**: Click on the specific ID or record you wish to modify.
4. **Update Status**:
   - Change the `Status` dropdown to your desired value (e.g., from `SUBMITTED` to `APPROVED`, or `ACTIVE` to `PAID`).
   - _Note: As an admin, you can now bypass standard transition rules if needed._
5. **Save**: Scroll to the bottom and click **Save**.

### Via API (For Developers)

Send a `PATCH` request to the application endpoint:

```bash
PATCH /api/loan-applications/{id}/
Content-Type: application/json
Authorization: Bearer <your_token>

{
    "status": "APPROVED"
}
```

### Via Dashboard

1. Log in as a **Loan Officer**.
2. Navigate to the **Lender Dashboard**.
3. Find the application in the **Marketplace** or **New Loan Requests** section.
4. Click the appropriate action button (e.g., **Approve** or **Disburse**).
