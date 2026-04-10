"""
Geo-tagging and Alert Service
Handles location-based services for ICHS
"""

import logging
from typing import Dict, List, Tuple
from geopy.distance import geodesic
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class GeoAlertService:
    """Service for geo-tagging reports and sending alerts"""

    def __init__(self, alert_radius_km: float = 10.0):
        """
        Initialize GeoAlertService

        Args:
            alert_radius_km: Radius in km for sending alerts to neighboring farmers
        """
        self.alert_radius_km = alert_radius_km
        self.reports = []  # In production, use a database
        logger.info(f"GeoAlertService initialized with {alert_radius_km}km radius")

    def add_report(self, location: Tuple[float, float],
                   disease: str, confidence: float,
                   farmer_id: str = None) -> str:
        """
        Add a new disease report with geo-tagging

        Args:
            location: Tuple of (latitude, longitude)
            disease: Predicted disease name
            confidence: Prediction confidence score
            farmer_id: Unique farmer identifier

        Returns:
            Report ID
        """
        report_id = f"report_{len(self.reports) + 1}"
        report = {
            "id": report_id,
            "location": location,
            "disease": disease,
            "confidence": confidence,
            "farmer_id": farmer_id,
            "timestamp": datetime.now().isoformat(),
            "alerts_sent": []
        }

        self.reports.append(report)
        logger.info(f"Added report {report_id} for disease {disease}")

        # Send alerts to nearby farmers
        self._send_alerts(report)

        return report_id

    def _send_alerts(self, report: Dict):
        """
        Send alerts to farmers within the alert radius

        Args:
            report: Disease report dictionary
        """
        report_location = report["location"]
        disease = report["disease"]

        nearby_farmers = self._find_nearby_farmers(report_location)

        for farmer in nearby_farmers:
            alert = {
                "to_farmer": farmer["id"],
                "from_report": report["id"],
                "disease": disease,
                "location": report_location,
                "distance_km": farmer["distance"],
                "timestamp": datetime.now().isoformat()
            }

            # In production, send actual notifications (SMS, push, etc.)
            logger.info(f"Alert sent to farmer {farmer['id']}: {disease} detected {farmer['distance']:.1f}km away")
            report["alerts_sent"].append(alert)

    def _find_nearby_farmers(self, location: Tuple[float, float]) -> List[Dict]:
        """
        Find farmers within alert radius
        Note: In production, query from farmer database

        Args:
            location: Center location (lat, lng)

        Returns:
            List of nearby farmers with distances
        """
        # Mock farmer locations - in production, query database
        mock_farmers = [
            {"id": "farmer_001", "location": (location[0] + 0.05, location[1] + 0.05)},
            {"id": "farmer_002", "location": (location[0] - 0.03, location[1] - 0.03)},
            {"id": "farmer_003", "location": (location[0] + 0.08, location[1] - 0.02)},
        ]

        nearby = []
        for farmer in mock_farmers:
            distance = geodesic(location, farmer["location"]).km
            if distance <= self.alert_radius_km:
                nearby.append({
                    "id": farmer["id"],
                    "distance": distance
                })

        return nearby

    def get_reports_in_area(self, center: Tuple[float, float],
                           radius_km: float) -> List[Dict]:
        """
        Get all disease reports within a given area

        Args:
            center: Center location (lat, lng)
            radius_km: Search radius in km

        Returns:
            List of reports in the area
        """
        reports_in_area = []

        for report in self.reports:
            distance = geodesic(center, report["location"]).km
            if distance <= radius_km:
                report_copy = report.copy()
                report_copy["distance_from_center"] = distance
                reports_in_area.append(report_copy)

        return reports_in_area

    def get_alert_history(self, farmer_id: str) -> List[Dict]:
        """
        Get alert history for a specific farmer

        Args:
            farmer_id: Farmer identifier

        Returns:
            List of alerts received by the farmer
        """
        alerts = []

        for report in self.reports:
            for alert in report.get("alerts_sent", []):
                if alert["to_farmer"] == farmer_id:
                    alerts.append(alert)

        return alerts


if __name__ == "__main__":
    service = GeoAlertService()

    # Example usage
    report_id = service.add_report(
        location=(12.9716, 77.5946),  # Bangalore coordinates
        disease="Late Blight",
        confidence=0.85,
        farmer_id="farmer_123"
    )

    print(f"Report added: {report_id}")

    # Get reports in area
    reports = service.get_reports_in_area((12.9716, 77.5946), 15.0)
    print(f"Reports in area: {len(reports)}")
