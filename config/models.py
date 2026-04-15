from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserRole(models.TextChoices):
    ADMIN = "ADMIN"
    USER  = "USER"


class InternshipStatus(models.TextChoices):
    CURRENT   = "CURRENT"
    COMPLETED = "COMPLETED"


class ContentType(models.TextChoices):
    NEWS       = "NEWS"
    BLOG       = "BLOG"
    OPED       = "OPED"
    NEWSLETTER = "NEWSLETTER"
    POLICY     = "POLICY"


class ContentStatus(models.TextChoices):
    DRAFT     = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED  = "ARCHIVED"


class ReportType(models.TextChoices):
    POLICY_BRIEF     = "POLICY_BRIEF"
    REPORT           = "REPORT"
    WORKING_PAPER    = "WORKING_PAPER"
    RESEARCH_SUMMARY = "RESEARCH_SUMMARY"
    PUBLICATION      = "PUBLICATION"
    OTHER            = "OTHER"



class UserManager(BaseUserManager):

    def _create(self, email, password, **extra):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("role", UserRole.USER)
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create(email, password, **extra)

    def create_superuser(self, email, password, **extra):
        extra["role"]         = UserRole.ADMIN
        extra["is_staff"]     = True
        extra["is_superuser"] = True
        return self._create(email, password, **extra)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(AbstractBaseUser, PermissionsMixin):
    """
    First-party user model.  email is the login credential.
    Role-based access (ADMIN / USER) is enforced by DRF permission classes.
    """
    email      = models.EmailField(unique=True, db_index=True)
    name       = models.CharField(max_length=255)
    role       = models.CharField(
                     max_length=20,
                     choices=UserRole.choices,
                     default=UserRole.USER,
                     db_index=True,
                 )
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)   # Django admin access
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"
        indexes  = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.name} <{self.email}>"

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_editor_or_above(self) -> bool:
        # Extend this if you add an EDITOR role later
        return self.role in (UserRole.ADMIN,)


