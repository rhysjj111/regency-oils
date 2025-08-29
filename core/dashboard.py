# In core/dashboard.py (Corrected)
from django.utils import timezone
from .models import Route, RouteDefinition, Stop, Site

def planner_dashboard_callback(request, context):
    """
    This callback prepares data and adds it to the context
    for the custom admin/index.html template.
    """
    today = timezone.now().date()

    # --- Auto-create today's routes if they don't exist ---
    active_definitions = RouteDefinition.objects.filter(is_active=True)
    for definition in active_definitions:
        Route.objects.get_or_create(
            definition=definition,
            route_date=today,
            # You may want to set a default vehicle or leave as None
            defaults={'vehicle': None} 
        )
    
    # --- Get all routes scheduled for today ---
    todays_routes = Route.objects.filter(route_date=today).prefetch_related('stops')

    # --- Get all unassigned sites ---
    assigned_site_ids = Stop.objects.filter(route__route_date=today).values_list('site_id', flat=True)
    unassigned_sites = Site.objects.exclude(id__in=assigned_site_ids)

    # --- Add our data to the context ---
    context.update({
        "todays_routes": todays_routes,
        "unassigned_stops": unassigned_sites,
    })

    return context