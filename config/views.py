from rest_framework import viewsets

from core.permissions import (
    PublicReadEditorWrite,
    PublicReadAdminWrite,
    PublicReadAuthCreate,
    AuthenticatedReadAdminWrite,
    IsAdmin,
)
from .models import (
    User, Content, ContentSection, TeamMember, Fellowship,
    Internship, Publication, Seminar, Course, Training, News,
    Report, Download, DataCatalogue, DataCatalogueView,
    PolicyBrief, Subscription, ContactForm, RateLimit,
    AuditLog, SystemLog,
)
from .serializers import (
    UserSerializer, ContentSerializer, ContentSectionSerializer,
    TeamMemberSerializer, FellowshipSerializer, InternshipSerializer,
    PublicationSerializer, SeminarSerializer, CourseSerializer,
    TrainingSerializer, NewsSerializer, ReportSerializer,
    DownloadSerializer, DataCatalogueSerializer, DataCatalogueViewSerializer,
    PolicyBriefSerializer, SubscriptionSerializer, ContactFormSerializer,
    RateLimitSerializer, AuditLogSerializer, SystemLogSerializer,
)

# ---------------------------------------------------------------------------
# Permission matrix
#
# PublicReadEditorWrite     GET: anyone | POST/PUT/PATCH: editor+ | DELETE: admin
# PublicReadAdminWrite      GET: anyone | all writes: admin
# PublicReadAuthCreate      GET: anyone | POST: authenticated | PUT/PATCH/DELETE: admin
# AuthenticatedReadAdminWrite  GET: authenticated | writes: admin
# IsAdmin                   everything: admin only
# ---------------------------------------------------------------------------


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    search_fields = ["name", "email"]
    ordering = ["-created_at"]


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.select_related("author").all()
    serializer_class = ContentSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["type", "status", "featured", "category"]
    search_fields = ["title", "excerpt"]
    ordering_fields = ["date", "published_at", "created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        raci_user = getattr(self.request, "raci_user", None)
        if raci_user and raci_user.is_authenticated:
            try:
                author = User.objects.get(id=raci_user.user_id)
                serializer.save(author=author)
                return
            except User.DoesNotExist:
                pass
        serializer.save()


class ContentSectionViewSet(viewsets.ModelViewSet):
    queryset = ContentSection.objects.select_related("content").all()
    serializer_class = ContentSectionSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["content"]
    ordering = ["order"]


class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["department", "featured", "alumni", "status", "is_active", "in_team"]
    search_fields = ["name", "role", "title"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class FellowshipViewSet(viewsets.ModelViewSet):
    queryset = Fellowship.objects.select_related("team_member").all()
    serializer_class = FellowshipSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["type", "status", "year", "institution"]
    search_fields = ["name", "topic"]
    ordering_fields = ["year", "created_at"]
    ordering = ["-year"]


class InternshipViewSet(viewsets.ModelViewSet):
    queryset = Internship.objects.all()
    serializer_class = InternshipSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["status", "year", "country"]
    search_fields = ["name", "university", "internship_position"]
    ordering_fields = ["year", "created_at"]
    ordering = ["-year"]


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["publication_type", "publication_year", "category"]
    search_fields = ["title", "abstract", "journal"]
    ordering_fields = ["publication_year", "date_published", "created_at"]
    ordering = ["-publication_year"]


class SeminarViewSet(viewsets.ModelViewSet):
    queryset = Seminar.objects.all()
    serializer_class = SeminarSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["upcoming", "featured"]
    search_fields = ["title", "author", "description"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-created_at"]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["upcoming"]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-created_at"]


class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["upcoming", "category"]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-created_at"]


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["featured"]
    search_fields = ["title", "excerpt", "body"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-created_at"]


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["type", "is_public", "year_published"]
    search_fields = ["title", "description"]
    ordering_fields = ["year_published", "date_published", "created_at"]
    ordering = ["-created_at"]


class DownloadViewSet(viewsets.ModelViewSet):
    queryset = Download.objects.select_related("report").all()
    serializer_class = DownloadSerializer
    permission_classes = [AuthenticatedReadAdminWrite]
    filterset_fields = ["report"]
    ordering = ["-created_at"]


class DataCatalogueViewSet(viewsets.ModelViewSet):
    queryset = DataCatalogue.objects.all()
    serializer_class = DataCatalogueSerializer
    permission_classes = [PublicReadEditorWrite]
    filterset_fields = ["category", "is_public", "is_featured", "year"]
    search_fields = ["title", "description"]
    ordering_fields = ["year", "downloads", "created_at"]
    ordering = ["-created_at"]


class DataCatalogueViewViewSet(viewsets.ModelViewSet):
    queryset = DataCatalogueView.objects.select_related("item").all()
    serializer_class = DataCatalogueViewSerializer
    permission_classes = [AuthenticatedReadAdminWrite]
    filterset_fields = ["item"]
    ordering = ["-created_at"]


class PolicyBriefViewSet(viewsets.ModelViewSet):
    queryset = PolicyBrief.objects.all()
    serializer_class = PolicyBriefSerializer
    permission_classes = [PublicReadEditorWrite]
    search_fields = ["title", "summary", "findings"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]


class SubscriptionViewSet(viewsets.ModelViewSet):
    """POST open to anyone. Manage (GET/PUT/DELETE) is admin only."""
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [PublicReadAuthCreate]
    ordering = ["-created_at"]


class ContactFormViewSet(viewsets.ModelViewSet):
    """POST open to anyone. Manage (GET/PUT/DELETE) is admin only."""
    queryset = ContactForm.objects.all()
    serializer_class = ContactFormSerializer
    permission_classes = [PublicReadAuthCreate]
    filterset_fields = ["is_read"]
    search_fields = ["full_name", "email", "subject"]
    ordering = ["-created_at"]


class RateLimitViewSet(viewsets.ModelViewSet):
    queryset = RateLimit.objects.all()
    serializer_class = RateLimitSerializer
    permission_classes = [IsAdmin]
    ordering = ["-created_at"]


class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [AuthenticatedReadAdminWrite]
    filterset_fields = ["action", "resource", "success"]
    search_fields = ["user_email", "resource_id", "route"]
    ordering = ["-created_at"]


class SystemLogViewSet(viewsets.ModelViewSet):
    queryset = SystemLog.objects.all()
    serializer_class = SystemLogSerializer
    permission_classes = [AuthenticatedReadAdminWrite]
    filterset_fields = ["level", "component"]
    search_fields = ["message", "component"]
    ordering = ["-created_at"]