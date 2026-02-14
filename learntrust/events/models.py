from django.db import models
from django.contrib.auth.models import User
from student.models import Module


class ImmutableLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    token_hash = models.CharField(max_length=128)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.event_type} @ {self.timestamp}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise Exception("ImmutableLog is immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise Exception("ImmutableLog is immutable and cannot be deleted.")
