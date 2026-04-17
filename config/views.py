from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from core.permissions import AnonPostOnly, EditorWrite, IsAuthenticated, RequiresAdmin

from .models import (
    User, Content, ContentSection, TeamMember, Fellowship,
    Internship, Publication, Seminar, Course, Training, News,
    Report, Download, DataCatalogue, DataCatalogueView,
    PolicyBrief, Subscription, ContactForm, RateLimit,
    AuditLog, SystemLog,
)
from .serializers import (
    ContentListSerializer, UserSerializer, ContentSerializer, ContentSectionSerializer,
    TeamMemberSerializer, FellowshipSerializer, InternshipSerializer,
    PublicationSerializer, SeminarSerializer, CourseSerializer,
    TrainingSerializer, NewsSerializer, ReportSerializer,
    DownloadSerializer, DataCatalogueSerializer, DataCatalogueViewSerializer,
    PolicyBriefSerializer, SubscriptionSerializer, ContactFormSerializer,
    RateLimitSerializer, AuditLogSerializer, SystemLogSerializer,
)


def ok(data=None, status_code=status.HTTP_200_OK):
    body = {"success": True}
    if data is not None:
        body["data"] = data
    return Response(body, status=status_code)


def ok_created():
    return Response({"success": True}, status=status.HTTP_201_CREATED)


def fail(errors=None, message=None, status_code=status.HTTP_400_BAD_REQUEST):
    body = {"success": False}
    if errors:
        body["errors"] = errors
    if message:
        body["message"] = message
    return Response(body, status=status_code)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [RequiresAdmin]
    search_fields = ["name", "email"]
    ordering = ["-created_at"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="User already exists.")
        return ok_created()


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    permission_classes = [EditorWrite]
    filterset_fields = ["type", "status", "featured", "category"]
    search_fields = ["title", "excerpt"]
    ordering_fields = ["date", "published_at", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        # list() → lightweight, no sections
        # retrieve() / create() / update() → full, with nested sections
        if self.action == "list":
            return ContentListSerializer
        return ContentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Prefetch sections only when we'll actually return them
        if self.action != "list":
            qs = qs.prefetch_related("sections")
        return qs

    def perform_create(self, serializer):

        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create content.")
        return ok_created()

class ContentSectionViewSet(viewsets.ModelViewSet):
    queryset = ContentSection.objects.select_related("content").all()
    serializer_class = ContentSectionSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["content"]
    ordering = ["order"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create content section.")
        return ok_created()



class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["department", "featured", "alumni", "status", "is_active", "in_team"]
    search_fields = ["name", "role", "title"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create team member.")
        return ok_created()



class FellowshipViewSet(viewsets.ModelViewSet):
    queryset = Fellowship.objects.select_related("team_member").all()
    serializer_class = FellowshipSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["type", "status", "year", "institution"]
    search_fields = ["name", "topic"]
    ordering_fields = ["year", "created_at"]
    ordering = ["-year"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create fellowship.")
        return ok_created()


class InternshipViewSet(viewsets.ModelViewSet):
    queryset = Internship.objects.all()
    serializer_class = InternshipSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["status", "year", "country"]
    search_fields = ["name", "university", "internship_position"]
    ordering_fields = ["year", "created_at"]
    ordering = ["-year"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create internship.")
        return ok_created()



class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["publication_type", "publication_year", "category"]
    search_fields = ["title", "abstract", "journal"]
    ordering_fields = ["publication_year", "date_published", "created_at"]
    ordering = ["-publication_year"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create publication.")
        return ok_created()



class SeminarViewSet(viewsets.ModelViewSet):
    queryset = Seminar.objects.all()
    serializer_class = SeminarSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["upcoming", "featured"]
    search_fields = ["title", "author", "description"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create seminar.")
        return ok_created()


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["upcoming"]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create course.")
        return ok_created()


class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["upcoming", "category"]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create training.")
        return ok_created()


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["featured"]
    search_fields = ["title", "excerpt", "body"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create news.")
        return ok_created()


# ---------------------------------------------------------------------------
# Reports & Downloads
# ---------------------------------------------------------------------------

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["type", "is_public", "year_published"]
    search_fields = ["title", "description"]
    ordering_fields = ["year_published", "date_published", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create report.")
        return ok_created()


class DownloadViewSet(viewsets.ModelViewSet):
    queryset = Download.objects.select_related("report").all()
    serializer_class = DownloadSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["report"]
    ordering = ["-created_at"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to record download.")
        return ok_created()


# ---------------------------------------------------------------------------
# Data Catalogue
# ---------------------------------------------------------------------------

class DataCatalogueViewSet(viewsets.ModelViewSet):
    queryset = DataCatalogue.objects.all()
    serializer_class = DataCatalogueSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["category", "is_public", "is_featured", "year"]
    search_fields = ["title", "description"]
    ordering_fields = ["year", "downloads", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create data catalogue entry.")
        return ok_created()


class DataCatalogueViewViewSet(viewsets.ModelViewSet):
    queryset = DataCatalogueView.objects.select_related("item").all()
    serializer_class = DataCatalogueViewSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["item"]
    ordering = ["-created_at"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to record catalogue view.")
        return ok_created()


# ---------------------------------------------------------------------------
# Policy Briefs
# ---------------------------------------------------------------------------

class PolicyBriefViewSet(viewsets.ModelViewSet):
    queryset = PolicyBrief.objects.all()
    serializer_class = PolicyBriefSerializer
    permission_classes = [EditorWrite]
    search_fields = ["title", "summary", "findings"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create policy brief.")
        return ok_created()


# ---------------------------------------------------------------------------
# Admin-only
# ---------------------------------------------------------------------------

class RateLimitViewSet(viewsets.ModelViewSet):
    queryset = RateLimit.objects.all()
    serializer_class = RateLimitSerializer
    permission_classes = [RequiresAdmin]
    ordering = ["-created_at"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create rate limit.")
        return ok_created()


class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["action", "resource", "success"]
    search_fields = ["user_email", "resource_id", "route"]
    ordering = ["-created_at"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create audit log.")
        return ok_created()


class SystemLogViewSet(viewsets.ModelViewSet):
    queryset = SystemLog.objects.all()
    serializer_class = SystemLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["level", "component"]
    search_fields = ["message", "component"]
    ordering = ["-created_at"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create system log.")
        return ok_created()


# ---------------------------------------------------------------------------
# Public-submit (Subscription & ContactForm)
# ---------------------------------------------------------------------------

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset           = Subscription.objects.all()
    serializer_class   = SubscriptionSerializer
    permission_classes = [AnonPostOnly]
    ordering           = ["-created_at"]
    http_method_names  = ["post", "get", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve", "destroy"):
            return [RequiresAdmin()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(message="Failed to subscribe.")
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to subscribe.")
        return ok_created()


class ContactFormViewSet(viewsets.ModelViewSet):
    queryset           = ContactForm.objects.all()
    serializer_class   = ContactFormSerializer
    permission_classes = [AnonPostOnly]
    filterset_fields   = ["is_read"]
    search_fields      = ["full_name", "email", "subject"]
    ordering           = ["-created_at"]
    http_method_names  = ["post", "get", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve", "destroy"):
            return [RequiresAdmin()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        self.perform_create(serializer)
        return ok_created()