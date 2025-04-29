from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    #accounts
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    #Events
    path("events/", views.events, name="events"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    #tickets
    path('tickets/', views.ticket_list, name="ticket_list"),
    path('tickets/<int:event_id>/create/', views.ticket_create, name="ticket_create"),
    path('tickets/<int:ticket_id>/edit/', views.ticket_update, name="ticket_update"),
    path('tickets/<int:ticket_id>/delete/', views.ticket_delete, name="ticket_delete"),
]
