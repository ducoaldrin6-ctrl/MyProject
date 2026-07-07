from django import forms
from .models import Application


class ApplicationForm(forms.ModelForm):

    YEAR_LEVEL_CHOICES = [
        ('', 'Select Year Level'),
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
    ]

    year_level = forms.ChoiceField(
        choices=YEAR_LEVEL_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Application

        fields = [
            'full_name',
            'email',
            'course',
            'year_level',
            'commitment',
            'statement',
        ]

        widgets = {

            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            }),

            'course': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your course'
            }),

            'commitment': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'min': '500',
                'max': '2500'
            }),

            'statement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Write your personal statement'
            }),

        }

    def clean_commitment(self):

        commitment = self.cleaned_data.get('commitment')

        if int(commitment) < 500 or int(commitment) > 2500:
            raise forms.ValidationError(
                'Monthly commitment must be between ₱500 and ₱2500.'
            )

        return commitment

    def clean_statement(self):

        statement = self.cleaned_data.get('statement')

        if len(statement) < 20:
            raise forms.ValidationError(
                'Personal statement must be at least 20 characters.'
            )

        return statement