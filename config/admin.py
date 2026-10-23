from django.contrib import admin
from .models import (
    Career, Invitation, SiteImage, TrainingMedia, TrainingSection, User,
    Content, ContentSection, TeamMember, Fellowship, Internship,
    Publication, Seminar, Course, Training, News, Report, Download,
    DataCatalogue, DataCatalogueView, PolicyBrief, Subscription,
    ContactForm, RateLimit, AuditLog, SystemLog,
)

admin.site.register(Career)
admin.site.register(Invitation)
admin.site.register(SiteImage)
admin.site.register(TrainingMedia)
admin.site.register(TrainingSection)
admin.site.register(User)
admin.site.register(Content)
admin.site.register(ContentSection)
admin.site.register(TeamMember)
admin.site.register(Fellowship)
admin.site.register(Internship)
admin.site.register(Publication)
admin.site.register(Seminar)
admin.site.register(Course)
admin.site.register(Training)
admin.site.register(News)
admin.site.register(Report)
admin.site.register(Download)
admin.site.register(DataCatalogue)
admin.site.register(DataCatalogueView)
admin.site.register(PolicyBrief)
admin.site.register(Subscription)
admin.site.register(ContactForm)
admin.site.register(RateLimit)
admin.site.register(AuditLog)
admin.site.register(SystemLog)