import re
from datetime import datetime, timedelta, timezone  
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import formats
from django.utils.timezone import get_current_timezone
from django.utils import timezone as dj_timezone  

from playwright.sync_api import expect

from app.models import Event, User, Category, Venue
from app.test.test_e2e.base import BaseE2ETest




class EventBaseTest(BaseE2ETest):
    """Clase base específica para tests de eventos"""

    def setUp(self):
        super().setUp()

        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        self.category1 = Category.objects.create(name="Música")
        self.category2 = Category.objects.create(name="Deportes")
        self.venue1 = Venue.objects.create(name="Estadio Principal", address="Calle Falsa 123", capacity=1000)
        self.venue2 = Venue.objects.create(name="Teatro Central", address="Avenida Siempre Viva 456", capacity=500)

        # Obtener la zona horaria local
        local_tz = dj_timezone.get_current_timezone()

        # Evento 1: Fecha fija con hora local (ej. 29/05/2025 17:41 hora local)
        naive_dt = datetime(2025, 5, 29, 17, 41)
        aware_dt = naive_dt.replace(tzinfo=local_tz) 

        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=aware_dt,
            organizer=self.organizer,
            venue=self.venue1,
        )
        self.event1.categories.add(self.category1)

        # Evento 2: Dinámico (60 días después del "ahora")
        now = dj_timezone.now()
        future_date2 = now.replace(hour=14, minute=30, second=0, microsecond=0) + timedelta(days=60)
        self.event2 = Event.objects.create(
            title="Evento de prueba 2",
            description="Descripción del evento 2",
            scheduled_at=future_date2,
            organizer=self.organizer,
            venue=self.venue2,
        )
        self.event2.categories.add(self.category2)

    def _format_date_for_table(self, dt_obj):
        """
        Formatea un objeto datetime a la cadena esperada en la tabla HTML,
        utilizando los filtros de formato de Django para manejar zonas horarias y localización.
        """
        local_dt = dj_timezone.localtime(dt_obj)

        # Obtener el formato de fecha y hora
        date_part = formats.date_format(local_dt, "j M Y")
        time_part = formats.date_format(local_dt, "H:i")

        
        parts = date_part.split(' ')
        if len(parts) == 3: #
            
            parts[1] = parts[1].lower()
            date_part = ' '.join(parts) 
       

        return f"{date_part}, {time_part}"

    def _table_has_event_info(self):
        """Método auxiliar para verificar que la tabla tiene la información correcta de eventos"""
        # Verificar encabezados de la tabla
        headers = self.page.locator("table thead th")

        expect(headers.nth(0)).to_have_text("Título")
        expect(headers.nth(1)).to_have_text("Descripción")
        expect(headers.nth(2)).to_have_text("Fecha")
        expect(headers.nth(3)).to_have_text("Categorías")
        expect(headers.nth(4)).to_have_text("Estado")
        expect(headers.nth(5)).to_have_text("Acciones")


        # Verificar que los eventos aparecen en la tabla
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(2)

        # Formatear las fechas de los objetos Event para la comparación usando la función de Django
        expected_date_time_event1 = self._format_date_for_table(self.event1.scheduled_at)
        expected_date_time_event2 = self._format_date_for_table(self.event2.scheduled_at)


        # Verificar datos del primer evento (self.event1)
        row0 = rows.nth(0)
        expect(row0.locator("td").nth(0)).to_have_text("Evento de prueba 1")
        expect(row0.locator("td").nth(1)).to_have_text("Descripción del evento 1")
        expect(row0.locator("td").nth(2)).to_have_text(expected_date_time_event1)

       
        expect(row0.locator("td").nth(3)).to_have_text("Música")
        expect(row0.locator("td").nth(4)).to_contain_text("Activo") 

        # Verificar datos del segundo evento (self.event2)
        row1 = rows.nth(1)
        expect(row1.locator("td").nth(0)).to_have_text("Evento de prueba 2")
        expect(row1.locator("td").nth(1)).to_have_text("Descripción del evento 2")
        expect(row1.locator("td").nth(2)).to_have_text(expected_date_time_event2)

        expect(row1.locator("td").nth(3)).to_have_text("Deportes")
        expect(row1.locator("td").nth(4)).to_contain_text("Activo") # CAMBIAR A "Activo" y usar to_contain_text


    def _table_has_correct_actions(self, user_type):
        """Método auxiliar para verificar que las acciones son correctas según el tipo de usuario"""
        rows = self.page.locator("table tbody tr")
        num_rows = rows.count()

        for i in range(num_rows):
            row = rows.nth(i)
            event_id = self.event1.id if i == 0 else self.event2.id #type: ignore

            detail_button = row.get_by_role("link", name="Ver Detalle")
            edit_button = row.get_by_role("link", name="Editar")
            delete_form   = row.locator(f"form[action$='/{event_id}/delete/']")

            expect(detail_button).to_be_visible()
            expect(detail_button).to_have_attribute("href", f"/events/{event_id}/")

            if user_type == "organizador":
                expect(edit_button).to_be_visible()
                expect(edit_button).to_have_attribute("href", f"/events/{event_id}/edit/")

                expect(delete_form).to_have_attribute("action", f"/events/{event_id}/delete/")
                expect(delete_form).to_have_attribute("method", "POST")

                delete_button = delete_form.get_by_role("button", name="Eliminar")
                expect(delete_button).to_be_visible()
            else:
                expect(edit_button).to_have_count(0)
                expect(delete_form).to_have_count(0)


class EventAuthenticationTest(EventBaseTest):
    """Tests relacionados con la autenticación y permisos de usuarios en eventos"""

    def test_events_page_requires_login(self):
        """Test que verifica que la página de eventos requiere inicio de sesión"""
        # Cerrar sesión si hay alguna activa
        self.context.clear_cookies()

        # Intentar ir a la página de eventos sin iniciar sesión
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que redirige a la página de login
        expect(self.page).to_have_url(re.compile(r"/accounts/login/"))


