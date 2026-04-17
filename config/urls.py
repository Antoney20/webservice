from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'users',               views.UserViewSet,              basename='user')
router.register(r'content',             views.ContentViewSet,           basename='content')
router.register(r'content-sections',    views.ContentSectionViewSet,    basename='content-section')
router.register(r'team-members',        views.TeamMemberViewSet,        basename='team-member')
router.register(r'fellowships',         views.FellowshipViewSet,        basename='fellowship')
router.register(r'internships',         views.InternshipViewSet,        basename='internship')
router.register(r'publications',        views.PublicationViewSet,       basename='publication')
router.register(r'seminars',            views.SeminarViewSet,           basename='seminar')
router.register(r'courses',             views.CourseViewSet,            basename='course')
router.register(r"trainings",         views.TrainingViewSet)
router.register(r"training-sections", views.TrainingSectionViewSet)
router.register(r"training-media",    views.TrainingMediaViewSet)
router.register(r'news',                views.NewsViewSet,              basename='news')
router.register(r'reports',             views.ReportViewSet,            basename='report')
router.register(r'downloads',           views.DownloadViewSet,          basename='download')
router.register(r'data-catalogue',      views.DataCatalogueViewSet,     basename='data-catalogue')
router.register(r'data-catalogue-views',views.DataCatalogueViewViewSet, basename='data-catalogue-view')
router.register(r'policy-briefs',       views.PolicyBriefViewSet,       basename='policy-brief')
router.register(r'subscriptions',       views.SubscriptionViewSet,      basename='subscription')
router.register(r'contact-forms',       views.ContactFormViewSet,      basename='contact-form')
router.register(r'rate-limits',         views.RateLimitViewSet,         basename='rate-limit')
router.register(r'audit-logs',          views.AuditLogViewSet,          basename='audit-log')
router.register(r'system-logs',         views.SystemLogViewSet,         basename='system-log')

urlpatterns = [
    path('', include(router.urls)),
]