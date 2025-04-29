import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta
from .models import Event, User, Ticket, Comment
from .forms import TicketForm
from django.db.models import Count


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
    events = Event.objects.all().order_by("scheduled_at") # Los eventos
    events_with_comments = Event.objects.annotate(num_comment=Count('comment')).order_by('scheduled_at') # Los eventos pero con conteo de comentarios

    return render(
    request,
    "app/events.html",
    {
        "events": events,
        "events_with_comments": events_with_comments,
        "user_is_organizer": request.user.is_organizer,
    },
)


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, id=id)
    comments = event.comment.all()  # related_name='comment'

    if request.method == 'POST':
        tittle = request.POST.get('tittle')
        text = request.POST.get('text')
        Comment.objects.create(
            tittle=tittle,
            text=text,
            user=request.user,
            event=event,
            created_date=timezone.now()
        )
        return redirect('event_detail', id=event.id)

    return render(request, 'app/event_detail.html', {
        'event': event,
        'comments': Comment.objects.filter(event=event).order_by("-created_date"),
        'num_comments': comments.count()
    })



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


#Listado de todos los tickets del user
@login_required
def ticket_list(request):
    print(request.user)
    tickets = Ticket.objects.filter(user=request.user)
    print(tickets) 
    if not tickets:
        messages.info(request, "No tienes tickets registrados.")  
    return render(request, "app/ticket_list.html", {"tickets": tickets})


#Alta Ticket
@login_required
def ticket_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.event = event
            ticket.save()
            messages.success(request, "Ticket creado exitosamente.")
            return redirect("ticket_list")
    else:
        form = TicketForm()

    return render(request, "app/ticket_form.html", {"form": form, "event": event})


#Editar Ticket (solo si es dueño)
@login_required
def ticket_update(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Solo el dueño puede editar su ticket
    if ticket.user != request.user:
        messages.error(request, "No tienes permisos para editar este ticket.")
        return redirect("ticket_list")

    if request.method == "POST":
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, "Ticket actualizado exitosamente.")
            return redirect("ticket_list")
    else:
        form = TicketForm(instance=ticket)

    return render(request, "app/ticket_form.html", {"form": form})


# Eliminar Ticket
@login_required
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Caso 1: Usuario regular puede eliminar su propio ticket
    if ticket.user == request.user:
        ticket.delete()
        messages.success(request, "Ticket eliminado exitosamente.")
    # Caso 2: Organizador puede eliminar tickets de sus eventos
    elif request.user.is_organizer and ticket.event.organizer == request.user:
        ticket.delete()
        messages.success(request, "Ticket eliminado exitosamente.")
    else:
        messages.error(request, "No tienes permisos para eliminar este ticket.")

    return redirect("ticket_list")
