from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ---------------------------------
# 🔔 Notification
# ---------------------------------
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


# ---------------------------------
# 1️⃣ Student Profile
# ---------------------------------
class StudentProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(
        upload_to='profiles/',
        default='profiles/default.png',
        blank=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    moodle_user_id = models.IntegerField(null=True, blank=True, help_text="Moodle user ID for API integration")

    def __str__(self):
        return self.user.username


# ---------------------------------
# 2️⃣ Course
# ---------------------------------
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    moodle_course_id = models.IntegerField(null=True, blank=True, help_text="Moodle course ID for API integration")

    def __str__(self):
        return self.title


# ---------------------------------
# 3️⃣ Enrollment
# ---------------------------------
class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"


# ---------------------------------
# 4️⃣ Course Module
# ---------------------------------
class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='videos/%Y/%m/%d/', blank=True, null=True)
    hls_path = models.CharField(max_length=500, blank=True, null=True)
    order = models.IntegerField()
    min_watch_percent = models.IntegerField(default=80)
    must_pass_quiz = models.BooleanField(default=False)
    allowed_attempts = models.IntegerField(default=3)
    disable_seeking = models.BooleanField(default=True)
    required_replays = models.IntegerField(default=0)
    release_date = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    
    # Extended security fields
    disable_fast_forward = models.BooleanField(default=True)
    mandatory_checkpoints = models.IntegerField(default=0)
    timeout_seconds = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# ---------------------------------
# 5️⃣ Student Progress
# ---------------------------------
class StudentProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)

    watch_percent = models.FloatField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'module')

    def mark_completed(self):
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()

    def __str__(self):
        return f"{self.student.username} - {self.module.title}"


# ---------------------------------
# 6️⃣ Watch Events (append-only)
# ---------------------------------
class WatchEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('play', 'Play'),
        ('pause', 'Pause'),
        ('heartbeat', 'Heartbeat'),
        ('checkpoint', 'Checkpoint'),
        ('webcam_snapshot', 'Webcam Snapshot'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, db_index=True)
    current_time = models.FloatField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='play')
    sequence_number = models.IntegerField(default=0)
    token_hash = models.CharField(max_length=128, default='')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']
        unique_together = [('student', 'module', 'sequence_number')]
        indexes = [
            models.Index(fields=['student', 'module', 'created_at']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.module.title} @ {self.current_time}s"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise Exception("WatchEvent is append-only and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise Exception("WatchEvent is append-only and cannot be deleted.")


# ---------------------------------
# 7️⃣ Certificate
# ---------------------------------
class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    certificate_id = models.CharField(max_length=100, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_revoked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.certificate_id} - {self.student.username}"


# ---------------------------------
# 8️⃣ System Settings (Singleton)
# ---------------------------------
class SystemSettings(models.Model):
    token_expiry_minutes = models.IntegerField(default=10, help_text='Token expiry time in minutes')
    heartbeat_interval_seconds = models.IntegerField(default=10, help_text='Heartbeat interval in seconds')
    max_micro_quiz_failures = models.IntegerField(default=3, help_text='Maximum micro-quiz failures allowed')
    certificate_signer_name = models.CharField(max_length=200, default='LearnTrust Administrator', help_text='Default certificate signer name')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SystemSettings.objects.exists():
            raise Exception('Only one SystemSettings instance allowed')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"System Settings (Updated: {self.updated_at})"


# ---------------------------------
# 9️⃣ Teacher Registration Request
# ---------------------------------
class TeacherRegistrationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_request')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_teacher_requests')
    rejection_reason = models.TextField(blank=True, help_text='Reason for rejection if applicable')

    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'Teacher Registration Request'
        verbose_name_plural = 'Teacher Registration Requests'

    def __str__(self):
        return f"{self.user.email} - {self.status}"

    def approve(self, reviewed_by_user):
        """Approve the teacher registration request."""
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by_user
        self.save()
        
        # Update user profile to teacher role
        profile, _ = StudentProfile.objects.get_or_create(user=self.user)
        profile.role = 'teacher'
        profile.save()
        
        # Create notification for the teacher
        Notification.objects.create(
            user=self.user,
            message="Your teacher registration has been approved! You can now access the teacher panel."
        )

    def reject(self, reviewed_by_user, reason=''):
        """Reject the teacher registration request."""
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by_user
        self.rejection_reason = reason
        self.save()
        
        # Create notification for the teacher
        Notification.objects.create(
            user=self.user,
            message=f"Your teacher registration request has been rejected. Reason: {reason if reason else 'No reason provided'}"
        )
