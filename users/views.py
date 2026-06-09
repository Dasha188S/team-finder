"""View-функции приложения users."""
import json

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import ChangePasswordForm, EditProfileForm, LoginForm, RegisterForm
from .models import Skill, User

USERS_PER_PAGE = 12


def register_view(request):
    if request.user.is_authenticated:
        return redirect("/projects/list/")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("/users/login/")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("/projects/list/")
    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("/projects/list/")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/projects/list/")


def participants_view(request):
    """Список зарегистрированных пользователей с фильтром по навыкам."""
    queryset = User.objects.filter(is_active=True).order_by("id")
    active_skill = request.GET.get("skill", "").strip() or None
    if active_skill:
        queryset = queryset.filter(skills__name=active_skill).distinct()

    paginator = Paginator(queryset, USERS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "users/participants.html",
        {
            "participants": page_obj.object_list,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "all_skills": Skill.objects.order_by("name"),
            "active_skill": active_skill,
        },
    )


def user_detail_view(request, user_id: int):
    profile = get_object_or_404(User, pk=user_id, is_active=True)
    return render(request, "users/user-details.html", {"user": profile})


@login_required
def edit_profile_view(request):
    user = request.user
    form = EditProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(f"/users/{user.pk}/")
    return render(request, "users/edit_profile.html", {"form": form, "user": user})


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect(f"/users/{request.user.pk}/")
    else:
        form = ChangePasswordForm(user=request.user)
    return render(request, "users/change_password.html", {"form": form})


@require_GET
def skills_autocomplete(request):
    """Автодополнение по навыкам — первые 10 совпадений."""
    query = request.GET.get("q", "").strip()
    qs = Skill.objects.all()
    if query:
        qs = qs.filter(name__istartswith=query)
    qs = qs.order_by("name")[:10]
    data = [{"id": s.id, "name": s.name} for s in qs]
    return JsonResponse(data, safe=False)


def _parse_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


@login_required
@require_POST
def add_skill_view(request, user_id: int):
    """Добавить навык в профиль текущего пользователя."""
    profile = get_object_or_404(User, pk=user_id)
    if profile.pk != request.user.pk:
        return JsonResponse({"error": "forbidden"}, status=403)

    payload = _parse_json_body(request)
    if payload is None:
        return HttpResponseBadRequest("Invalid JSON")
    if not payload:
        payload = request.POST.dict()

    skill_id = payload.get("skill_id")
    name = (payload.get("name") or "").strip()

    created = False
    if skill_id:
        try:
            skill = Skill.objects.get(pk=skill_id)
        except Skill.DoesNotExist:
            return JsonResponse({"error": "skill not found"}, status=404)
    elif name:
        skill, created = Skill.objects.get_or_create(name=name)
    else:
        return HttpResponseBadRequest("skill_id or name required")

    added = False
    if not profile.skills.filter(pk=skill.pk).exists():
        profile.skills.add(skill)
        added = True

    return JsonResponse(
        {
            "skill_id": skill.id,
            "id": skill.id,
            "name": skill.name,
            "created": created,
            "added": added,
        }
    )


@login_required
@require_POST
def remove_skill_view(request, user_id: int, skill_id: int):
    profile = get_object_or_404(User, pk=user_id)
    if profile.pk != request.user.pk:
        return JsonResponse({"error": "forbidden"}, status=403)
    skill = get_object_or_404(Skill, pk=skill_id)
    if not profile.skills.filter(pk=skill.pk).exists():
        return JsonResponse({"error": "skill not in profile"}, status=400)
    profile.skills.remove(skill)
    return JsonResponse({"status": "ok"})
