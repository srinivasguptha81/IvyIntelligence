from django import forms
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import StudentProfile, DOMAIN_CHOICES


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating student profile information."""

    domains_of_interest = forms.MultipleChoiceField(
        choices=DOMAIN_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select all domains you are interested in."
    )

    skills_input = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Python, Machine Learning, Django, React...'}),
        help_text="Enter your skills separated by commas.",
        label="Skills"
    )

    class Meta:
        model = StudentProfile
        fields = [
            'bio', 'avatar', 'university', 'year_of_study',
            'cgpa', 'resume', 'linkedin_url', 'github_url',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us about yourself...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.domains_of_interest:
            self.fields['domains_of_interest'].initial = self.instance.domains_of_interest
        if self.instance and self.instance.skills:
            self.fields['skills_input'].initial = ', '.join(self.instance.skills)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('bio'),
            Field('avatar'),
            Row(
                Column('university', css_class='col-md-6'),
                Column('year_of_study', css_class='col-md-3'),
                Column('cgpa', css_class='col-md-3'),
            ),
            Field('skills_input'),
            Field('domains_of_interest'),
            Row(
                Column('linkedin_url', css_class='col-md-6'),
                Column('github_url', css_class='col-md-6'),
            ),
            Field('resume'),
            Submit('submit', 'Update Profile', css_class='btn btn-primary btn-lg mt-3'),
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert comma-separated skills to list
        skills_str = self.cleaned_data.get('skills_input', '')
        instance.skills = [s.strip() for s in skills_str.split(',') if s.strip()]
        # Save domain choices as list
        instance.domains_of_interest = self.cleaned_data.get('domains_of_interest', [])
        if commit:
            instance.save()
        return instance


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
