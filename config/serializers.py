from rest_framework import serializers

from core.validators.email import validate_email_address
from .models import (
    User, Content, ContentSection, TeamMember, Fellowship,
    Internship, Publication, Seminar, Course, Training, News,
    Report, Download, DataCatalogue, DataCatalogueView,
    PolicyBrief, Subscription, ContactForm, RateLimit,
    AuditLog, SystemLog,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class ContentSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentSection
        fields = "__all__"


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = "__all__"


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = "__all__"


class FellowshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fellowship
        fields = "__all__"


class InternshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Internship
        fields = "__all__"


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = "__all__"


class SeminarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seminar
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"


class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = "__all__"


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = "__all__"


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"


class DownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Download
        fields = "__all__"


class DataCatalogueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCatalogue
        fields = "__all__"


class DataCatalogueViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCatalogueView
        fields = "__all__"


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