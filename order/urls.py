from django.urls import path

from . import views

urlpatterns = [
    path('checkout/<int:listing_id>/', views.create_order, name='checkout'),
    path('confirmation/<int:order_id>/', views.received_order, name='purchase_confirmation'),
    path('mark-order/<int:order_id>/<str:role>/', views.mark_order, name='mark_order'),
]
