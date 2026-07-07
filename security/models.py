from django.contrib.auth.models import User
from django.db import models

class WebAuthnCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webauthn_credentials')
    credential_id = models.TextField(unique=True)
    public_key = models.TextField()
    sign_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'WebAuthn Credential'
        verbose_name_plural = 'WebAuthn Credentials'

    def __str__(self):
        return f"{self.user.username} - {self.credential_id[:20]}..."
