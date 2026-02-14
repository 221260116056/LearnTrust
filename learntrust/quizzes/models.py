from django.db import models
from student.models import Module


class MicroQuiz(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='micro_quizzes')
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1)
    trigger_time = models.IntegerField()  # seconds into video
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['trigger_time']

    def __str__(self):
        return f"{self.module.title} @ {self.trigger_time}s: {self.question[:50]}"
