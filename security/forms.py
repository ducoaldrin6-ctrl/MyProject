from django import forms


class LoginForm(forms.Form):
    username_or_email = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)
