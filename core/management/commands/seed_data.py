# In core/management/commands/seed_data.py

import datetime
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.models import (
    RouteDefinition, Vehicle, Customer, Site, Route, Stop, CustomUser, DailyVehicleLog, Collection
)

class Command(BaseCommand):
    help = 'Seeds the database with a large, realistic set of sample data and recent history.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("--- Deleting old data... ---")
        Collection.objects.all().delete()
        Stop.objects.all().delete()
        DailyVehicleLog.objects.all().delete()
        Route.objects.all().delete()
        Site.objects.all().delete()
        Customer.objects.all().delete()
        Vehicle.objects.all().delete()
        RouteDefinition.objects.all().delete()
        CustomUser.objects.filter(is_superuser=False).delete()

        self.stdout.write("\n--- Creating new sample data... ---")

        # 1. Create Core Data
        route_defs = {name: RouteDefinition.objects.create(name=name) for name in ['Cardiff South', 'Cardiff North', 'Newport', 'Bristol', 'Barry & Penarth', 'Caerphilly']}
        vehicles = {v['name']: Vehicle.objects.create(registration_number=v['reg'], nickname=v['name']) for v in [{'reg': 'CV21 ABC', 'name': 'Big Blue'}, {'reg': 'CV21 XYZ', 'name': 'The Tank'}]}
        drivers = [CustomUser.objects.create_user(username=d['username'], password='password123', first_name=d['first_name'], last_name=d['last_name'], is_staff=True) for d in [{'username': 'driver1', 'first_name': 'Dave', 'last_name': 'Davis'}, {'username': 'driver2', 'first_name': 'Jane', 'last_name': 'Smith'}]]
        self.stdout.write("Core data created.")

        # 2. Create Customers and Sites
        customer_names = ["The Royal Oak", "The Red Lion", "The White Hart", "The Crown Inn", "The Bell", "The Plough", "The Ship", "The King's Arms", "City Fish Bar", "Golden Dragon", "Mamma Mia Pizzeria", "The Corner Deli", "Newport Grill House", "Bristol Fryer", "Gavin's Chippy", "The Pilot", "Seaview Restaurant", "The Heathcock Inn", "The Potters", "The Three Elms", "La Trattoria", "Spice Fusion", "The Olive Tree", "The Harbour Lights", "The Old Cottage", "The Castle Bistro", "The Black Bull", "The Rose & Crown", "The Swan", "The George", "The Railway Arms", "The Victoria", "The Angel", "The Fox & Hounds", "The Star Inn", "The Horse & Groom", "The Lamb"] * 2
        postcode_map = {'CF10': 'Cardiff South', 'CF14': 'Cardiff North', 'NP20': 'Newport', 'BS1': 'Bristol', 'CF62': 'Barry & Penarth', 'CF83': 'Caerphilly'}
        
        all_sites = []
        for name in customer_names:
            customer, _ = Customer.objects.get_or_create(name=name, defaults={'contact_email': f"{name.lower().replace(' ', '')}@example.com"})
            prefix = random.choice(list(postcode_map.keys()))
            city = postcode_map[prefix].split(' ')[0]
            site = Site.objects.create(
                customer=customer, address_line_1=f"{random.randint(1, 200)} Main Street", city=city,
                postcode=f"{prefix} {random.randint(1,9)}{random.choice('ADEFGHJLNPQRSTUWXYZ')}{random.choice('ADEFGHJLNPQRSTUWXYZ')}",
                visit_frequency_days=random.choice([7, 14, 21, 30])
            )
            all_sites.append(site)
        self.stdout.write(f"Created {len(all_sites)} total sites.")
        
        # 3. Assign a default route to ~80% of sites
        sites_to_assign_count = int(len(all_sites) * 0.8)
        sites_to_assign = all_sites[:sites_to_assign_count]
        route_def_list = list(route_defs.values())
        assigned_count = 0
        for i, site in enumerate(sites_to_assign):
            site.default_route = route_def_list[i % len(route_def_list)]
            site.save()
            assigned_count += 1
        self.stdout.write(f"Assigned a default route to {assigned_count} sites.")

        # 4. Create varied historical visit data
        self.stdout.write("Creating varied and recent historical visit data...")
        today = timezone.now()
        for site in all_sites:
            # THIS IS THE FIX: Random number is now between 1 and 14
            days_ago = random.randint(1, 14)
            visit_date = (today - datetime.timedelta(days=days_ago)).date()
            self._create_historical_collection(site, visit_date, route_def_list, list(vehicles.values()))
        self.stdout.write("Historical data created.")
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded the database.'))

    def _create_historical_collection(self, site, date, route_defs, vehicles):
        """Helper function to create a single historical collection record."""
        route_def = site.default_route or random.choice(route_defs)
        past_route, _ = Route.objects.get_or_create(
            definition=route_def, route_date=date,
            defaults={'vehicle': random.choice(vehicles)}
        )
        
        # --- THIS IS THE FIX ---
        # Use get_or_create for the Stop to prevent duplicates
        past_stop, created = Stop.objects.get_or_create(
            route=past_route, 
            site=site,
            defaults={'sequence': 1, 'status': 'COMPLETED'}
        )
        
        # Only create a collection if the stop was newly created for this history
        if created:
            Collection.objects.create(
                stop=past_stop, waste_oil_quantity=random.randint(20, 200),
                timestamp=timezone.make_aware(datetime.datetime.combine(date, datetime.time(12, 0)))
            )