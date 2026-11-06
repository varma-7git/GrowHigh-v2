"""Every app adds its own urls here (prefix /api/v1/)."""
from django.urls import include, path

from common.health import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("", include("accounts.urls")),
    path("", include("academics.urls")),
    path("", include("jobs.urls")),
    path("", include("exams.urls")),
    # next steps: questions, tests, learning
]
