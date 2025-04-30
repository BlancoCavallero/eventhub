import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import RefundRequestForm
from .models import Event, User, RefundRequest, Ticket


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    return render(request, "app/event_detail.html", {"event": event})


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )

@login_required #Solicitud de reembolso
def refund_request(request, ticket_code):
    ticket = get_object_or_404(Ticket, ticket_code=ticket_code)

    if request.method == "POST":
        reason = request.POST.get("reason")
        if not reason:
            return redirect("ticket_detail", ticket_code=ticket_code)

        # Crear solicitud de reembolso
        refund = RefundRequest.new(
            ticket_code=ticket.ticket_code,
            reason=reason,
            user=request.user
        )

        if refund[0]:
            return redirect("events")
        else:
            return render(request, "app/refund_request.html", {"errors": refund[1]})

    return render(request, "app/refund_request.html", {"ticket": ticket})

@login_required
def handle_refund_request(request, refund_id):
    # Verifica si el usuario es organizador
    if not request.user.is_organizer:
        return redirect("events")

    # Obtén la solicitud de reembolso
    refund_request = get_object_or_404(RefundRequest, pk=refund_id)

    if request.method == "POST":
        action = request.POST.get("action")

        # Si se acepta la solicitud de reembolso
        if action == "accept":
            refund_request.approved = True
            refund_request.approval_date = timezone.now().date()  # Marca la fecha de aprobación
            refund_request.save()


        # Si se rechaza la solicitud de reembolso
        elif action == "reject":
            refund_request.approved = False
            refund_request.approval_date = None  # Borra la fecha de aprobación
            refund_request.save()

        return redirect("refund_requests")  # Redirige a la vista que lista las solicitudes de reembolso

    return render(
        request,
        "app/handle_refund_request.html",  # Plantilla para confirmar la acción
        {"refund_request": refund_request}
    )

def is_organizer(user):
    return user.is_staff or user.is_superuser


@user_passes_test(is_organizer)
def refund_list(request):
    refunds = RefundRequest.objects.all()
    return render(request, 'refunds/refund_list.html', {'refunds': refunds})

@user_passes_test(is_organizer)
def approve_refund(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    refund.approved = True
    refund.approval_date = timezone.now()
    refund.save()
    return redirect('refund_list')

@user_passes_test(is_organizer)
def reject_refund(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    refund.approved = False
    refund.approval_date = timezone.now()
    refund.save()
    return redirect('refund_list')

@user_passes_test(is_organizer)
def delete_refund(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    refund.delete()
    return redirect('refund_list')

# --- VISTA DEL USUARIO ---

@login_required
def create_refund(request):
    if request.method == 'POST':
        form = RefundRequestForm(request.POST)
        if form.is_valid():
            refund = form.save(commit=False)
            refund.user = request.user
            refund.created_at = timezone.now()
            refund.save()
            return redirect('refund_list')  # Redirige a la lista de solicitudes de reembolso
    else:
        form = RefundRequestForm()
    return render(request, 'refunds/create_refund.html', {'form': form})

@user_passes_test(is_organizer)
def refund_update(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    approved_value = request.POST.get("approved")

    if approved_value is not None:
        refund.approved = approved_value.lower() == "true"
        refund.approval_date = timezone.now()
        refund.save()

    return redirect("refund_list")