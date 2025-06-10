from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Event, FavoriteEvent
from django.utils import timezone

User = get_user_model()

class FavouriteE2ETest(TestCase):

    def setUp(self):
        # Crear usuarios
        self.user = User.objects.create_user(username='prueba', password='12345678')
        self.organizer = User.objects.create_user(username='organizador', password='87654321', is_organizer=True)

        # Crear evento
        self.event = Event.objects.create(
            title='Evento de prueba',
            description='Descripción del evento',
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            organizer=self.organizer,
            status='active',
            venue=None,
        )

        # Login del usuario de prueba
        self.client.login(username='prueba', password='12345678')

    def test_marcar_y_desmarcar_favorito(self):
        url_toggle_fav = reverse('toggle_favorite', kwargs={'event_id': self.event.id})
        # Ajustá 'favorite_toggle' y kwargs según tu configuración de urls

        # Al principio no hay favorito
        self.assertFalse(FavoriteEvent.objects.filter(user=self.user, event=self.event).exists())

        # Marcar favorito (POST)
        response = self.client.post(url_toggle_fav, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(FavoriteEvent.objects.filter(user=self.user, event=self.event).exists())

        # Desmarcar favorito (POST de nuevo)
        response = self.client.post(url_toggle_fav, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(FavoriteEvent.objects.filter(user=self.user, event=self.event).exists())
