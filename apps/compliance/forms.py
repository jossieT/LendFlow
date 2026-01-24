from django import forms

class AdminActionReasonForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True,
        help_text="Provide a detailed justification for this action."
    )

class BalanceAdjustmentForm(AdminActionReasonForm):
    amount_delta = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        required=True,
        help_text="Amount to add (positive) or subtract (negative) from the user balance."
    )
