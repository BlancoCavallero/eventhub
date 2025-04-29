from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    is_organizer = models.BooleanField(default=False)

    @classmethod
    def validate_new_user(cls, email, username, password, password_confirm):
        errors = {}

        if email is None:
            errors["email"] = "El email es requerido"
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Ya existe un usuario con este email"

        if username is None:
            errors["username"] = "El username es requerido"
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Ya existe un usuario con este nombre de usuario"

        if password is None or password_confirm is None:
            errors["password"] = "Las contraseñas son requeridas"
        elif password != password_confirm:
            errors["password"] = "Las contraseñas no coinciden"

        return errors


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
        )

        return True, None

    def update(self, title, description, scheduled_at, organizer):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer

        self.save()

class Ticket(models.Model):

    TICKET_TYPES = [
        ("GENERAL", "GENERAL"),
        ("VIP", "VIP"),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="tickets")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    buy_date = models.DateTimeField(auto_now_add=True)
    ticket_code = models.UUIDField(default=uuid.uuid4, editable =False, unique=True)
    quantity= models.PositiveIntegerField()
    type = models.CharField(max_length=10, choices=TICKET_TYPES)

    def __str__(self):
        return f"Ticket {self.ticket_code}: {self.user} ({self.type}), Event: {self.event.title}, Quantity: {self.quantity}, Bought on: {self.buy_date}"

class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)
    priority = models.CharField(max_length=6,choices=[("High","High"),("Medium","Medium"),("Low","Low")])
    is_read = models.BooleanField(default=False)
    users = models.ManyToManyField(User, related_name= "notificaciones")

    def __str__(self):
        return self.title
    
    @classmethod
    def validate(cls,title,message, priority):
        errors = {}

        if not title:
            errors["title"] = "El título no puede estar vacío."
        
        if not message:
            errors["message"] = "El mensaje no puede estar vacío."

        if priority not in ["High","Medium","Low"]:
            errors["priority"] = "La prioridad debe ser High, Medium o Low"

        return errors
    
    @classmethod    
    def new(cls, title, message, priority, users):
        errors = cls.validate(title, message,priority)

        if errors:
            return False, errors

        notif = cls(title=title, message=message, priority=priority)
        notif.save()

        if users:
            notif.users.set(users)

        return True, notif

    @classmethod
    def update(cls, notif_id, title, message, priority, users):

        try:
            notif = cls.objects.get(id=notif_id)

            errors = cls.validate(title, message,priority)

            if errors:  
                return False, errors  

            notif.title = title
            notif.message = message
            notif.priority = priority
            notif.save() 

            if users:
                notif.users.set(users) 

            return True, notif

        except cls.DoesNotExist:
            return False, "Notificación no encontrada."
        
    @classmethod
    def delete_id(cls,notif_id):

        try:
            notif = cls.objects.get(id = notif_id )
            notif.delete()
            return True, "Notificacion eliminada"
        
        except cls.DoesNotExist:
            return False, "Notificacion no encontrada"

class Comment(models.Model):
    tittle = models.CharField(max_length=255)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment',
        null=True
    )

    event = models.ForeignKey(
        'app.Event',
        on_delete=models.CASCADE,
        related_name='comment',
        null=True
    )

    def __str__(self):
        return f"{self.tittle} - {self.user}"
