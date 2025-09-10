import datetime
from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html, mark_safe
from django.template.response import TemplateResponse
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import DateFieldListFilter
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from unfold.admin import ModelAdmin
from unfold.contrib.inlines.admin import TabularInline
from unfold.components import BaseComponent, register_component
from .forms import CollectionForm
from .models import (
    CustomUser, Customer, Site, Vehicle, RouteDefinition, Route,
    Stop, Collection, DailyVehicleLog, RouteForLoading
)
from .views import StopCollectionView
from .filters import TodayDateFieldListFilter, RouteTodayDateFieldListFilter


# --- INLINES ---

class StopInline(TabularInline):
    """Editable inline for the Planner's main route view."""
    model = Stop
    fields = ('sequence', 'site', 'is_priority', 'planned_fresh_oil_load')
    extra = 0

class LoadingStopInline(TabularInline):
    """Read-only inline for the Warehouse Manager's loading view."""
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
    get_site_display.short_description = "Site"


# --- ADMIN CLASSES ---

class RouteAdmin(ModelAdmin):
    """Admin for the Planner (editable)."""
    inlines = [StopInline]
    list_display = ('definition', 'route_date', 'vehicle', 'view_reconciliation_link')
    list_filter = ('route_date', 'definition')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/reconciliation/', self.admin_site.admin_view(self.reconciliation_view), name='core_route_reconciliation'),
            path('driver-dashboard/', self.admin_site.admin_view(self.driver_dashboard_view), name='core_route_driver_dashboard'),
            path('stop/<path:object_id>/collect/', self.admin_site.admin_view(StopCollectionView.as_view(model_admin=self)), name='core_stop_collect'),
        ]
        return custom_urls + urls
    
    def driver_dashboard_view(self, request):
        context = self.admin_site.each_context(request)
        today = datetime.date.today()
        
        try:
            todays_route = Route.objects.get(drivers=request.user, route_date=today)
            # Get ALL stops for the day, not just pending
            stops = todays_route.stops.all().order_by('-status', 'sequence')
            
            # Create the Stop card data for the dashboard list
            cards_data = []
            for stop in stops:
                stop_form_url = reverse('admin:core_stop_collect', args=[stop.pk])
                card_class = ""
                if stop.status != 'PENDING':
                    card_class = "opacity-50"

                cards_data.append({
                    "title": f"{stop.sequence + 1}. {stop.site.customer.name}",
                    "subtitle": stop.site.postcode,
                    "link": stop_form_url,
                    "label": stop.get_status_display(),
                    "class": card_class,
                })

            # Add data to the context for the template
            context['route'] = todays_route
            context['stops_cards_data'] = cards_data

        except Route.DoesNotExist:
            context['route'] = None
            context['stops_cards_data'] = []

        return TemplateResponse(request, 'admin/driver_dashboard.html', context)

    def reconciliation_view(self, request, object_id):
        route = self.get_object(request, object_id)
        stops = route.stops.all()
        collections = Collection.objects.filter(stop__in=stops)

        # --- PREPARE DATA AS LISTS OF DICTIONARIES ---
        
        financial_cards = [
            {
                "title": "Money In (Fresh Oil Sales)",
                "metric": f"£{collections.aggregate(total=Sum('payment_received'))['total'] or 0.00:.2f}",
                "color_class": "bg-green-50 dark:bg-green-900/20"
            },
            {
                "title": "Money Out (Waste Oil Payments)",
                "metric": f"£{collections.aggregate(total=Sum('payment_made'))['total'] or 0.00:.2f}",
                "color_class": "bg-red-50 dark:bg-red-900/20"
            }
        ]

        oil_cards = [
            {
                "title": "Planned Fresh Oil",
                "metric": f"{stops.aggregate(total=Sum('planned_fresh_oil_load'))['total'] or 0.00:.2f} L"
            },
            {
                "title": "Actual Fresh Oil Loaded",
                "metric": f"{stops.aggregate(total=Sum('actual_fresh_oil_loaded'))['total'] or 0.00:.2f} L"
            }
        ]

        extra_context = {
            'original': route,
            'financial_cards': financial_cards,
            'oil_cards': oil_cards,
        }
        
        self.change_form_template = 'admin/reconciliation_report.html'
        return self.change_view(request, object_id, extra_context=extra_context)

    def view_reconciliation_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:core_route_reconciliation', args=[obj.pk])
        return format_html('<a href="{}">View Report</a>', url)
    view_reconciliation_link.short_description = "Reconciliation"

class RouteForLoadingAdmin(ModelAdmin):
    """Admin for the Warehouse Manager's read-only loading view."""
    inlines = [LoadingStopInline]
    list_display = ('definition', 'route_date', 'vehicle')
    list_filter = (RouteTodayDateFieldListFilter,)
    readonly_fields = ('definition', 'route_date', 'vehicle', 'drivers')

    change_form_template = 'admin/route_loading_view.html'


class DailyVehicleLogAdmin(ModelAdmin):
    list_display = ('route', 'checked_by', 'log_time')
    list_filter = (TodayDateFieldListFilter,)

    # This method controls the layout of the form itself. It checks if you are editing an existing log (if obj:)
    # When editing an existing log: It shows our special display_route method, which is a non-clickable, read-only text field.
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

    # get_readonly_fields tells Django to always make the "Checked By" field read-only, if you are editing an existing log.
    def get_readonly_fields(self, request, obj=None):
        if obj: 
            return ['display_route', 'display_checked_by']
        else:
            return ['display_checked_by']

    # Runs when the form is saved. The if not obj.pk: check means "if this is a brand new object," 
    # and it automatically sets the checked_by field to the currently logged-in user, creating a secure audit trail.
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.checked_by = request.user
        super().save_model(request, obj, form, change)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_delete'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )
    
    # Customizes the route dropdown, so it only shows routes that haven't been created for a log today.
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "route":
            today = datetime.date.today()
            logged_route_ids = DailyVehicleLog.objects.filter(route__route_date=today).values_list('route_id', flat=True)
            kwargs["queryset"] = Route.objects.filter(route_date=today).exclude(id__in=logged_route_ids)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    #Helper method to create a read-only text field for the route.
    def display_route(self, obj):
        return str(obj.route)
    display_route.short_description = "Route"

    #Helper method to create a read-only text field for the route.
    def display_checked_by(self, obj):
        # When creating a new form, 'obj' doesn't exist yet, so we can't show a user.
        # It will be set automatically on save.
        if obj and obj.checked_by:
            return obj.checked_by.get_full_name() or obj.checked_by.username
        return "Set automatically on save"
    display_checked_by.short_description = "Checked By"

# --- REGISTRATIONS ---

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Customer)
admin.site.register(Site)
admin.site.register(Vehicle)
admin.site.register(RouteDefinition)
admin.site.register(Route, RouteAdmin) # The main editable route admin
admin.site.register(RouteForLoading, RouteForLoadingAdmin) # The warehouse manager's read-only view
admin.site.register(Stop)
admin.site.register(Collection)
admin.site.register(DailyVehicleLog, DailyVehicleLogAdmin)