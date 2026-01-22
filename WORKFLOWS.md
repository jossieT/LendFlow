# LendFlow Project Workflows

This document lists the available operational workflows for the LendFlow system. Each workflow is documented in detail in the `.agent/workflows/` directory.

## Available Workflows

### 1. [Editing Loan Status](.agent/workflows/edit-loan-status.md)

**Command**: `/edit-loan-status`
**Description**: Explains how to transition loan applications and loans between statuses using the Admin portal, API, or Dashboard.

### 2. [Repaying a Loan](.agent/workflows/repay-loan.md)

**Command**: `/repay-loan`
**Description**: Outlines the process for initiating payments, handling webhooks, and manually adjusting repayment allocations.

## Implementation Standards

All workflows must adhere to the FOLLOWING principles:

- **Auditability**: Every change must be logged.
- **Idempotency**: Retrying a workflow step must be safe.
- **Transactionality**: Financial operations must be atomic.
