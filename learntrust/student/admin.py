from django.contrib import admin
from .models import *

admin.site.register(StudentProfile)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Module)
admin.site.register(StudentProgress)
admin.site.register(WatchEvent)
admin.site.register(Certificate)
