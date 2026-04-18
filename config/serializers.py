import json

from rest_framework import serializers
from django.db import IntegrityError
from rest_framework.response import Response

from core.validators.email import validate_email_address
from core.validators.file import validate_file
from .models import (
    TrainingMedia, TrainingSection, User, Content, ContentSection, TeamMember, Fellowship,
    Internship, Publication, Seminar, Course, Training, News,
    Report, Download, DataCatalogue, DataCatalogueView,
    PolicyBrief, Subscription, ContactForm, RateLimit,
    AuditLog, SystemLog,
)


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True, allow_null=True)
    # Write-only password — never returned in responses
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={"input_type": "password"},
    )

    class Meta:
        model  = User
        fields = [
            "id", "email", "name", "role",
            "is_active", "is_staff",
            "last_login",
            "password",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "last_login"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user     = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class ContentSectionSerializer(serializers.ModelSerializer):
    id    = serializers.UUIDField(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True, use_url=True)

    class Meta:
        model  = ContentSection
        fields = "__all__"


class _ContentBase(serializers.ModelSerializer):
    id         = serializers.UUIDField(read_only=True)
    created_by = UserSerializer(read_only=True)
    image      = serializers.ImageField(
                     required=False,
                     allow_null=True,
                     allow_empty_file=True,
                     use_url=True,
                 )

    class Meta:
        model            = Content
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at", "date", "created_by"]

    def validate_image(self, value):
        if not value:
            return None
        return value

    def validate_tags(self, value):
        # Already a list (e.g. from JSON API)
        if isinstance(value, list):
            return value
        # Comma-separated string from FormData e.g. "tag1, tag2"
        if isinstance(value, str):
            # Try JSON first in case it's a stringified array
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            # Fall back to comma-split
            return [t.strip() for t in value.split(',') if t.strip()]
        return []
class ContentListSerializer(_ContentBase):
    """Lightweight — no sections. Used for list()."""
    pass


class ContentSerializer(_ContentBase):
    """Full detail — includes nested sections ordered by `order`."""
    sections = ContentSectionSerializer(many=True, read_only=True)

    class Meta(_ContentBase.Meta):
        pass





class TeamMemberSerializer(serializers.ModelSerializer):
    id         = serializers.UUIDField(read_only=True)
    created_by = UserSerializer(read_only=True)
    image      = serializers.ImageField(
                     required=False,
                     allow_null=True,
                     allow_empty_file=True,
                     use_url=True,
                 )

    class Meta:
        model            = TeamMember
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at", "created_by"]

    def validate_image(self, value):
        if not value:
            return None
        return value

    def validate_specializations(self, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            return [v.strip() for v in value.split(",") if v.strip()]
        return []

    def validate_user_titles(self, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return [v.strip() for v in value.split(",") if v.strip()]
        return []

    def validate_current_research(self, value):
        return self.validate_user_titles(value)


class FellowshipSerializer(serializers.ModelSerializer):
    id          = serializers.UUIDField(read_only=True)
    created_by  = UserSerializer(read_only=True)
    team_member = TeamMemberSerializer(read_only=True)
    team_member_id = serializers.PrimaryKeyRelatedField(
        queryset=TeamMember.objects.all(),
        source="team_member",
        write_only=True,
        required=False,
        allow_null=True,
    )
    image = serializers.ImageField(required=False, allow_null=True, use_url=True)

    class Meta:
        model            = Fellowship
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at", "created_by"]

    def validate_image(self, value):
        if not value:
            return None
        return value

class InternshipSerializer(serializers.ModelSerializer):
    id          = serializers.UUIDField(read_only=True)
    created_by  = UserSerializer(read_only=True)
    team_member = TeamMemberSerializer(read_only=True)
    team_member_id = serializers.PrimaryKeyRelatedField(
        queryset=TeamMember.objects.all(),
        source="team_member",
        write_only=True,
        required=False,
        allow_null=True,
    )
    name = serializers.CharField(read_only=True)

    class Meta:
        model            = Internship
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at", "created_by", "name"]

LIST_FIELDS = [
    "id", "title", "abstract", "journal", "authors", "cema_authors",
    "publication_year", "publication_type", "category", "tags", "url", "updated_at",
]

class PublicationListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Publication
        fields = LIST_FIELDS


class PublicationSerializer(serializers.ModelSerializer):
    id         = serializers.UUIDField(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model            = Publication
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at", "created_by"]

    def validate_tags(self, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            return [t.strip() for t in value.split(",") if t.strip()]
        return []

    def validate_authors(self, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return [v.strip() for v in value.split(",") if v.strip()]
        return []

    def validate_cema_authors(self, value):
        return self.validate_authors(value)

class SeminarSerializer(serializers.ModelSerializer):
    id         = serializers.UUIDField(read_only=True)
    created_by = UserSerializer(read_only=True)
    image      = serializers.ImageField(required=False, allow_null=True, use_url=True)

    class Meta:
        model            = Seminar
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at", "created_by"]

    def validate_image(self, value):
        if not value:
            return None
        return value

    def validate_tags(self, value):
        return _parse_json_list(value)

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"




class TrainingSectionSerializer(serializers.ModelSerializer):
    id    = serializers.UUIDField(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True, use_url=True)

    class Meta:
        model            = TrainingSection
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at"]

    def validate_image(self, value):
        if not value:
            return None
        return value


class TrainingMediaSerializer(serializers.ModelSerializer):
    id   = serializers.UUIDField(read_only=True)
    file = serializers.FileField(required=False, allow_null=True, use_url=True)

    class Meta:
        model            = TrainingMedia
        fields           = "__all__"
        read_only_fields = ["created_at"]

    def validate_file(self, value):
        if not value:
            return None
        validate_file(value, self.context.get("request"))
        return value


class TrainingSerializer(serializers.ModelSerializer):
    id         = serializers.UUIDField(read_only=True)
    created_by = UserSerializer(read_only=True)
    sections   = TrainingSectionSerializer(many=True, read_only=True)
    media      = TrainingMediaSerializer(many=True, read_only=True)

    class Meta:
        model            = Training
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at", "created_by"]

    def validate_tags(self, value):
        return _parse_json_list(value)


class TrainingListSerializer(serializers.ModelSerializer):
    """Lightweight — no sections or media."""
    id         = serializers.UUIDField(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model            = Training
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at", "created_by"]

    def validate_tags(self, value):
        return _parse_json_list(value)


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = "__all__"


class ReportSerializer(serializers.ModelSerializer):
    id             = serializers.UUIDField(read_only=True)
    created_by     = UserSerializer(read_only=True)
    file           = serializers.FileField(required=False, allow_null=True, use_url=True)
    download_count = serializers.SerializerMethodField()

    class Meta:
        model            = Report
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at", "created_by", "file_size", "file_type"]

    def get_download_count(self, obj):
        return getattr(obj, "download_count", obj.downloads.count())

    def validate_file(self, value):
        if not value:
            return None
      
        validate_file(value, self.context.get("request"))
        return value

    def validate_tags(self, value):
        return _parse_json_list(value)

    def validate_keywords(self, value):
        return _parse_json_list(value)


class DownloadSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model            = Download
        fields           = "__all__"
        read_only_fields = ["created_at"]



def _parse_json_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


class DataCatalogueSerializer(serializers.ModelSerializer):
    id         = serializers.CharField(read_only=True)
    created_by = UserSerializer(read_only=True)
    image      = serializers.ImageField(required=False, allow_null=True, use_url=True)
    view_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model            = DataCatalogue
        fields           = "__all__"
        read_only_fields = ["created_at", "updated_at", "created_by", "downloads"]

    def validate_image(self, value):
        return value or None

    def validate_tags(self, value):
        if isinstance(value, list):
            return value

        if isinstance(value, str):
            import json
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass

            return [t.strip() for t in value.split(",") if t.strip()]

        return []

    def to_representation(self, instance):
        data = super().to_representation(instance)

        tags = data.get("tags")

        if isinstance(tags, str):
            import json
            try:
                parsed = json.loads(tags)
                data["tags"] = parsed if isinstance(parsed, list) else []
            except Exception:
                data["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

        return data

class DataCatalogueViewSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model            = DataCatalogueView
        fields           = "__all__"
        read_only_fields = ["created_at"]


class PolicyBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyBrief
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Subscription
        fields = "__all__"

    def validate_email(self, value):
        return validate_email_address(value)


class ContactFormSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ContactForm
        fields = "__all__"

    def validate_email(self, value):
        return validate_email_address(value)

class RateLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateLimit
        fields = "__all__"


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"


class SystemLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemLog
        fields = "__all__"