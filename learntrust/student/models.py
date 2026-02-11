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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(
        upload_to='profiles/',
        default='profiles/default.png',
        blank=True
    )

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
    order = models.IntegerField()
    min_watch_percent = models.IntegerField(default=80)

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
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    current_time = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.student.username} - {self.module.title} @ {self.current_time}s"


# ---------------------------------
# 7️⃣ Certificate
# ---------------------------------
class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    certificate_id = models.CharField(max_length=100, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.certificate_id} - {self.student.username}"
