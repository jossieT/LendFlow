from django.db import models

class AuditEventType(models.TextChoices):
    # Loan Events
    LOAN_APPLICATION_SUBMITTED = 'LOAN.SUBMITTED', 'Loan Application Submitted'
    LOAN_APPROVED = 'LOAN.APPROVED', 'Loan Approved'
    LOAN_REJECTED = 'LOAN.REJECTED', 'Loan Rejected'
    LOAN_DISBURSED = 'LOAN.DISBURSED', 'Loan Disbursed'
    
    # Payment Events
    PAYMENT_INITIATED = 'PAYMENT.INITIATED', 'Payment Initiated'
    PAYMENT_COMPLETED = 'PAYMENT.COMPLETED', 'Payment Completed'
    PAYMENT_FAILED = 'PAYMENT.FAILED', 'Payment Failed'
    PAYMENT_ALLOCATED = 'PAYMENT.ALLOCATED', 'Payment Allocated'
    ALLOCATION_FAILED = 'PAYMENT.ALLOCATION_FAILED', 'Allocation Failed'
    
    # Admin Events
    ADMIN_MANUAL_ALLOCATION = 'ADMIN.MANUAL_ALLOCATION', 'Manual Allocation Triggered'
    ADMIN_STATUS_OVERRIDE = 'ADMIN.STATUS_OVERRIDE', 'Status Manually Overridden'
    ADMIN_LOAN_WRITE_OFF = 'ADMIN.LOAN_WRITE_OFF', 'Loan Written Off'
    ADMIN_BALANCE_ADJUSTMENT = 'ADMIN.BALANCE_ADJUSTMENT', 'Manual Balance Adjustment'
    
    # Compliance Events
    COMPLIANCE_RISK_EVALUATION = 'COMPLIANCE.RISK_EVALUATION', 'Compliance Risk Evaluation'
    USER_BLACKLISTED = 'COMPLIANCE.USER_BLACKLISTED', 'User Blacklisted'
    USER_WHITELISTED = 'COMPLIANCE.USER_WHITELISTED', 'User Whitelisted'
    COMPLIANCE_REPORT_GENERATED = 'COMPLIANCE.REPORT_GENERATED', 'Compliance Report Generated'
