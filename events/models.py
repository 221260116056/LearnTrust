import hashlib
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from student.models import Module


class ImmutableLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)
    token_hash = models.CharField(max_length=128)
    previous_hash = models.CharField(max_length=64, blank=True)
    current_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.event_type} @ {self.created_at}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise Exception("ImmutableLog is immutable and cannot be updated.")
        
        # Fetch last log and set previous_hash
        last_log = ImmutableLog.objects.order_by('-created_at').first()
        if last_log:
            self.previous_hash = last_log.current_hash
        else:
            self.previous_hash = "0" * 64
        
        # Generate current_hash before saving
        hash_input = f"{self.user_id}{self.event_type}{self.created_at}{self.previous_hash}{settings.SECRET_KEY}"
        self.current_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise Exception("ImmutableLog is immutable and cannot be deleted.")
