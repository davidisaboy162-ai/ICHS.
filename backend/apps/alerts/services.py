from math import asin, cos, radians, sin, sqrt

from django.contrib.auth import get_user_model

from .models import OutbreakAlert


class AlertService:
    def __init__(self, radius_km: float = 10.0):
        self.radius_km = radius_km

    @staticmethod
    def haversine_km(lat1, lon1, lat2, lon2):
        # Fast fallback for development. Production should use PostGIS ST_DWithin().
        r = 6371.0
        d_lat = radians(lat2 - lat1)
        d_lon = radians(lon2 - lon1)
        a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
        return 2 * r * asin(sqrt(a))

    def create_alerts_for_report(self, report):
        user_model = get_user_model()
        farmers = user_model.objects.filter(role=user_model.FARMER).exclude(id=report.created_by_id)
        for farmer in farmers:
            if farmer.latitude is None or farmer.longitude is None:
                continue

            distance = self.haversine_km(report.latitude, report.longitude, farmer.latitude, farmer.longitude)
            if distance <= self.radius_km:
                OutbreakAlert.objects.get_or_create(
                    report=report,
                    recipient=farmer,
                    defaults={"distance_km": round(distance, 3)},
                )
