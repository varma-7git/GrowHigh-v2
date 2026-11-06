import logging

from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("growhigh.health")


class HealthView(APIView):
    """GET /health/  Used by uptime monitors and the deployment health check. No login needed."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
            return Response({"status": "ok", "database": "ok"})
        except Exception:  # database unreachable
            logger.exception("Health check failed: database unreachable")
            return Response({"status": "error", "database": "down"}, status=503)
