from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import Route, Stop
from .serializers import StopSerializer
from .serializers import CollectionCreateSerializer

class StopListView(APIView):
    """
    API endpoint for a driver to get their stops for the current day.
    
    Expects a 'vehicle_id' query parameter in the URL, 
    e.g., /api/stops/?vehicle_id=1
    """
    def get(self, request, *args, **kwargs):
        # 1. Get the vehicle ID from the URL
        vehicle_id = request.query_params.get('vehicle_id')
        if not vehicle_id:
            return Response(
                {"error": "A 'vehicle_id' parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Find today's route for that vehicle
        today = timezone.now().date()
        try:
            todays_route = Route.objects.get(vehicle_id=vehicle_id, route_date=today)
        except Route.DoesNotExist:
            return Response(
                {"message": "No route found for this vehicle today."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 3. Get all the stops for that route, in order
        stops = todays_route.stops.all().order_by('sequence')
        
        # 4. Serialize the data and return it as a JSON response
        serializer = StopSerializer(stops, many=True)
        return Response(serializer.data)

class StopDetailView(APIView):
    """
    API endpoint to retrieve the details of a single stop.
    """
    def get(self, request, stop_id, *args, **kwargs):
        try:
            stop = Stop.objects.get(id=stop_id)
            serializer = StopSerializer(stop) # Note: not many=True
            return Response(serializer.data)
        except Stop.DoesNotExist:
            return Response(
                {"error": "Stop not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class StopCollectionCreateView(APIView):
    """
    API endpoint for a driver to submit the details of a collection for a specific stop.
    """
    def post(self, request, stop_id, *args, **kwargs):
        try:
            stop = Stop.objects.get(id=stop_id, status=Stop.Status.PENDING)
        except Stop.DoesNotExist:
            return Response(
                {"error": "Pending stop not found or already completed."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # We pass the 'stop' object into the serializer's context
        serializer = CollectionCreateSerializer(data=request.data, context={'stop': stop})
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Collection submitted successfully."}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)