from django.test import TestCase
from decimal import Decimal
from datetime import date
from .services import LoanCalculator

class LoanCalculatorTests(TestCase):
    def test_flat_interest_calculation(self):
        # $1000, 12%, 12 months = $120 interest
        principal = 1000
        rate = 12
        term = 12
        interest = LoanCalculator.calculate_flat_interest(principal, rate, term)
        self.assertEqual(interest, Decimal('120.00'))

    def test_reducing_emi_calculation(self):
        # $1000, 12%, 12 months EMI approx $88.85
        principal = 1000
        rate = 12
        term = 12
        emi = LoanCalculator.calculate_reducing_emi(principal, rate, term)
        self.assertEqual(emi, Decimal('88.85'))

    def test_penalty_calculation(self):
        # $100 overdue, 10% rate, 30 days late, $5 flat fee
        amount = 100
        rate = 10
        days = 30
        flat = 5
        # 100 * 0.1 * 30/365 = 0.8219... -> 0.82
        # Total = 0.82 + 5 = 5.82
        penalty = LoanCalculator.calculate_penalty(amount, rate, days, flat)
        self.assertEqual(penalty, Decimal('5.82'))

    def test_early_repayment(self):
        principal = 500
        fee_rate = 2
        # 500 + 2% of 500 (10) = 510
        total = LoanCalculator.calculate_early_repayment(principal, fee_rate)
        self.assertEqual(total, Decimal('510.00'))

class IntegrationTests(TestCase):
    def test_grace_period_flat_schedule(self):
        # Mock loan with grace period
        from unittest.mock import MagicMock
        loan = MagicMock()
        loan.principal = Decimal('1000.00')
        loan.interest_rate = Decimal('12.00')
        loan.term = 12
        loan.grace_period = 3
        loan.disbursement_date.date.return_value = date(2024, 1, 1)
        
        from .services import ScheduleGenerator
        schedule = ScheduleGenerator.generate_flat_schedule(loan)
        
        # First 3 should have 0 principal
        self.assertEqual(schedule[0]['principal'], Decimal('0.00'))
        self.assertEqual(schedule[1]['principal'], Decimal('0.00'))
        self.assertEqual(schedule[2]['principal'], Decimal('0.00'))
        # 4th should start principal
        self.assertGreater(schedule[3]['principal'], Decimal('0.00'))
        # Total principal should be 1000
        self.assertEqual(sum(s['principal'] for s in schedule), Decimal('1000.00'))
