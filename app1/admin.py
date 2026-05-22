from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(ActivityLog)
admin.site.register(Alert)
admin.site.register(SuspiciousActivity)