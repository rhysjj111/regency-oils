import datetime
from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.inlines.admin import TabularInline

from .models import (
    CustomUser, Customer, Site, Vehicle, RouteDefinition, Route,
    Stop, Collection, DailyVehicleLog, RouteForLoading
)
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import DateFieldListFilter



# --- INLINES ---

class StopInline(TabularInline):
    """Editable inline for the Planner's main route view."""
    model = Stop
    fields = ('sequence', 'site', 'is_priority', 'planned_fresh_oil_load')
    extra = 1

class LoadingStopInline(TabularInline):
    """Read-only inline for the Manager's loading view."""
    model = Stop
    # Use our custom method 'get_site_display' instead of the 'site' field
    fields = ('sequence', 'get_site_display', 'planned_fresh_oil_load', 'actual_fresh_oil_loaded')
    readonly_fields = ('sequence', 'get_site_display', 'planned_fresh_oil_load')
    can_delete = False
    extra = 0
    
    def has_add_permission(self, request, obj=None): return False

    # This custom method displays the site name as plain text (not a link)
    def get_site_display(self, obj):
        return str(obj.site)
    get_site_display.short_description = "Site" # Sets the column header

# --- ADMIN CLASSES ---

class RouteAdmin(ModelAdmin):
    """Admin for the Planner (editable)."""
    inlines = [StopInline]
    list_display = ('definition', 'route_date', 'vehicle')
    list_filter = ('route_date', 'definition')

class RouteForLoadingAdmin(ModelAdmin):
    """Admin for the Manager's read-only loading view."""
    inlines = [LoadingStopInline]
    list_display = ('definition', 'route_date', 'vehicle')
    list_filter = ('route_date',)
    readonly_fields = ('definition', 'route_date', 'vehicle', 'drivers')

    change_form_template = 'admin/route_loading_view.html'

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_history'] = False # This hides the button
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def get_queryset(self, request):
        # Always filter the list to only show today's routes
        return super().get_queryset(request).filter(route_date=datetime.date.today())

    # This method is called after the form and its inlines are saved
    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        # After saving the loaded oil amounts, automatically create the end-of-day log
        route = form.instance
        DailyVehicleLog.objects.get_or_create(
            route=route,
            defaults={'checked_by': request.user}
        )

    # Prevent managers from adding or deleting routes from this view
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False

class DailyVehicleLogAdmin(ModelAdmin):
    list_display = ('route', 'checked_by', 'log_time')
    list_filter = ('route__route_date',)

    def get_fieldsets(self, request, obj=None):
        if obj:
            return (
                (None, {'fields': ('display_route', 'display_checked_by')}),
                ('End of Day Measurements (litres)', {
                    'fields': ('end_day_waste_oil', 'end_day_fresh_oil')
                }),
            )
        else:
            return (
                (None, {'fields': ('route', 'display_checked_by')}),
                ('End of Day Measurements (litres)', {
                    'fields': ('end_day_waste_oil', 'end_day_fresh_oil')
                }),
            )

    def get_readonly_fields(self, request, obj=None):
        if obj: 
            return ['display_route', 'display_checked_by']
        else:
            return ['display_checked_by']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.checked_by = request.user
        super().save_model(request, obj, form, change)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_history'] = False
        extra_context['show_delete'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "route":
            today = datetime.date.today()
            logged_route_ids = DailyVehicleLog.objects.filter(route__route_date=today).values_list('route_id', flat=True)
            kwargs["queryset"] = Route.objects.filter(route_date=today).exclude(id__in=logged_route_ids)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def display_route(self, obj):
        return str(obj.route)
    display_route.short_description = "Route"

    def display_checked_by(self, obj):
        # When creating a new form, 'obj' doesn't exist yet, so we can't show a user.
        # It will be set automatically on save.
        if obj and obj.checked_by:
            return obj.checked_by.get_full_name() or obj.checked_by.username
        return "Set automatically on save"
    display_checked_by.short_description = "Checked By"

    def response_add(self, request, obj, post_url_continue=None):
        # Redirect back to the main list page after saving a new log
        return HttpResponseRedirect("../")

    # def has_delete_permission(self, request, obj=None):
    #     return False
    # change_form_template = "admin/core/dailyvehiclelog/change_form.html"

# --- REGISTRATIONS ---

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Customer)
admin.site.register(Site)
admin.site.register(Vehicle)
admin.site.register(RouteDefinition)
admin.site.register(Route, RouteAdmin) # The main editable route admin
admin.site.register(RouteForLoading, RouteForLoadingAdmin) # The manager's read-only view
admin.site.register(Stop)
admin.site.register(Collection)
admin.site.register(DailyVehicleLog, DailyVehicleLogAdmin)