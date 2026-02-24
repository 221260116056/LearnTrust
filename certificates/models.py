import hashlib
import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from student.models import Course


class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certapp_certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certapp_certificates')
    certificate_id = models.CharField(max_length=100, unique=True)
    certificate_hash = models.CharField(max_length=64, unique=True, blank=True)
    verification_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    issued_at = models.DateTimeField(auto_now_add=True)
    
    # Signer information
    signer_name = models.CharField(max_length=200, blank=True)
    signer_title = models.CharField(max_length=200, blank=True)
    signature_image = models.ImageField(upload_to='signatures/', blank=True)
    
    # Certificate template
    template_html = models.TextField(blank=True, help_text='HTML template for certificate generation')
    
    # Revocation status
    is_revoked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'course')

    def save(self, *args, **kwargs):
        if not self.certificate_hash:
            hash_input = f"{self.student_id}{self.course_id}{self.issued_at}{settings.SECRET_KEY}"
            self.certificate_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.certificate_id} - {self.student.username}"
