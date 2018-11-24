from django.contrib import admin
from django.urls import path

from django_managerie import Managerie

m = Managerie(admin.site)
m.patch()

urlpatterns = [
    path('admin/', admin.site.urls),
]
