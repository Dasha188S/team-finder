"""View-функции приложения projects."""
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from team_finder.pagination import paginate

from .forms import ProjectForm
from .models import Project

# === Параметры страницы списка ==============================================

PROJECTS_PER_PAGE = 12

# === Сообщения JSON-ошибок ==================================================

ERROR_KEY = "error"
ERROR_PROJECT_NOT_FOUND = "project not found"
ERROR_FORBIDDEN = "forbidden"
ERROR_ALREADY_CLOSED = "already closed"

# === Имена URL-маршрутов ====================================================

URL_PROJECT_DETAIL = "projects:detail"


def project_list(request):
    """Главная страница: все проекты, отсортированные от новых к старым."""
    queryset = Project.objects.select_related("owner").order_by("-created_at")
    page_obj = paginate(request, queryset, PROJECTS_PER_PAGE)
    return render(
        request,
        "projects/project_list.html",
        {
            "projects": page_obj.object_list,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
        },
    )


def project_detail(request, project_id: int):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants"),
        pk=project_id,
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect(URL_PROJECT_DETAIL, project_id=project.pk)
    else:
        form = ProjectForm()
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False},
    )


@login_required
def project_edit(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id:
        return redirect(URL_PROJECT_DETAIL, project_id=project.pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect(URL_PROJECT_DETAIL, project_id=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True, "project": project},
    )


@login_required
@require_POST
def project_complete(request, project_id: int):
    """Завершить проект (только владелец, статус ``open`` -> ``closed``).

    Эндпоинт возвращает только JSON, поэтому ``get_object_or_404`` не подходит
    (он отдаёт HTML). Существование проекта проверяем через ``.first()``.
    """
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return JsonResponse(
            {ERROR_KEY: ERROR_PROJECT_NOT_FOUND}, status=HTTPStatus.NOT_FOUND
        )
    if project.owner_id != request.user.id:
        return JsonResponse(
            {ERROR_KEY: ERROR_FORBIDDEN}, status=HTTPStatus.FORBIDDEN
        )
    if project.status != Project.STATUS_OPEN:
        return JsonResponse(
            {ERROR_KEY: ERROR_ALREADY_CLOSED}, status=HTTPStatus.BAD_REQUEST
        )
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": project.status})


@login_required
@require_POST
def project_toggle_participate(request, project_id: int):
    """Включить/выключить участие текущего пользователя в проекте.

    Эндпоинт возвращает только JSON — проверяем существование через
    ``.first()`` (а не ``get_object_or_404``, который вернул бы HTML 404).
    """
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return JsonResponse(
            {ERROR_KEY: ERROR_PROJECT_NOT_FOUND}, status=HTTPStatus.NOT_FOUND
        )

    is_already_participant = project.participants.filter(pk=request.user.pk).exists()
    if is_already_participant:
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)
    return JsonResponse({"status": "ok", "participant": not is_already_participant})
