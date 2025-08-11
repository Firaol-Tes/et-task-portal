from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('submit_tasks/', views.submit_tasks, name='submit_tasks'),
    path('submission_confirmation/', views.submission_confirmation, name='submission_confirmation'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export_excel/', views.export_excel, name='export_excel'),
    path('export_pdf/', views.export_pdf, name='export_pdf'),
    path('download_inventory/', views.download_inventory, name='download_inventory'),
]