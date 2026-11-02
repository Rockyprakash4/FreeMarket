from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Payment


@login_required
def payment_list_view(request):
    if request.user.role == request.user.Role.CLIENT:
        payments = Payment.objects.filter(payer=request.user).select_related(
            "order", "order__freelancer", "order__project"
        )
    else:
        payments = Payment.objects.filter(order__freelancer=request.user).select_related(
            "order", "payer", "order__project"
        )

    return render(
        request,
        "payments/payment_list.html",
        {"payments": payments},
    )
