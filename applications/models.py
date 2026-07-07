from django.db import models
from django.contrib.auth.models import User


class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    course = models.CharField(max_length=100)
    year_level = models.CharField(max_length=50)
    commitment = models.CharField(max_length=50)
    statement = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    date_applied = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name