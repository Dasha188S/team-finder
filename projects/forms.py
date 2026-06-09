"""Формы приложения projects."""
from django import forms

from users.forms import validate_github_url

from .models import Project


class ProjectForm(forms.ModelForm):
    """Создание и редактирование проекта."""

    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на GitHub",
            "status": "Статус",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "status": forms.Select(
                choices=[("open", "Открыт"), ("closed", "Закрыт")],
            ),
        }

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url", ""))