class Content(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=255)
    excerpt = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=ContentType.choices, db_index=True)
    date = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True, db_column="publishedAt")
    status = models.CharField(max_length=20, choices=ContentStatus.choices, default=ContentStatus.DRAFT, db_index=True)
    featured = models.BooleanField(default=False, db_index=True)
    image = models.ImageField(upload_to='site/images/content/', null=True, blank=True)
    image_alt = models.CharField(max_length=255, null=True, blank=True, db_column="imageAlt")
    category = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    tags = models.JSONField(default=list, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contents", db_index=True,  db_column="authorId")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt")

    class Meta:
        db_table = "content"
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["featured"]),
            models.Index(fields=["author"]),
            models.Index(fields=["published_at"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.title


class ContentSection(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="sections", db_index=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    body = models.TextField()
    order = models.IntegerField()
    image = models.ImageField(upload_to='site/images/content/', null=True, blank=True)
    image_alt = models.CharField(max_length=255, null=True, blank=True, db_column="imageAlt")
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt")

    class Meta:
        db_table = "content_sections"
        indexes = [
            models.Index(fields=["content", "order"]),
        ]
        ordering = ["order"]

    def __str__(self):
        return f"{self.content.title} — section {self.order}"



class TeamMember(models.Model):
    # Using AutoField (int) to match Prisma's autoincrement PK
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    role = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=255)
    bio = models.TextField(null=True, blank=True)
    research_interests = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='site/images/people/', null=True, blank=True)
    education = models.TextField(null=True, blank=True)
    department = models.CharField(max_length=255, db_index=True)
    featured = models.BooleanField(default=False, db_index=True)
    alumni = models.BooleanField(default=False, db_index=True)
    specializations = models.JSONField(default=list, blank=True)
    user_titles = models.JSONField(default=list, blank=True)
    current_research = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=50, default="ACTIVE", db_index=True)
    is_active = models.BooleanField(default=True)
    is_fellow = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    in_team = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "team_members"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["role"]),
            models.Index(fields=["department"]),
            models.Index(fields=["featured"]),
            models.Index(fields=["alumni"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Fellowship
# ---------------------------------------------------------------------------

class Fellowship(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    topic = models.CharField(max_length=255)
    type = models.CharField(max_length=100, db_index=True)
    year = models.CharField(max_length=20, db_index=True)
    status = models.CharField(max_length=50, db_index=True)
    mentor = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    institution = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    description = models.TextField(null=True, blank=True)
    funding_source = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='site/images/fellows/', null=True, blank=True)

    # Relationship to TeamMember (nullable — fellow may not be a team member)
    team_member = models.ForeignKey(
        TeamMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fellowships",
        db_index=True,
    )

    # Custom fellow info (when not linked to a TeamMember)
    custom_name = models.CharField(max_length=255, null=True, blank=True)
    custom_title = models.CharField(max_length=255, null=True, blank=True)
    custom_dept = models.CharField(max_length=255, null=True, blank=True)
    custom_email = models.EmailField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fellowships"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["year"]),
            models.Index(fields=["institution"]),
            models.Index(fields=["team_member"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.year})"


class Internship(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    course = models.CharField(max_length=255)
    university = models.CharField(max_length=255)
    country = models.CharField(max_length=100, db_index=True)
    internship_position = models.CharField(max_length=255, db_index=True)
    year = models.CharField(max_length=20, db_index=True)
    status = models.CharField(max_length=20, choices=InternshipStatus.choices, default=InternshipStatus.CURRENT, db_index=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "internships"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["year"]),
            models.Index(fields=["status"]),
            models.Index(fields=["country"]),
            models.Index(fields=["internship_position"]),
        ]

    def __str__(self):
        return f"{self.name} — {self.internship_position}"


# ---------------------------------------------------------------------------
# Publication
# ---------------------------------------------------------------------------

class Publication(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=500, db_index=True)
    abstract = models.TextField(null=True, blank=True)
    journal = models.CharField(max_length=255, null=True, blank=True)
    authors = models.JSONField(default=list, blank=True)
    cema_authors = models.JSONField(default=list, blank=True,  db_column="cemaAuthors")
    citation = models.TextField(null=True, blank=True)
    doi = models.CharField(max_length=255, null=True, blank=True)
    publication_year = models.IntegerField(null=True, blank=True, db_index=True)
    date_published = models.DateTimeField(null=True, blank=True)
    pmid = models.CharField(max_length=100, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    publication_type = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "publications"
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["publication_year"]),
            models.Index(fields=["publication_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# Seminar
# ---------------------------------------------------------------------------

class Seminar(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=500, db_index=True)
    description = models.TextField()
    image = models.ImageField(upload_to='site/images/seminar/', null=True, blank=True)
    video = models.CharField(max_length=500, null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    author = models.CharField(max_length=255, db_index=True)
    author_title = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=100, db_index=True)
    duration = models.CharField(max_length=100, null=True, blank=True)
    upcoming = models.BooleanField(default=False, db_index=True)
    featured = models.BooleanField(default=False, db_index=True)
    tags = models.JSONField(default=list, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "seminars"
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["author"]),
            models.Index(fields=["upcoming"]),
            models.Index(fields=["featured"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class Course(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=500)
    description = models.TextField()
    image = models.ImageField(upload_to='site/images/course/', null=True, blank=True)
    date = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    link = models.URLField(null=True, blank=True)
    upcoming = models.BooleanField(default=False)
    duration = models.CharField(max_length=100, null=True, blank=True)
    target = models.CharField(max_length=255, null=True, blank=True)
    tools = models.CharField(max_length=255, null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt")

    class Meta:
        db_table = "courses"

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

class Training(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=500)
    description = models.TextField()
    image = models.ImageField(upload_to='site/images/trainings/', null=True, blank=True)
    date = models.CharField(max_length=100)
    upcoming = models.BooleanField(default=False)
    category = models.CharField(max_length=255)
    application_deadline = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=255)
    link = models.URLField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt")

    class Meta:
        db_table = "trainings"

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

class News(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=500)
    excerpt = models.TextField()
    body = models.TextField()
    date = models.CharField(max_length=100)
    image = models.ImageField(upload_to='site/images/news/', null=True, blank=True)
    categories = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt")

    class Meta:
        db_table = "news"

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# Report & Download
# ---------------------------------------------------------------------------

class Report(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    year_published = models.IntegerField(null=True, blank=True)
    date_published = models.DateTimeField(null=True, blank=True, auto_now_add=False)
    type = models.CharField(max_length=50, choices=ReportType.choices)
    tags = models.JSONField(default=list, blank=True)
    keywords = models.JSONField(default=list, blank=True)
    is_public = models.BooleanField(default=False)
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    file_name = models.CharField(max_length=500)
    drive_link = models.URLField(null=True, blank=True)
    file_type = models.CharField(max_length=100, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt")

    class Meta:
        db_table = "report"

    def __str__(self):
        return self.title


class Download(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    user_email = models.EmailField(null=True, blank=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="downloads")
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    # updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt")

    class Meta:
        db_table = "download"

    def __str__(self):
        return f"Download of {self.report_id} by {self.user_email}"


# ---------------------------------------------------------------------------
# Data Catalogue
# ---------------------------------------------------------------------------

class DataCatalogue(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=500, db_index=True)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    is_public = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    year = models.IntegerField(null=True, blank=True, db_index=True)
    image = models.ImageField(upload_to='site/images/catalogue/', null=True, blank=True)
    document_url = models.URLField(null=True, blank=True)
    external_url = models.URLField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    file_size = models.CharField(max_length=100, null=True, blank=True)
    file_type = models.CharField(max_length=100, null=True, blank=True)
    downloads = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "data_catalogue"
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["is_public"]),
            models.Index(fields=["is_featured"]),
            models.Index(fields=["year"]),
            models.Index(fields=["title"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title


class DataCatalogueView(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    item = models.ForeignKey(DataCatalogue, on_delete=models.CASCADE, related_name="views", db_index=True)
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "data_catalogue_views"
        unique_together = [("item", "ip_address")]
        indexes = [
            models.Index(fields=["item"]),
            models.Index(fields=["ip_address"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"View of {self.item_id} from {self.ip_address}"


class PolicyBrief(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=500)
    subtitle = models.CharField(max_length=500, null=True, blank=True)
    summary = models.TextField()
    introduction = models.TextField()
    background = models.TextField(null=True, blank=True)
    problem_statement = models.TextField(null=True, blank=True)
    methodology = models.TextField(null=True, blank=True)
    findings = models.TextField()
    key_findings = models.JSONField(default=list, blank=True)
    policy_recommendations = models.TextField()
    recommendations = models.JSONField(default=list, blank=True)
    conclusions = models.TextField(null=True, blank=True)
    publication_ids = models.JSONField(default=list, blank=True)
    image = models.ImageField(upload_to='site/images/policy/', null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt")

    class Meta:
        db_table = "policy_briefs"

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------

class Subscription(models.Model):
    id         = models.AutoField(primary_key=True)
    email      = models.EmailField(unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True,     db_column="updatedAt")

    class Meta:
        db_table = "subscriptions"

    def __str__(self):
        return self.email


# ---------------------------------------------------------------------------
# Contact Form
# ---------------------------------------------------------------------------

class ContactForm(models.Model):
    id         = models.AutoField(primary_key=True)
    full_name  = models.CharField(max_length=255, db_column="fullName")
    email      = models.EmailField()
    subject    = models.CharField(max_length=500)
    message    = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_read    = models.BooleanField(default=False, db_column="isRead")
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True,     db_column="updatedAt")

    class Meta:
        db_table = "contact_forms"

    def __str__(self):
        return f"{self.full_name} — {self.subject}"


# ---------------------------------------------------------------------------
# Rate Limit
# ---------------------------------------------------------------------------

class RateLimit(models.Model):
    id           = models.AutoField(primary_key=True)
    ip_address   = models.GenericIPAddressField()
    endpoint     = models.CharField(max_length=500)
    attempts     = models.IntegerField(default=1)
    window_start = models.DateTimeField(auto_now_add=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table      = "rate_limits"
        unique_together = [("ip_address", "endpoint")]

    def __str__(self):
        return f"{self.ip_address} — {self.endpoint}"


# ---------------------------------------------------------------------------
# Blocked IP
# ---------------------------------------------------------------------------

class BlockedIP(models.Model):
    id         = models.AutoField(primary_key=True)
    ip_address = models.GenericIPAddressField(unique=True, db_index=True)
    reason     = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "blocked_ips"

    def __str__(self):
        return self.ip_address
# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

class AuditLog(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    user_email = models.EmailField(null=True, blank=True)
    action = models.CharField(max_length=255, db_index=True)
    resource = models.CharField(max_length=255, db_index=True)
    resource_id = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(max_length=20)
    route = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(null=True, blank=True)
    status_code = models.IntegerField()
    duration = models.IntegerField(null=True, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["resource"]),
            models.Index(fields=["ip_address"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.action} on {self.resource} by {self.user_email}"


# ---------------------------------------------------------------------------
# System Log
# ---------------------------------------------------------------------------

class SystemLog(models.Model):
    id = models.AutoField(primary_key=True)
    level = models.CharField(max_length=20, db_index=True)
    message = models.TextField()
    component = models.CharField(max_length=255, db_index=True)
    route = models.CharField(max_length=500, null=True, blank=True)
    method = models.CharField(max_length=20, null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    stack = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "system_logs"
        indexes = [
            models.Index(fields=["level"]),
            models.Index(fields=["component"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"[{self.level}] {self.component}: {self.message[:60]}"