import re
from django.utils.timezone import now, timedelta
from playwright.sync_api import expect

from app.models import Event, User, Venue, Category


from .base import BaseE2ETest


class TestEventStateFlow(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.organizer = User.objects.create_user(username='organizer', password='password', is_organizer=True)
        self.category = Category.objects.create(name="Tecnologia")
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="Some Street",
            city="Test City",
            capacity=100,
            contact="venue@test.com"
        )

    def test_event_shows_correct_state(self):
        #accedo al login y me logueo como organizador, previamente creado.
        self.page.goto(f'{self.live_server_url}/accounts/login/')
        self.page.fill('input[name="username"]', 'organizer')
        self.page.fill('input[name="password"]', 'password')
        self.page.click('button:has-text("Iniciar sesión")')
        expect(self.page).not_to_have_url(f'{self.live_server_url}/accounts/login/')


        self.page.goto(f'{self.live_server_url}/events/')
        self.page.click("text=Crear Evento")
        self.page.fill('input[name="title"]', 'Conferencia Playwright')
        self.page.fill('textarea[name="description"]', 'Una conferencia sobre pruebas automáticas con Playwright.')

       
        future_date = (now() + timedelta(days=3)).date().isoformat()
        future_time = (now() + timedelta(hours=2)).time().strftime('%H:%M')
        self.page.fill('input[name="date"]', future_date)
        self.page.fill('input[name="time"]', future_time)

        
        self.page.check(f'input[type="checkbox"][value="{self.category.id}"]') # type: ignore
        self.page.select_option('select[name="venue"]', str(self.venue.id)) # type: ignore

        # Enviar el formulario
        self.page.get_by_role("button", name="Crear Evento").click()
        self.page.goto(f'{self.live_server_url}/events/')
        expect(self.page).to_have_url(f'{self.live_server_url}/events/')
        expect(self.page.locator("text=Conferencia Playwright")).to_be_visible() #verifico si se creo el evento

       
        self.page.click('a[title="Editar"]')

        
        expect(self.page).to_have_url(re.compile(r"/events/\d+/edit/"))

        # Modificar la fecha y hora
        new_date = (now() + timedelta(days=5)).date().isoformat()
        new_time = (now() + timedelta(hours=4)).time().strftime('%H:%M')

        self.page.fill('input[name="date"]', new_date)
        self.page.fill('input[name="time"]', new_time)

        # Enviar el formulario
        self.page.get_by_role("button", name="Crear Evento").click()

        # Verificar redirección a la lista y que el evento sigue presente
        expect(self.page).to_have_url(f'{self.live_server_url}/events/')
        expect(self.page.locator("text=Conferencia Playwright")).to_be_visible()


        #verificar que el estado haya cambiado
        event = Event.objects.get(title="Conferencia Playwright")
        self.assertEqual(event.status, "rescheduled")


