from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.contrib.auth import get_user_model


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
        
class RefundRequest(models.Model):
    approved = models.BooleanField(default=False)
    approval_date = models.DateField(null=True, blank=True)
    ticket_code = models.CharField(max_length=50)
    reason = models.TextField   
    created_at = models.DateField(auto_now_add=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="RefundRequest")

    def __str__(self):
        return f"{self.ticket_code} - {self.user.username}"
    
    @classmethod
    def validate(cls, ticket_code, reason):
        errors = {}

        if not ticket_code:
            errors["ticket_code"] = "El código de ticket no puede estar vacío."

        if not reason:
            errors["reason"] = "El motivo no puede estar vacío."

        return errors

    @classmethod
    def new(cls, ticket_code, reason, user, approved=False, approval_date=None, created_at=None):
        errors = cls.validate(ticket_code, reason)

        if errors:
            return False, errors

        refund = cls(
            ticket_code=ticket_code,
            reason=reason,
            user=user,
            approved=approved,
            approval_date=approval_date,
            created_at=created_at
        )
        refund.save()
        return True, refund

    @classmethod
    def update(cls, refund_id, ticket_code, reason, approved, approval_date):
        try:
            refund = cls.objects.get(id=refund_id)

            errors = cls.validate(ticket_code, reason)
            if errors:
                return False, errors

            refund.ticket_code = ticket_code
            refund.reason = reason
            refund.approved = approved
            refund.approval_date = approval_date
            refund.save()

            return True, refund

        except cls.DoesNotExist:
            return False, "Solicitud de reembolso no encontrada."

    @classmethod
    def delete_id(cls, refund_id):
        try:
            refund = cls.objects.get(id=refund_id)
            refund.delete()
            return True, "Solicitud de reembolso eliminada correctamente."

        except cls.DoesNotExist:
            return False, "Solicitud de reembolso no encontrada."