class EventDisplayTest(EventBaseTest):
    """Tests relacionados con la visualización de la página de eventos"""

    def test_events_page_display_as_organizer(self):
        """Test que verifica la visualización correcta de la página de eventos para organizadores"""
        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar el título de la página
        expect(self.page).to_have_title("Eventos")

        # Verificar que existe un encabezado con el texto "Eventos"
        header = self.page.locator("h1")
        expect(header).to_have_text("Eventos")
        expect(header).to_be_visible()

        # Verificar que existe un botón de "Crear Evento"
        create_button = self.page.get_by_role("link", name="Crear Evento")
        expect(create_button).to_be_visible()

        # Verificar que existe una tabla
        table = self.page.locator("table")
        expect(table).to_be_visible()

        self._table_has_event_info()
        self._table_has_correct_actions("organizador")


    def test_events_page_regular_user(self):
        """Test que verifica la visualización de la página de eventos para un usuario regular"""
        # Iniciar sesión como usuario regular
        self.login_user("usuario", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        expect(self.page).to_have_title("Eventos")

        # Verificar que existe un encabezado con el texto "Eventos"
        header = self.page.locator("h1")
        expect(header).to_have_text("Eventos")
        expect(header).to_be_visible()

        # Verificar que existe una tabla
        table = self.page.locator("table")
        expect(table).to_be_visible()

        # Verificar la información y acciones de la tabla (sin botones de gestión)
        self._table_has_event_info()
        self._table_has_correct_actions("regular")

    def test_events_page_no_events(self):
        """Test que verifica el comportamiento cuando no hay eventos"""
        # Eliminar todos los eventos
        Event.objects.all().delete()

        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que existe un mensaje indicando que no hay eventos
        no_events_message = self.page.locator("text=No hay eventos disponibles")
        expect(no_events_message).to_be_visible()


class EventPermissionsTest(EventBaseTest):
    """Tests relacionados con los permisos de usuario para diferentes funcionalidades"""

    def test_buttons_visible_only_for_organizer(self):
        """Test que verifica que los botones de gestión solo son visibles para organizadores"""
        # Primero verificar como organizador
        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que existe el botón de crear
        create_button = self.page.get_by_role("link", name="Crear Evento")
        expect(create_button).to_be_visible()

        # Cerrar sesión
        self.page.get_by_role("button", name="Salir").click()

        # Iniciar sesión como usuario regular
        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que NO existe el botón de crear
        create_button = self.page.get_by_role("link", name="Crear Evento")
        expect(create_button).to_have_count(0)


class EventCRUDTest(EventBaseTest):
    """Tests relacionados con las operaciones CRUD (Crear, Leer, Actualizar, Eliminar) de eventos"""

    def test_create_new_event_organizer(self):
        """Test que verifica la funcionalidad de crear un nuevo evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Hacer clic en el botón de crear evento
        self.page.get_by_role("link", name="Crear Evento").click()

        # Verificar que estamos en la página de creación de evento
        expect(self.page).to_have_url(f"{self.live_server_url}/events/create/")

        header = self.page.locator("h1")
        expect(header).to_have_text("Crear evento")
        expect(header).to_be_visible()

        # Completar el formulario con una fecha futura y hora específica
        future_date = (dj_timezone.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        future_time = "16:45" # Hora fija para determinismo del test

        self.page.get_by_label("Título del Evento").fill("Evento de prueba E2E")
        self.page.get_by_label("Descripción").fill("Descripción creada desde prueba E2E")
        self.page.get_by_label("Fecha").fill(future_date)
        self.page.get_by_label("Hora").fill(future_time)

        # Seleccionar la categoría (es un checkbox, no un select)
        # El label del checkbox individual es el nombre de la categoría (ej. "Música")
        self.page.get_by_label(self.category1.name).check()

        # Seleccionar la ubicación (es un select)
        # El label en el HTML es "Ubicación del Evento"
        self.page.get_by_label("Ubicación del Evento").select_option(str(self.venue1.id)) #type:ignore

        # Enviar el formulario
        self.page.get_by_role("button", name="Crear Evento").click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Verificar que ahora hay 3 eventos
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(3)

        # Verificar el nuevo evento en la tabla
        row = self.page.locator("table tbody tr").last
        expect(row.locator("td").nth(0)).to_have_text("Evento de prueba E2E")
        expect(row.locator("td").nth(1)).to_have_text("Descripción creada desde prueba E2E")
        # Formatear la fecha esperada para el nuevo evento en la tabla
        new_event_datetime = dj_timezone.make_aware(datetime.strptime(f"{future_date} {future_time}", "%Y-%m-%d %H:%M"))
        expected_new_event_date_time = self._format_date_for_table(new_event_datetime)
        expect(row.locator("td").nth(2)).to_have_text(expected_new_event_date_time)
        expect(row.locator("td").nth(3)).to_have_text(self.category1.name) # Esperamos el nombre de la categoría seleccionada
        expect(row.locator("td").nth(4)).to_contain_text("Activo") # Asume que se crea como "Activo"
    

    def test_delete_event_organizer(self):
        """Test que verifica la funcionalidad de eliminar un evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Contar eventos antes de eliminar
        initial_count = len(self.page.locator("table tbody tr").all())

        # Hacer clic en el botón eliminar del primer evento
        self.page.get_by_role("button", name="Eliminar").first.click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Verificar que ahora hay un evento menos
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(initial_count - 1)

        # Verificar que el evento eliminado ya no aparece en la tabla
        expect(self.page.get_by_text("Evento de prueba 1")).to_have_count(0)