# In core/dashboard.py (with filtering logic)
import datetime
from django.utils import timezone
from django.db.models import Subquery, OuterRef
from .models import Route, RouteDefinition, Stop, Site, Collection

def planner_dashboard_callback(request, context):
    today = datetime.date.today()

    # (Auto-creation of routes remains the same)
    active_definitions = RouteDefinition.objects.filter(is_active=True)
    for definition in active_definitions:
        Route.objects.get_or_create(
            definition=definition, 
            route_date=today, 
            defaults={'vehicle': None}
        )
    
    todays_routes = Route.objects.filter(route_date=today).prefetch_related('stops')

    # --- UPDATED: Unassigned Stops Query with Filtering ---
    assigned_site_ids = Stop.objects.filter(route__route_date=today).values_list('site_id', flat=True)
    
    # Base query for unassigned sites
    unassigned_sites = Site.objects.exclude(id__in=assigned_site_ids)

    # Check for a filter in the URL (e.g., /admin/?route_filter=1)
    route_filter_id = request.GET.get('route_filter')
    if route_filter_id:
        if route_filter_id == 'none':
            unassigned_sites = unassigned_sites.filter(default_route__isnull=True)
        elif route_filter_id.isdigit():
            unassigned_sites = unassigned_sites.filter(default_route_id=route_filter_id)

    # (Urgency Score Calculation remains the same)
    last_collection_subquery = Collection.objects.filter(stop__site=OuterRef('pk')).order_by('-timestamp').values('timestamp')[:1]
    unassigned_sites = unassigned_sites.annotate(last_visit=Subquery(last_collection_subquery))
    
    sites_with_urgency = []
    for site in unassigned_sites:
        days_since_visit = 999
        if site.last_visit:
            days_since_visit = (timezone.now() - site.last_visit).days
        
        urgency_score = (days_since_visit / site.visit_frequency_days) if site.visit_frequency_days > 0 else 0
        site.urgency_score = round(urgency_score, 2)
        site.days_since_last_visit = days_since_visit
        sites_with_urgency.append(site)

    sites_with_urgency.sort(key=lambda x: x.urgency_score, reverse=True)

    # --- Add ALL route definitions to the context for the dropdown ---
    all_route_definitions = RouteDefinition.objects.filter(is_active=True)

    context.update({
        "todays_routes": todays_routes,
        "unassigned_stops": sites_with_urgency,
        "all_route_definitions": all_route_definitions, # For the filter dropdown
        "current_filter": route_filter_id, # To remember the selected option
    })

    return context