from django import forms
from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

from .models import CustomUser, University
from django.utils import timezone


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label='Email', widget=forms.EmailInput)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput,
                                help_text=password_validation.password_validators_help_text_html())
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    university = forms.ModelChoiceField(
        queryset=University.objects.all().order_by('name'),
        required=True,
        widget=forms.Select(attrs={'id': 'id_university'}),
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2', 'university')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Email already exists.')
        if not email.endswith('.ac.uk'):
            raise ValidationError('Email must be a university email address.')
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        password_validation.validate_password(password1)
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')

    def clean_university(self):
        instance_university = self.instance.university
        new_university = self.cleaned_data.get('university')

        if instance_university and new_university != instance_university:
            raise forms.ValidationError("The university for a user can only be set once and cannot be changed.")

        return new_university

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        university_instance = self.cleaned_data['university']
        user.university = university_instance
        user.city = university_instance.city
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        self.user = authenticate(email=email, password=password)

        if self.user is None:
            raise forms.ValidationError("Invalid email or password.")

        return cleaned_data


class CustomPasswordChangeForm(PasswordChangeForm):

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        password_validation.validate_password(password1, self.user)
        return password1

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(UserProfileForm, self).__init__(*args, **kwargs)

        # Set queryset to user's university
        if self.user and self.user.university:
            self.fields['university'].queryset = University.objects.filter(id=self.user.university.id)

        # Make the field read-only
        self.fields['university'].disabled = True

    bio = forms.CharField(required=False, help_text='Max length: 300 characters')

    move_out_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = CustomUser
        fields = ['avatar', 'first_name', 'last_name',
                  'bio', 'university', 'move_out_date']

    def clean_move_out_date(self):
        move_out_date = self.cleaned_data.get('move_out_date')
        if move_out_date and move_out_date < timezone.now().date():
            raise ValidationError('Invalid date. Please enter a date in the future.')
        return move_out_date

    def save(self, commit=True):
        if not self.is_valid():
            # Don't save if the form is not valid
            return None

        user = super(UserProfileForm, self).save(commit=False)
        avatar = self.cleaned_data['avatar']
        if avatar:
            user.avatar = avatar
        first_name = self.cleaned_data['first_name']
        if first_name:
            user.first_name = first_name
        last_name = self.cleaned_data['last_name']
        if last_name:
            user.last_name = last_name
        bio = self.cleaned_data['bio']
        if bio:
            user.bio = bio
        user.move_out_date = self.cleaned_data['move_out_date']

        if commit:
            user.save()
        return user
