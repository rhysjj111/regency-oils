# In core/admin.py

from django.contrib import admin
# Make sure you've imported all the relevant models
from .models import (
    CustomUser, Customer, Site, Vehicle, RouteDefinition,
    Route, Stop, Collection, DailyVehicleLog
)
from django.contrib.auth.admin import UserAdmin

# 1. This class defines how Stops will be displayed 'inline' on the Route page
class StopInline(admin.TabularInline):
    model = Stop
    # 2. We only show fields the planner needs, hiding driver-only fields
    fields = ('sequence', 'site', 'is_priority')
    # 3. This gives the planner a few empty slots to add new stops
    extra = 3

# 4. This class defines the main admin page for the Route model
class RouteAdmin(admin.ModelAdmin):
    # 5. This is the magic line that includes the stop editor
    inlines = [StopInline]
    # 6. These improve the main list view of all routes
    list_display = ('definition', 'route_date', 'vehicle')
    list_filter = ('route_date', 'definition')

# --- Update your registrations at the bottom of the file ---

# Unregister the simple versions if they were there
# admin.site.unregister(Route)
# admin.site.unregister(Stop)

# Register Route with its new, powerful admin class
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