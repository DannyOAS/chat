"""URL patterns for Business API."""
from django.urls import path

from .views import (
    BusinessDetailView,
    InviteTeamMemberView,
    RemoveTeamMemberView,
    TeamMembersListView,
    UpdateTeamMemberRoleView,
)

app_name = "business"

urlpatterns = [
    # Business management
    path("", BusinessDetailView.as_view(), name="business-detail"),
    # Team member management
    path("team/", TeamMembersListView.as_view(), name="team-list"),
    path("team/invite/", InviteTeamMemberView.as_view(), name="team-invite"),
    path("team/<int:member_id>/role/", UpdateTeamMemberRoleView.as_view(), name="team-update-role"),
    path("team/<int:member_id>/", RemoveTeamMemberView.as_view(), name="team-remove"),
]
