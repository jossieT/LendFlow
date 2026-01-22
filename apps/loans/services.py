from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class LoanCalculator:
    @staticmethod
    def calculate_flat_interest(principal, annual_rate, term_months):
        """
        I = P * r * t
        """
        principal = Decimal(str(principal))
        annual_rate = Decimal(str(annual_rate))
        
        monthly_rate = annual_rate / Decimal('100') / Decimal('12')
        total_interest = principal * monthly_rate * Decimal(str(term_months))
        
        return total_interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_reducing_emi(principal, annual_rate, term_months):
        """
        EMI = [P x r x (1+r)^n] / [(1+r)^n - 1]
        """
        P = Decimal(str(principal))
        r = Decimal(str(annual_rate)) / Decimal('1200') # Monthly rate
        n = term_months
        
        if r == 0:
            return (P / Decimal(str(n))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        emi = (P * r * (1 + r)**n) / ((1 + r)**n - 1)
        return emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_penalty(overdue_amount, penalty_rate, days_late, flat_fee=0):
        """
        Penalty = Overdue * (rate/100) * (days/365) + flat_fee
        """
        overdue_amount = Decimal(str(overdue_amount))
        penalty_rate = Decimal(str(penalty_rate))
        days_late = Decimal(str(days_late))
        flat_fee = Decimal(str(flat_fee))

        if overdue_amount <= 0:
            return Decimal('0.00')

        penalty = (overdue_amount * (penalty_rate / Decimal('100')) * (days_late / Decimal('365'))) + flat_fee
        return penalty.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_early_repayment(remaining_principal, penalty_rate=0):
        """
        Total to close = remaining_principal + (penalty_rate/100 * remaining_principal)
        """
        remaining_principal = Decimal(str(remaining_principal))
        penalty_rate = Decimal(str(penalty_rate))
        
        fee = (remaining_principal * (penalty_rate / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return remaining_principal + fee

class ScheduleGenerator:
    @staticmethod
    def generate_flat_schedule(loan):
        principal = loan.principal
        term = loan.term
        grace_period = loan.grace_period
        
        total_interest = LoanCalculator.calculate_flat_interest(principal, loan.interest_rate, term)
        monthly_interest = (total_interest / Decimal(str(term))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # In flat interest, we usually just delay the principal
        repayment_term = term - grace_period
        monthly_principal = (principal / Decimal(str(repayment_term))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if repayment_term > 0 else Decimal('0.00')
        
        start_date = loan.disbursement_date.date()
        installments = []
        
        for i in range(1, term + 1):
            due_date = start_date + relativedelta(months=i)
            
            p_comp = Decimal('0.00')
            i_comp = monthly_interest
            
            if i > grace_period:
                p_comp = monthly_principal
                # Adjust last installment
                if i == term:
                    p_comp = principal - sum(inst['principal'] for inst in installments)
                    i_comp = total_interest - sum(inst['interest'] for inst in installments)

            installments.append({
                'due_date': due_date,
                'principal': p_comp,
                'interest': i_comp
            })
            
        return installments

    @staticmethod
    def generate_reducing_schedule(loan):
        principal = loan.principal
        rate = loan.interest_rate
        term = loan.term
        grace_period = loan.grace_period
        
        monthly_rate = Decimal(str(rate)) / Decimal('1200')
        repayment_term = term - grace_period
        emi = LoanCalculator.calculate_reducing_emi(principal, rate, repayment_term) if repayment_term > 0 else Decimal('0.00')
        
        remaining_balance = principal
        start_date = loan.disbursement_date.date()
        installments = []
        
        for i in range(1, term + 1):
            due_date = start_date + relativedelta(months=i)
            
            interest_component = (remaining_balance * monthly_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            principal_component = Decimal('0.00')
            
            if i > grace_period:
                if i == term:
                    principal_component = remaining_balance
                else:
                    principal_component = emi - interest_component
                    remaining_balance -= principal_component

            installments.append({
                'due_date': due_date,
                'principal': principal_component,
                'interest': interest_component
            })
            
        return installments
