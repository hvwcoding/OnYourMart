from django.urls import path

from .views import (
    ListingDeleteView,
    ListingSearchView, ListingDetailsView, ListingCreateOrUpdateView
)

urlpatterns = [
    path('search/', ListingSearchView.as_view(), name='search_listing'),
    path('details/<int:pk>/', ListingDetailsView.as_view(), name='listing_details'),
    path('create/', ListingCreateOrUpdateView.as_view(), name='create_listing'),
    path('edit/<int:pk>/', ListingCreateOrUpdateView.as_view(), name='update_listing'),
    path('delete/<int:pk>/', ListingDeleteView.as_view(), name='delete_listing'),
]
