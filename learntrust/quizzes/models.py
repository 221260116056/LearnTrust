from django.db import models
from django.contrib.auth.models import User
from student.models import Module


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    time_limit_seconds = models.IntegerField(default=1800)  # Default 30 minutes
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.module.title} - {'Passed' if self.passed else 'Failed'}"


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
