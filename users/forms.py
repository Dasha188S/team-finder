"""Формы приложения users."""
import re
from urllib.parse import urlparse

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.forms import PasswordChangeForm

from .models import User

PHONE_RE = re.compile(r"^(?:8|\+7)\d{10}$")


def normalize_phone(raw: str) -> str:
    """Привести телефон к формату +7XXXXXXXXXX. Пустая строка возвращается как есть."""
    raw = (raw or "").strip().replace(" ", "").replace("-", "")
    if not raw:
        return ""
    if raw.startswith("8") and len(raw) == 11:
        return "+7" + raw[1:]
    return raw


def validate_github_url(value: str) -> str:
    """Проверить, что ссылка валидная и ведёт на github.com."""
    if not value:
        return value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise forms.ValidationError("Некорректная ссылка")
    host = parsed.netloc.lower()
    if host != "github.com" and not host.endswith(".github.com"):
        raise forms.ValidationError("Ссылка должна вести на github.com")
    return value


class RegisterForm(forms.ModelForm):
    """Регистрация нового пользователя."""

    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")
        labels = {"name": "Имя", "surname": "Фамилия", "email": "Email"}

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован")
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
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
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
                raise forms.ValidationError("Неверный email или пароль")
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
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "Ссылка на GitHub",
        }
        widgets = {
            "about": forms.Textarea(attrs={"rows": 4}),
            "avatar": forms.ClearableFileInput(attrs={"id": "id_avatar"}),
        }

    def clean_phone(self):
        raw = self.cleaned_data.get("phone", "")
        normalized = normalize_phone(raw)
        if normalized and not PHONE_RE.match(normalized):
            raise forms.ValidationError(
                "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX"
            )
        if normalized:
            qs = User.objects.filter(phone=normalized).exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Этот номер телефона уже используется")
        return normalized

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url", ""))


class ChangePasswordForm(PasswordChangeForm):
    """Стандартная форма смены пароля Django (содержит нужные поля)."""

    error_messages = {
        **PasswordChangeForm.error_messages,
        "password_incorrect": "Текущий пароль введён неверно",
    }
