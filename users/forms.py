"""Формы приложения users."""
from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.forms import PasswordChangeForm

from .models import User
from .utils import (
    PHONE_DUPLICATE_ERROR,
    PHONE_FORMAT_ERROR,
    PHONE_RE,
    normalize_phone,
    validate_github_url,
)

# === Текстовые лейблы и параметры виджетов ==================================
# Чтобы избежать «магических» строк/чисел, повторяющихся в формах.

LABEL_NAME = "Имя"
LABEL_SURNAME = "Фамилия"
LABEL_EMAIL = "Email"
LABEL_PASSWORD = "Пароль"
LABEL_AVATAR = "Аватар"
LABEL_ABOUT = "О себе"
LABEL_PHONE = "Телефон"
LABEL_GITHUB = "Ссылка на GitHub"

DUPLICATE_EMAIL_ERROR = "Пользователь с таким email уже зарегистрирован"
INVALID_CREDENTIALS_ERROR = "Неверный email или пароль"
PASSWORD_INCORRECT_ERROR = "Текущий пароль введён неверно"

ABOUT_TEXTAREA_ROWS = 4

NEW_PASSWORD_AUTOCOMPLETE = "new-password"
CURRENT_PASSWORD_AUTOCOMPLETE = "current-password"
EMAIL_AUTOCOMPLETE = "email"
AVATAR_INPUT_ID = "id_avatar"


class RegisterForm(forms.ModelForm):
    """Регистрация нового пользователя."""

    password = forms.CharField(
        label=LABEL_PASSWORD,
        widget=forms.PasswordInput(attrs={"autocomplete": NEW_PASSWORD_AUTOCOMPLETE}),
    )

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")
        labels = {"name": LABEL_NAME, "surname": LABEL_SURNAME, "email": LABEL_EMAIL}

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(DUPLICATE_EMAIL_ERROR)
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        password_validation.validate_password(password)
        return password

    def save(self, commit=True):
        user = User(
            email=self.cleaned_data["email"],
            name=self.cleaned_data["name"].strip(),
            surname=self.cleaned_data["surname"].strip(),
        )
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Авторизация по email и паролю."""

    email = forms.EmailField(
        label=LABEL_EMAIL,
        widget=forms.EmailInput(attrs={"autocomplete": EMAIL_AUTOCOMPLETE}),
    )
    password = forms.CharField(
        label=LABEL_PASSWORD,
        widget=forms.PasswordInput(attrs={"autocomplete": CURRENT_PASSWORD_AUTOCOMPLETE}),
    )

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                raise forms.ValidationError(INVALID_CREDENTIALS_ERROR)
            self.user = user
        return cleaned

    def get_user(self):
        return self.user


class EditProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя."""

    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")
        labels = {
            "name": LABEL_NAME,
            "surname": LABEL_SURNAME,
            "avatar": LABEL_AVATAR,
            "about": LABEL_ABOUT,
            "phone": LABEL_PHONE,
            "github_url": LABEL_GITHUB,
        }
        widgets = {
            "about": forms.Textarea(attrs={"rows": ABOUT_TEXTAREA_ROWS}),
            "avatar": forms.ClearableFileInput(attrs={"id": AVATAR_INPUT_ID}),
        }

    def clean_phone(self):
        raw = self.cleaned_data.get("phone", "")
        normalized = normalize_phone(raw)
        if normalized and not PHONE_RE.match(normalized):
            raise forms.ValidationError(PHONE_FORMAT_ERROR)
        if normalized:
            qs = User.objects.filter(phone=normalized).exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(PHONE_DUPLICATE_ERROR)
        return normalized

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url", ""))


class ChangePasswordForm(PasswordChangeForm):
    """Стандартная форма смены пароля Django (содержит нужные поля)."""

    error_messages = {
        **PasswordChangeForm.error_messages,
        "password_incorrect": PASSWORD_INCORRECT_ERROR,
    }
