from django.shortcuts import redirect
from django.urls import path
from .views import kpi_user, kpi_overview

urlpatterns = [
    # Your other URL patterns go here...
    path('redirect/recycle-an-item/', lambda request: redirect('https://www.recyclenow.com/recycle-an-item'),
         name='redirect_recycle_an_item'),
    path('redirect/recycling-locator/', lambda request: redirect('https://www.recyclenow.com/recycling-locator'),
         name='redirect_recycling_locator'),
    path('redirect/how-to-recycle/', lambda request: redirect('https://www.recyclenow.com/how-to-recycle'),
         name='redirect_how_to_recycle'),
    path('', kpi_user, name='kpi_user'),
    path('overview', kpi_overview, name='kpi_overview'),
]
