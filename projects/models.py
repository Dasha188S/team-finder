"""Модели приложения projects."""
from django.conf import settings
from django.db import models
from django.urls import reverse

# === Ограничения длин полей и доступные статусы =============================
# Все «магические числа» и значения статуса вынесены в константы уровня
# модуля.

PROJECT_NAME_MAX_LENGTH = 200
PROJECT_STATUS_MAX_LENGTH = 6

PROJECT_STATUS_OPEN = "open"
PROJECT_STATUS_CLOSED = "closed"
PROJECT_STATUS_CHOICES = [
    (PROJECT_STATUS_OPEN, "Open"),
    (PROJECT_STATUS_CLOSED, "Closed"),
]


class Project(models.Model):
    """Pet-проект, опубликованный пользователем."""

    # Ссылки-сокращения на константы статуса, чтобы пользоваться через
    # ``Project.STATUS_OPEN`` (как принято в Django-моделях).
    STATUS_OPEN = PROJECT_STATUS_OPEN
    STATUS_CLOSED = PROJECT_STATUS_CLOSED
    STATUS_CHOICES = PROJECT_STATUS_CHOICES

    name = models.CharField("Название", max_length=PROJECT_NAME_MAX_LENGTH)
    description = models.TextField("Описание", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    github_url = models.URLField("GitHub", blank=True)
    status = models.CharField(
        "Статус",
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
        verbose_name="Участники",
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("-created_at",)),
            models.Index(fields=("status",)),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("projects:detail", args=[self.pk])

    @property
    def is_open(self) -> bool:
        return self.status == self.STATUS_OPEN
