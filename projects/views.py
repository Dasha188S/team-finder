"""View-функции приложения projects."""
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import Project

PROJECTS_PER_PAGE = 12


def project_list(request):
    """Главная страница: все проекты, отсортированные от новых к старым."""
    queryset = Project.objects.select_related("owner").order_by("-created_at")
    paginator = Paginator(queryset, PROJECTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
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
            return redirect(f"/projects/{project.pk}/")
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
        return redirect(f"/projects/{project.pk}/")
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect(f"/projects/{project.pk}/")
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
    """Завершить проект (только владелец, статус open -> closed)."""
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id:
        return JsonResponse({"error": "forbidden"}, status=403)
    if project.status != Project.STATUS_OPEN:
        return JsonResponse({"error": "already closed"}, status=400)
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": project.status})


@login_required
@require_POST
def project_toggle_participate(request, project_id: int):
    """Включить/выключить участие текущего пользователя в проекте."""
    project = get_object_or_404(Project, pk=project_id)
    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        is_participant = False
    else:
        project.participants.add(request.user)
        is_participant = True
    return JsonResponse({"status": "ok", "participant": is_participant})
