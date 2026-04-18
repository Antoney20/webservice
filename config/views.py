import json
import uuid

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from django.db import IntegrityError
from core.caches.content import  get_content_list, set_content_list, invalidate_content_list, get_content_item, set_content_item, invalidate_content_item, invalidate_content
from core.caches.seminars import get_seminar_item, set_seminar_item, get_seminar_list, invalidate_seminar, set_seminar_list
from core.caches.internships import (
    get_internship_list, set_internship_list,
    get_internship_item, set_internship_item,
    invalidate_internship,
)

from core.permissions import AnonPostOnly, EditorWrite, IsAuthenticated, PublicReadOnly, RequiresAdmin
from django.db.models import Count, Sum

from .models import (
    TrainingMedia, TrainingSection, User, Content, ContentSection, TeamMember, Fellowship,
    Internship, Publication, Seminar, Course, Training, News,
    Report, Download, DataCatalogue, DataCatalogueView,
    PolicyBrief, Subscription, ContactForm, RateLimit,
    AuditLog, SystemLog,
)
from .serializers import (
    ContentListSerializer, PublicationListSerializer, TrainingListSerializer, TrainingMediaSerializer, TrainingSectionSerializer, UserSerializer, ContentSerializer, ContentSectionSerializer,
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
    queryset           = User.objects.all().order_by("-created_at")
    serializer_class   = UserSerializer
    permission_classes = [RequiresAdmin]
    filterset_fields   = ["role", "is_active", "is_staff"]
    search_fields      = ["name", "email"]
    ordering_fields    = ["name", "email", "created_at", "role"]
    ordering           = ["-created_at"]

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            obj = User.objects.get(pk=pk)
        except User.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return ok(data=self.get_paginated_response(serializer.data).data)
        return ok(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance   = self.get_object()
        serializer = self.get_serializer(instance)
        return ok(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            serializer.save()
        except IntegrityError:
            return fail(message="User with this email already exists.")
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            serializer.save()
        except IntegrityError:
            return fail(message="Email already in use.")
        return ok(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Prevent deleting yourself
        if instance.pk == request.user.pk:
            return fail(message="You cannot delete your own account.")
        instance.delete()
        return ok(message="User deleted.")

class ContentViewSet(viewsets.ModelViewSet):
    queryset           = Content.objects.all()
    permission_classes = [EditorWrite]
    filterset_fields   = ["type", "status", "featured", "category"]
    search_fields      = ["title", "excerpt"]
    ordering_fields    = ["date", "published_at", "created_at"]
    ordering           = ["-created_at"]

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            obj = self.get_queryset().get(pk=pk)
        except Content.DoesNotExist:
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_class(self):
        if self.action == "list":
            return ContentListSerializer
        return ContentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action != "list":
            qs = qs.prefetch_related("sections")
        return qs

    def _parse_sections(self):
        sections_data = self.request.data.get("sections", [])
        if isinstance(sections_data, str):
            try:
                sections_data = json.loads(sections_data)
            except (json.JSONDecodeError, ValueError):
                sections_data = []
        return sections_data if isinstance(sections_data, list) else []

    def _save_sections(self, instance, sections_data):
        instance.sections.all().delete()
        for section in sections_data:
            if not section.get("body", "").strip():
                continue
            ContentSection.objects.create(
                content=instance,
                title=section.get("title") or None,
                body=section.get("body", ""),
                order=section.get("order", 0),
                image_alt=section.get("image_alt") or None,
            )

    # ── List ──────────────────────────────────────────────────────────────

    def list(self, request, *args, **kwargs):
        cached = get_content_list()
        if cached is not None:
            return ok(data=cached)
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        data       = self.get_paginated_response(serializer.data).data if page is not None else serializer.data
        set_content_list(data)
        return ok(data=data)

    # ── Retrieve ──────────────────────────────────────────────────────────

    def retrieve(self, request, *args, **kwargs):
        pk     = self.kwargs.get("pk")
        cached = get_content_item(pk)
        if cached is not None:
            return ok(data=cached)
        instance   = self.get_object()
        serializer = self.get_serializer(instance)
        data       = serializer.data
        set_content_item(pk, data)
        return ok(data=data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            instance = serializer.save(created_by=request.user)
            self._save_sections(instance, self._parse_sections())
            invalidate_content()
        except IntegrityError as e:
            return fail(message="Failed to create content.")
        except Exception as e:
            return fail(message=str(e))
        # Return fresh instance with sections
        out = self.get_serializer(
            Content.objects.prefetch_related("sections").get(pk=instance.pk)
        )
        return ok(data=out.data)


    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            instance = serializer.save()
            self._save_sections(instance, self._parse_sections())
            invalidate_content(pk=str(instance.pk))
        except IntegrityError:
            return fail(message="Failed to update content.")
        except Exception as e:
            return fail(message=str(e))
        # Return fresh instance with sections
        out = self.get_serializer(
            Content.objects.prefetch_related("sections").get(pk=instance.pk)
        )
        return ok(data=out.data)


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        pk       = instance.pk
        instance.delete()
        invalidate_content(pk=pk)
        return ok()

# from config.models import Content
class ContentSectionViewSet(viewsets.ModelViewSet):
    serializer_class   = ContentSectionSerializer
    permission_classes = [EditorWrite]

    def get_queryset(self):
        return ContentSection.objects.filter(
            content_id=self.kwargs["content_pk"]
        ).order_by("order")

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            obj = ContentSection.objects.get(pk=pk)
        except ContentSection.DoesNotExist:
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        content = Content.objects.get(pk=self.kwargs["content_pk"])
        serializer.save(content=content)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
            invalidate_content(pk=self.kwargs["content_pk"])  # bust cache
        except Exception as e:
            return fail(message=str(e))
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_update(serializer)
            invalidate_content(pk=str(instance.content_id))  # bust cache
        except Exception as e:
            return fail(message=str(e))
        return ok(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        content_pk = str(instance.content_id)
        instance.delete()
        invalidate_content(pk=content_pk)  # bust cache
        return ok()


class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset           = TeamMember.objects.select_related("created_by").all()
    serializer_class   = TeamMemberSerializer
    permission_classes = [EditorWrite]
    filterset_fields   = ["department", "featured", "alumni", "status", "is_active", "in_team", "is_fellow"]
    search_fields      = ["name", "role", "title", "department"]
    ordering_fields    = ["name", "created_at", "department"]
    ordering           = ["name"]

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            # Try integer first (existing rows seeded with int IDs)
            obj = TeamMember.objects.get(pk=int(pk))
        except (ValueError, TypeError):
            # Fall back to UUID for new rows
            try:
                obj = TeamMember.objects.get(pk=uuid.UUID(pk))
            except (ValueError, TeamMember.DoesNotExist):
                from rest_framework.exceptions import NotFound
                raise NotFound()
        except TeamMember.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj


    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create team member.")
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_update(serializer)
        except IntegrityError:
            return fail(message="Failed to update team member.")
        return ok(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return ok(message="Team member deleted.")

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return ok(data=self.get_paginated_response(serializer.data).data)
        return ok(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance   = self.get_object()
        serializer = self.get_serializer(instance)
        return ok(data=serializer.data)


class FellowshipViewSet(viewsets.ModelViewSet):
    queryset           = Fellowship.objects.select_related("team_member", "created_by").all()
    serializer_class   = FellowshipSerializer
    permission_classes = [EditorWrite]
    filterset_fields   = ["type", "status", "year", "institution"]
    search_fields      = ["name", "topic", "institution", "mentor"]
    ordering_fields    = ["year", "created_at", "name"]
    ordering           = ["-year"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            obj = Fellowship.objects.select_related("team_member", "created_by").get(pk=pk)
        except Fellowship.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return ok(data=self.get_paginated_response(serializer.data).data)
        return ok(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            serializer.save(created_by=request.user)
        except IntegrityError:
            return fail(message="Failed to create fellowship.")
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            new_image = request.FILES.get("image")
            if new_image and instance.image:
                instance.image.delete(save=False)
            serializer.save()
        except IntegrityError:
            return fail(message="Failed to update fellowship.")
        return ok(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.image:
            instance.image.delete(save=False)
        instance.delete()
        return ok(message="Fellowship deleted.")




class InternshipViewSet(viewsets.ModelViewSet):
    queryset           = Internship.objects.select_related("team_member", "created_by").order_by("-year")
    serializer_class   = InternshipSerializer
    permission_classes = [EditorWrite]
    filterset_fields   = ["status", "year", "country", "team_member"]
    search_fields      = ["name", "university", "internship_position", "country"]
    ordering_fields    = ["year", "created_at", "name"]
    ordering           = ["-year"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            obj = Internship.objects.select_related(
                "team_member", "created_by"
            ).get(pk=uuid.UUID(pk))
        except (ValueError, Internship.DoesNotExist):
            from rest_framework.exceptions import NotFound
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        cached = get_internship_list()
        if cached is not None:
            return ok(data=cached)

        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(
            page if page is not None else qs,
            many=True,
            context={"request": request},
        )
        result = self.get_paginated_response(serializer.data).data if page is not None else serializer.data
        set_internship_list(result)
        return ok(data=result)

    def retrieve(self, request, *args, **kwargs):
        pk     = self.kwargs.get("pk")
        cached = get_internship_item(pk)
        if cached is not None:
            return ok(data=cached)

        instance   = self.get_object()
        serializer = self.get_serializer(instance, context={"request": request})
        set_internship_item(pk, serializer.data)
        return ok(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            serializer.save(created_by=request.user)
            invalidate_internship()
        except IntegrityError:
            return fail(message="Failed to create internship.")
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            serializer.save()
            invalidate_internship(pk=str(instance.pk))
        except IntegrityError:
            return fail(message="Failed to update internship.")
        return ok(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        pk       = str(instance.pk)
        instance.delete()
        invalidate_internship(pk=pk)
        return ok(message="Internship deleted.")
    
class PublicationViewSet(viewsets.ModelViewSet):
    queryset         = Publication.objects.select_related("created_by").all()
    serializer_class = PublicationSerializer
    permission_classes = [EditorWrite]
    filterset_fields = ["publication_type", "publication_year", "category"]
    search_fields    = ["title", "abstract", "journal"]
    ordering_fields  = ["publication_year", "date_published", "created_at"]
    ordering         = ["-publication_year"]


    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            obj = Publication.objects.get(pk=pk)
        except Publication.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj


    def get_serializer_class(self):
        if self.action == "list":
            return PublicationListSerializer
        return PublicationSerializer
    
    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return fail(message="Failed to create publication.")
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self.perform_update(serializer)
        except IntegrityError:
            return fail(message="Failed to update publication.")
        return ok(data=serializer.data)


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return ok()




class SeminarViewSet(viewsets.ModelViewSet):
    queryset           = Seminar.objects.order_by("-created_at")
    serializer_class   = SeminarSerializer
    permission_classes = [EditorWrite]
    filterset_fields   = ["upcoming", "featured"]
    search_fields      = ["title", "author", "description"]
    ordering_fields    = ["date", "created_at", "title"]
    ordering           = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            obj = Seminar.objects.get(pk=pk)
        except Seminar.DoesNotExist:
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        cached = get_seminar_list()
        if cached is not None:
            return ok(data=cached)
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        data       = self.get_paginated_response(serializer.data).data if page is not None else serializer.data
        set_seminar_list(data)
        return ok(data=data)

    def retrieve(self, request, *args, **kwargs):
        pk     = self.kwargs.get("pk")
        cached = get_seminar_item(pk)
        if cached is not None:
            return ok(data=cached)
        instance   = self.get_object()
        serializer = self.get_serializer(instance)
        set_seminar_item(pk, serializer.data)
        return ok(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            serializer.save(created_by=request.user)
            invalidate_seminar()
        except IntegrityError:
            return fail(message="Failed to create seminar.")
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            if request.FILES.get("image") and instance.image:
                instance.image.delete(save=False)
            serializer.save()
            invalidate_seminar(pk=str(instance.pk))
        except IntegrityError:
            return fail(message="Failed to update seminar.")
        return ok(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        pk       = instance.pk
        if instance.image:
            instance.image.delete(save=False)
        instance.delete()
        invalidate_seminar(pk=str(pk))
        return ok()

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
    queryset           = Training.objects.select_related("created_by").prefetch_related("sections", "media").order_by("-created_at")
    permission_classes = [EditorWrite]
    filterset_fields   = ["upcoming", "category", "featured", "mode"]
    search_fields      = ["title", "description", "location", "category"]
    ordering_fields    = ["date", "created_at", "title"]
    ordering           = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return TrainingListSerializer
        return TrainingSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "list":
            return qs.prefetch_related(None)   
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            obj = Training.objects.prefetch_related("sections", "media").get(pk=uuid.UUID(pk))
        except (ValueError, Training.DoesNotExist):
            try:
                obj = Training.objects.prefetch_related("sections", "media").get(pk=int(pk))
            except (ValueError, Training.DoesNotExist):
                from rest_framework.exceptions import NotFound
                raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return ok(data=self.get_paginated_response(serializer.data).data)
        return ok(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            instance = serializer.save(created_by=request.user)
            self._sync_sections(instance, request.data.get("sections"))
            self._sync_media(instance, request)
        except IntegrityError:
            return fail(message="Failed to create training.")
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            instance = serializer.save()
            self._sync_sections(instance, request.data.get("sections"))
            self._sync_media(instance, request)
        except IntegrityError:
            return fail(message="Failed to update training.")
        return ok(data=self.get_serializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Clean up media files
        for m in instance.media.all():
            if m.file:
                m.file.delete(save=False)
        for s in instance.sections.all():
            if s.image:
                s.image.delete(save=False)
        instance.delete()
        return ok(message="Training deleted.")

    def _sync_sections(self, instance, sections_json):
        """Replace sections from JSON payload."""
        if sections_json is None:
            return
        import json as _json
        try:
            sections = _json.loads(sections_json) if isinstance(sections_json, str) else sections_json
        except (ValueError, TypeError):
            return
        instance.sections.all().delete()
        for i, s in enumerate(sections):
            TrainingSection.objects.create(
                training  = instance,
                title     = s.get("title") or None,
                body      = s.get("body", ""),
                order     = s.get("order", i),
                image_alt = s.get("image_alt") or None,
            )

    def _sync_media(self, instance, request):
        """Handle media_<n>_file uploads and media_<n>_url entries from FormData."""
        import json as _json
        media_meta_raw = request.data.get("media_meta")
        if not media_meta_raw:
            return
        try:
            meta_list = _json.loads(media_meta_raw) if isinstance(media_meta_raw, str) else media_meta_raw
        except (ValueError, TypeError):
            return

        instance.media.all().delete()
        for i, meta in enumerate(meta_list):
            file_key = f"media_{i}_file"
            file_obj = request.FILES.get(file_key)
            TrainingMedia.objects.create(
                training   = instance,
                media_type = meta.get("media_type", "DOCUMENT"),
                title      = meta.get("title") or None,
                file       = file_obj,
                url        = meta.get("url") or None,
                order      = i,
            )


class TrainingSectionViewSet(viewsets.ModelViewSet):
    queryset           = TrainingSection.objects.select_related("training").all()
    serializer_class   = TrainingSectionSerializer
    permission_classes = [EditorWrite]
    filterset_fields   = ["training"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)
        return ok(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        serializer.save()
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        serializer.save()
        return ok(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.image:
            instance.image.delete(save=False)
        instance.delete()
        return ok(message="Section deleted.")


class TrainingMediaViewSet(viewsets.ModelViewSet):
    queryset           = TrainingMedia.objects.select_related("training").all()
    serializer_class   = TrainingMediaSerializer
    permission_classes = [EditorWrite]
    filterset_fields   = ["training", "media_type"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)
        return ok(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        serializer.save()
        return ok_created()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.file:
            instance.file.delete(save=False)
        instance.delete()
        return ok(message="Media deleted.")

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
    queryset           = Report.objects.select_related("created_by").annotate(
                             download_count=Count("downloads")
                         ).order_by("-created_at")
    serializer_class   = ReportSerializer
    permission_classes = [EditorWrite]
    filterset_fields   = ["type", "is_public", "year_published"]
    search_fields      = ["title", "description", "tags", "keywords"]
    ordering_fields    = ["title", "year_published", "created_at", "download_count"]
    ordering           = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            obj = Report.objects.annotate(download_count=Count("downloads")).get(pk=pk)
        except Report.DoesNotExist:
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return ok(data=self.get_paginated_response(serializer.data).data)
        return ok(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            self._save_with_file_meta(serializer, created_by=request.user)
        except Exception as e:
            return fail(message=str(e))
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            if request.data.get("file") and instance.file:
                instance.file.delete(save=False)
            self._save_with_file_meta(serializer)
        except Exception as e:
            return fail(message=str(e))
        return ok(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.file:
            instance.file.delete(save=False)
        instance.delete()
        return ok()

    def _save_with_file_meta(self, serializer, **kwargs):
        file = serializer.validated_data.get("file")
        if file:
            kwargs["file_size"] = file.size
            kwargs["file_type"] = getattr(file, "content_type", None)
            if not serializer.validated_data.get("file_name"):
                kwargs["file_name"] = file.name
        serializer.save(**kwargs)


class DownloadViewSet(viewsets.ModelViewSet):
    queryset           = Download.objects.select_related("report").order_by("-created_at")
    serializer_class   = DownloadSerializer
    permission_classes = [AnonPostOnly]
    filterset_fields   = ["report"]
    ordering           = ["-created_at"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        ip = get_client_ip(request)
        serializer.save(user_id=str(request.user.pk) if request.user.is_authenticated else None)
        return ok_created()

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return ok(data=self.get_paginated_response(serializer.data).data)
        return ok(data=serializer.data)


class DataCatalogueViewSet(viewsets.ModelViewSet):
    queryset           = DataCatalogue.objects.annotate(
                             view_count=Count("views")
                         ).order_by("-created_at")
    serializer_class   = DataCatalogueSerializer
    permission_classes = [EditorWrite]
    filterset_fields   = ["category", "is_public", "is_featured", "year"]
    search_fields      = ["title", "description", "tags"]
    ordering_fields    = ["year", "downloads", "created_at", "view_count"]
    ordering           = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return super().get_permissions()

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            obj = DataCatalogue.objects.annotate(view_count=Count("views")).get(pk=pk)
        except DataCatalogue.DoesNotExist:
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return ok(data=self.get_paginated_response(serializer.data).data)
        return ok(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Auto-record view on retrieve
        ip = get_client_ip(request)
        if ip:
            DataCatalogueView.objects.get_or_create(
                item=instance,
                ip_address=ip,
                defaults={"user_agent": request.META.get("HTTP_USER_AGENT", "")},
            )
        return ok(data=self.get_serializer(instance).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            serializer.save(created_by=request.user)
        except IntegrityError:
            return fail(message="Failed to create data catalogue entry.")
        return ok_created()

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop("partial", False)
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return fail(errors=serializer.errors)
        try:
            serializer.save()
        except IntegrityError:
            return fail(message="Failed to update data catalogue entry.")
        return ok(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.image:
            instance.image.delete(save=False)
        instance.delete()
        return ok()


class DataCatalogueViewViewSet(viewsets.ModelViewSet):
    queryset           = DataCatalogueView.objects.select_related("item").order_by("-created_at")
    serializer_class   = DataCatalogueViewSerializer
    permission_classes = [PublicReadOnly]
    filterset_fields   = ["item"]
    ordering           = ["-created_at"]

    def get_permissions(self):
        if self.action in ("create", "list", "retrieve"):
            return []
        return [RequiresAdmin()]

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return ok(data=self.get_paginated_response(serializer.data).data)
        return ok(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return ok(data=self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            if "non_field_errors" in serializer.errors:
                return ok()  # already viewed
            return fail(errors=serializer.errors)
        ip = get_client_ip(request)
        try:
            serializer.save(ip_address=ip)
        except IntegrityError:
            return ok()  # already viewed
        return ok_created()

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return ok()

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