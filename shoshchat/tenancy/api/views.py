"""Tenant API views."""
from __future__ import annotations

from django.http import Http404
from rest_framework import generics, mixins, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from tenancy.models import Domain, Tenant
from .serializers import (
    DomainSerializer,
    TenantDetailSerializer,
    TenantSerializer,
    TenantSettingsSerializer,
)


class TenantCreateView(generics.CreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.AllowAny]


class TenantDetailView(generics.RetrieveAPIView):
    serializer_class = TenantDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        tenant = Tenant.objects.filter(owner=self.request.user).first()
        if not tenant:
            raise Http404("Tenant not found")
        return tenant


class TenantSettingsView(mixins.UpdateModelMixin, generics.GenericAPIView):
    serializer_class = TenantSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        tenant = Tenant.objects.filter(owner=self.request.user).first()
        if not tenant:
            raise Http404("Tenant not found")
        return tenant

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class TenantDomainView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        tenant = Tenant.objects.filter(owner=request.user).first()
        if tenant is None:
            raise Http404("Tenant not found")
        serializer = DomainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain, _ = Domain.objects.update_or_create(
            tenant=tenant,
            domain=serializer.validated_data["domain"].lower(),
            defaults={"is_primary": serializer.validated_data.get("is_primary", False)},
        )
        if domain.is_primary:
            Domain.objects.filter(tenant=tenant).exclude(pk=domain.pk).update(is_primary=False)
        return Response(DomainSerializer(domain).data)


class TenantEmbedCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tenant = Tenant.objects.filter(owner=request.user).first()
        if tenant is None:
            raise Http404("Tenant not found")
        script = (
            "<script src=\"https://app.shoshchat.ai/widget-loader.js\" async></script>\n"
            "<script>\n"
            "  window.ShoshChatWidget = window.ShoshChatWidget || {};\n"
            "  window.ShoshChatWidget.init({\n"
            f"    tenantId: '{tenant.schema_name}',\n"
            f"    accent: '{tenant.widget_accent}'\n"
            "  });\n"
            "</script>"
        )
        return Response({"embed_code": script})
