from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.timezone import localtime
from .models import Event, Notification, Ticket

@receiver(pre_save, sender=Event)
def detect_event_update(sender, instance, **kwargs):
    if not instance.pk:
        return  

    try:
        previous = Event.objects.get(pk=instance.pk)
    except Event.DoesNotExist:
        return

    changes = []
    instance._old_scheduled_at = previous.scheduled_at
    instance._old_venue = previous.venue.name if previous.venue else "N/A"

    if instance.scheduled_at != previous.scheduled_at:
        changes.append(("scheduled_at", previous.scheduled_at, instance.scheduled_at))

    if instance.venue != previous.venue:
        changes.append(("venue", previous.venue.name if previous.venue else "N/A", instance.venue.name if instance.venue else "N/A"))

    instance._detected_changes = changes if changes else None

@receiver(post_save, sender=Event)
def create_notification_on_event_update(sender, instance, created, **kwargs):
    if created:
        return  

    changes = getattr(instance, '_detected_changes', None)
    if not changes:
        return

    change_descriptions = []

    for field, old, new in changes:
        if field == "scheduled_at":
            field_label = "la fecha"
            old = localtime(old).strftime("%d/%m/%Y a las %H:%M Hs.")
            new = localtime(new).strftime("%d/%m/%Y a las %H:%M Hs.")

        elif field == "venue":
            field_label = "el lugar"

        else:
            field_label = field
        change_descriptions.append(f"{field_label} de {old} al {new}")
        
    change_text = " y ".join(change_descriptions)

    date_part = localtime(instance._old_scheduled_at).strftime("%d/%m/%Y")
    venue_part = instance._old_venue
    
    title = f"Actualización del evento {instance.title} - {date_part} - {venue_part} "
    message = f"El evento {instance.title} ha cambiado {change_text}."

    notif = Notification.objects.create(
        title=title,
        message=message,
        priority="High",
        event=instance
    )

    user_ids = Ticket.objects.filter(event=instance).values_list("user_id", flat=True).distinct()
    notif.users.set(user_ids)
    notif.save()
