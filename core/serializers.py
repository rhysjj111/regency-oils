# In core/serializers.py
from rest_framework import serializers
from .models import Stop, Site, Customer, Collection

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name']

class SiteSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()

    class Meta:
        model = Site
        fields = ['id', 'customer', 'address_line_1', 'city', 'postcode']

class StopSerializer(serializers.ModelSerializer):
    site = SiteSerializer()

    class Meta:
        model = Stop
        fields = ['id', 'sequence', 'status', 'is_priority', 'site']

class CollectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        # These are the fields the driver will submit
        fields = [
            'waste_oil_quantity',
            'payment_made',
            'docket_number',
            # We'll add fresh oil fields here later
        ]

    def create(self, validated_data):
        # When a collection is created, also update the stop's status
        stop = self.context['stop']
        collection = Collection.objects.create(stop=stop, **validated_data)
        stop.status = Stop.Status.COMPLETED
        stop.save()
        return collection