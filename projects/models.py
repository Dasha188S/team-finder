"""Модели приложения projects."""
from django.conf import settings
from django.db import models
from django.urls import reverse


class Project(models.Model):
    """Pet-проект, опубликованный пользователем."""

    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [(STATUS_OPEN, "Open"), (STATUS_CLOSED, "Closed")]

    name = models.CharField("Название", max_length=200)
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
        max_length=6,
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
