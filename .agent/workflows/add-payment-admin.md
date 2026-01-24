---
description: How to manually add a payment as an administrator
---

# Admin Guide: Manually Adding a Payment

Follow these steps to manually record a payment received from a borrower (e.g., via bank transfer or cash) and ensure it is correctly applied to their loan.

### 1. Access the Admin Portal

- Open your browser and go to your site's `/admin/` URL.
- Log in with your **Admin** or **Staff** credentials.

### 2. Create the Payment Record

1. Navigate to the **PAYMENTS** section and click on **Payments**.
2. Click the **[+] Add payment** button in the top right corner.
3. Fill in the following fields:
   - **Idempotency key**: Enter a unique reference (e.g., `bank-transfer-2024-01-23-001`).
   - **User**: Select the borrower's name.
   - **Loan**: Select the specific loan this payment belongs to.
   - **Amount**: Enter the exact amount received (e.g., `500.00`).
   - **Payment method**: Select **Bank Transfer** or **Internal Wallet**.
   - **Status**: Set this to **Pending** initially.
4. Click **Save and continue editing**.

### 3. Finalize and Allocate Funds

Once the payment is saved and you have confirmed the funds are in the system:

1. Change the **Status** to **Completed**.
2. Click **Save and continue editing**.
3. Look for the **PROCESS ALLOCATION** button in the top right of the page (near the History button).
4. Click **Process Allocation**.

### 4. Verify the Results

- **Installment Updates**: Scroll down to the **Repayment Allocations** section at the bottom of the page. You should see new entries showing exactly how much was applied to Penalty, Interest, and Principal.
- **Audit Trail**: Check the **Payment Audit Logs** section to see a record of the "ALLOCATED" event.
- **Loan Balance**: You can navigate to the **Loans** section to verify that the loan status or remaining principal has been updated accordingly.

> [!IMPORTANT]
> Once a payment status is set to **Completed**, you will no longer be able to edit its financial details. This ensures the integrity of the ledger.
