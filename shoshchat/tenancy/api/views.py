"""Tenant API views."""
from __future__ import annotations

from rest_framework import generics, permissions

from tenancy.models import Tenant
from .serializers import TenantSerializer


class TenantCreateView(generics.CreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.AllowAny]
