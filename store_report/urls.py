from django.urls import path
from store_report import views

urlpatterns = [
    path('generate-report/', views.trigger_report, name='generate_report'),
    path('get-report/', views.get_report, name='get_report'),
]