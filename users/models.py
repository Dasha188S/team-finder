"""Модели приложения users: User и Skill (для варианта 2)."""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.urls import reverse

from .managers import UserManager
from .utils import generate_avatar

# === Ограничения длин полей =================================================
# Все размеры вынесены на уровень модуля, чтобы не было «магических чисел»
# в определениях полей.

SKILL_NAME_MAX_LENGTH = 124
USER_NAME_MAX_LENGTH = 124
USER_SURNAME_MAX_LENGTH = 124
USER_PHONE_MAX_LENGTH = 12
USER_ABOUT_MAX_LENGTH = 256

AVATAR_UPLOAD_DIR = "avatars/"
DEFAULT_AVATAR_USERNAME = "user"
AVATAR_FILE_EXTENSION = ".png"


class Skill(models.Model):
    """Навык, привязываемый к пользователям."""

    name = models.CharField("Название", max_length=SKILL_NAME_MAX_LENGTH, unique=True)

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь Team Finder. Логин по email."""

    email = models.EmailField("Email", unique=True)
    name = models.CharField("Имя", max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField("Фамилия", max_length=USER_SURNAME_MAX_LENGTH)
    avatar = models.ImageField("Аватар", upload_to=AVATAR_UPLOAD_DIR)
    phone = models.CharField("Телефон", max_length=USER_PHONE_MAX_LENGTH, blank=True)
    github_url = models.URLField("GitHub", blank=True)
    about = models.CharField("О себе", max_length=USER_ABOUT_MAX_LENGTH, blank=True)

    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Администратор", default=False)
    date_joined = models.DateTimeField("Дата регистрации", auto_now_add=True)

    skills = models.ManyToManyField(
        Skill,
        related_name="users",
        blank=True,
        verbose_name="Навыки",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.name} {self.surname} <{self.email}>"

    def get_full_name(self) -> str:
        return f"{self.name} {self.surname}".strip()

    def get_short_name(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("users:detail", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.avatar:
            seed = self.email or self.name
            avatar_file = generate_avatar(self.name, seed=seed)
            local_part = (self.email or DEFAULT_AVATAR_USERNAME).split("@")[0]
            self.avatar.save(local_part + AVATAR_FILE_EXTENSION, avatar_file, save=False)
        super().save(*args, **kwargs)
