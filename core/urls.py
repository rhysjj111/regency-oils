from django.urls import path, include
from . import views
from . import api
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('api/today-stops/', api.StopListView.as_view(), name='api-today-stops'),
    path('api/stops/<int:stop_id>/submit-collection/', api.StopCollectionCreateView.as_view(), name='api-submit-collection'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)