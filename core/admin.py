from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    Customer,
    Site,
    Vehicle,
    RouteDefinition,
    Route,
    Stop,
    Collection,
)

# We need to use a special class for the CustomUser
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # You can customize the admin display for users here if needed
    
# Register all your models here so they appear in the admin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Customer)
admin.site.register(Site)
admin.site.register(Vehicle)
admin.site.register(RouteDefinition)
admin.site.register(Route)
admin.site.register(Stop)
admin.site.register(Collection)