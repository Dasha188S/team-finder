"""Формы приложения projects."""
from django import forms

from users.utils import validate_github_url

from .models import Project, PROJECT_STATUS_CLOSED, PROJECT_STATUS_OPEN

# === Лейблы и параметры виджетов ============================================

LABEL_NAME = "Название проекта"
LABEL_DESCRIPTION = "Описание проекта"
LABEL_GITHUB = "Ссылка на GitHub"
LABEL_STATUS = "Статус"

STATUS_LABEL_OPEN = "Открыт"
STATUS_LABEL_CLOSED = "Закрыт"
STATUS_HUMAN_CHOICES = (
    (PROJECT_STATUS_OPEN, STATUS_LABEL_OPEN),
    (PROJECT_STATUS_CLOSED, STATUS_LABEL_CLOSED),
)

DESCRIPTION_TEXTAREA_ROWS = 5


class ProjectForm(forms.ModelForm):
    """Создание и редактирование проекта."""

    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        labels = {
            "name": LABEL_NAME,
            "description": LABEL_DESCRIPTION,
            "github_url": LABEL_GITHUB,
            "status": LABEL_STATUS,
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": DESCRIPTION_TEXTAREA_ROWS}),
            "status": forms.Select(choices=STATUS_HUMAN_CHOICES),
        }

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url", ""))
