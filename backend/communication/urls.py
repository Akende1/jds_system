from django.urls import path

from . import views

app_name = 'communication'

urlpatterns = [
    path('', views.communication_hub, name='communication_hub'),
    path('teacher/', views.teacher_communication_hub, name='teacher_communication_hub'),
    path('announcements/', views.communication_hub, name='announcement_list'),
    path('messages/', views.communication_hub, name='message_list'),
    path('reminders/', views.communication_hub, name='reminder_list'),
    path('newsletters/', views.communication_hub, name='newsletter_list'),
]
