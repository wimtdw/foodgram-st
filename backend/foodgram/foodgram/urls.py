from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from api.views import redirect_short_link

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:short_code>/', redirect_short_link, name='short-link-redirect'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
