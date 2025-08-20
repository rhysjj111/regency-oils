from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin

# Import all your models from the core app
from .models import (
    CustomUser,
    Customer,
    Site,
    Vehicle,
    RouteDefinition,
    Route,
    Stop,
    Collection,
    DailyVehicleLog,
)

# --- Custom Admin Classes ---

class StopInline(SortableInlineAdminMixin, admin.TabularInline):
    """
    Allows adding and drag-and-drop reordering of Stops
    directly on the Route page.
    """
    model = Stop
    # The 'sequence' field is now handled automatically by the sortable mixin
    fields = ('sequence', 'site', 'is_priority')
    extra = 1 # Provides one extra empty row for adding a new stop

class RouteAdmin(SortableAdminMixin, admin.ModelAdmin):
    """
    Customizes the admin page for Routes to include the inline stop editor.
    """
    inlines = [StopInline]
    list_display = ('definition', 'route_date', 'vehicle')
    list_filter = ('route_date', 'definition')

# --- Model Registrations --

# Register Route with its new, powerful admin class
try:
    admin.site.unregister(Route)
except admin.sites.NotRegistered:
    pass
admin.site.register(Route, RouteAdmin)

# We can keep the main Stop admin for now, so you can view all stops at once if needed
admin.site.register(Stop)

# Make sure all your other models are still registered
# (This is just an example, ensure it matches your file)
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Customer)
admin.site.register(Site)
admin.site.register(Vehicle)
admin.site.register(RouteDefinition)
admin.site.register(Collection)
admin.site.register(DailyVehicleLog)