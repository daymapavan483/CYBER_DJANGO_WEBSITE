from django.db import models

# Create your models here.

class User(models.Model):
    first_name = models.CharField(max_length=30,null=True,blank=True)
    last_name = models.CharField(max_length=30,null=True,blank=True)
    email = models.EmailField(unique=True,null=True,blank=True)
    password = models.CharField(max_length=50,null=True,blank=True)
    contact_no = models.CharField(max_length=15,null=True,blank=True)

    otp = models.IntegerField(default=0,null=True,blank=True)
    is_verified = models.BooleanField(default=False,null=True,blank=True)
    is_suspicious = models.BooleanField(default=False,null=True,blank=True)
    login_attempts = models.IntegerField(default=0,null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)

    def __str__(self):
        return self.email


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    ip_address = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class SuspiciousActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)