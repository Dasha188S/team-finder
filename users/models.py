"""Модели приложения users: User и Skill (для варианта 2)."""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.urls import reverse

from .managers import UserManager
from .utils import generate_avatar


class Skill(models.Model):
    """Навык, привязываемый к пользователям."""

    name = models.CharField("Название", max_length=124, unique=True)

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь Team Finder. Логин по email."""

    email = models.EmailField("Email", unique=True)
    name = models.CharField("Имя", max_length=124)
    surname = models.CharField("Фамилия", max_length=124)
    avatar = models.ImageField("Аватар", upload_to="avatars/")
    phone = models.CharField("Телефон", max_length=12, blank=True)
    github_url = models.URLField("GitHub", blank=True)
    about = models.CharField("О себе", max_length=256, blank=True)

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
            filename = f"{(self.email or 'user').split('@')[0]}.png"
            self.avatar.save(filename, avatar_file, save=False)
        super().save(*args, **kwargs)
