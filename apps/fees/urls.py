from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    path('', views.fee_dashboard_view, name='dashboard'),
    path('pay/<int:invoice_id>/', views.record_payment_view, name='record_payment'),
    path('promotion/', views.student_promotion_view, name='promotion'),
]