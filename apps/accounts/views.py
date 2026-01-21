from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template.loader import render_to_string

User = get_user_model()


from .services.auth_service import AuthService

@require_http_methods(["GET", "POST"])
def register(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			# Role mapping: borrower -> BORROWER, lender -> LOAN_OFFICER
			raw_role = request.POST.get('role', 'borrower')
			role_mapping = {
				'borrower': User.Role.BORROWER,
				'lender': User.Role.LOAN_OFFICER,
				'officer': User.Role.LOAN_OFFICER,
				'admin': User.Role.ADMIN,
			}
			role = role_mapping.get(raw_role, User.Role.BORROWER)
			
			# Use AuthService
			AuthService.register_user(
				request=request,
				form=form,
				role=role,
				email=request.POST.get('email', '')
			)
			return redirect('login_router')
	else:
		form = UserCreationForm()

	# support HTMX partial rendering
	if request.headers.get('Hx-Request'):
		html = render_to_string('registration/_register_form.html', {'form': form}, request=request)
		return HttpResponse(html)

	return render(request, 'registration/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def htmx_login_fragment(request):
	form = AuthenticationForm(request=request, data=request.POST or None)
	if request.method == 'POST' and form.is_valid():
		login(request, form.get_user())
		return HttpResponse("<div hx-trigger=\"refresh\"></div>")
	html = render_to_string('registration/_login_form.html', {'form': form}, request=request)
	return HttpResponse(html)

# Create your views here.
