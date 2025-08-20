from django.urls import path
from . import api

urlpatterns = [
    path('stops/', api.StopListView.as_view(), name='api-stop-list'),
    path('stops/<int:stop_id>/', api.StopDetailView.as_view(), name='api-stop-detail'),
    path('stops/<int:stop_id>/collection/', api.StopCollectionCreateView.as_view(), name='api-stop-collection-create'),
]