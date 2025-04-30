from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("events/", views.events, name="events"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path('refunds/', views.refund_list, name='refund_list'),
    path('refunds/<int:refund_id>/approve/', views.approve_refund, name='approve_refund'),
    path('refunds/<int:refund_id>/reject/', views.reject_refund, name='reject_refund'),
    path('refunds/<int:refund_id>/delete/', views.delete_refund, name='delete_refund'),
    path('refunds/create/', views.create_refund, name='create_refund'),
    path('refunds/<int:refund_id>/update/', views.refund_update, name='refund_update'),

]
