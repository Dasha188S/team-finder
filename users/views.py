"""View-функции приложения users."""
import json
from http import HTTPStatus

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from team_finder.pagination import paginate

from .forms import ChangePasswordForm, EditProfileForm, LoginForm, RegisterForm
from .models import Skill, User

# === Параметры страницы списка ==============================================

USERS_PER_PAGE = 12

# === Параметры автодополнения навыков =======================================

SKILL_AUTOCOMPLETE_LIMIT = 10
SKILL_QUERY_PARAM = "q"
SKILL_FILTER_PARAM = "skill"

# === Параметры тела JSON-запроса добавления навыка ==========================

PAYLOAD_SKILL_ID = "skill_id"
PAYLOAD_NAME = "name"

# === Сообщения JSON-ошибок ==================================================

ERROR_KEY = "error"
ERROR_USER_NOT_FOUND = "user not found"
ERROR_SKILL_NOT_FOUND = "skill not found"
ERROR_SKILL_NOT_IN_PROFILE = "skill not in profile"
ERROR_FORBIDDEN = "forbidden"
ERROR_INVALID_JSON = "Invalid JSON"
ERROR_SKILL_ARGS_REQUIRED = "skill_id or name required"

# === Имена URL-маршрутов (используются с redirect) ==========================

URL_PROJECTS_LIST = "projects:list"
URL_USERS_LOGIN = "users:login"
URL_USER_DETAIL = "users:detail"


def register_view(request):
    if request.user.is_authenticated:
        return redirect(URL_PROJECTS_LIST)
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(URL_USERS_LOGIN)
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect(URL_PROJECTS_LIST)
    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(URL_PROJECTS_LIST)
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect(URL_PROJECTS_LIST)


def participants_view(request):
    """Список зарегистрированных пользователей с фильтром по навыкам."""
    queryset = User.objects.filter(is_active=True).order_by("id")
    active_skill = request.GET.get(SKILL_FILTER_PARAM, "").strip() or None
    if active_skill:
        queryset = queryset.filter(skills__name=active_skill).distinct()

    page_obj = paginate(request, queryset, USERS_PER_PAGE)

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
        return redirect(URL_USER_DETAIL, user_id=user.pk)
    return render(request, "users/edit_profile.html", {"form": form, "user": user})


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect(URL_USER_DETAIL, user_id=request.user.pk)
    else:
        form = ChangePasswordForm(user=request.user)
    return render(request, "users/change_password.html", {"form": form})


@require_GET
def skills_autocomplete(request):
    """Автодополнение по навыкам — первые ``SKILL_AUTOCOMPLETE_LIMIT`` совпадений."""
    query = request.GET.get(SKILL_QUERY_PARAM, "").strip()
    qs = Skill.objects.all()
    if query:
        qs = qs.filter(name__istartswith=query)
    qs = qs.order_by("name")[:SKILL_AUTOCOMPLETE_LIMIT]
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
    """Добавить навык в профиль текущего пользователя.

    Возвращает только JSON, поэтому пользователя ищем через ``.first()`` и
    отдаём ``JsonResponse`` с нужным статусом — иначе ``get_object_or_404``
    подсунул бы клиенту HTML-страницу.
    """
    profile = User.objects.filter(pk=user_id).first()
    if profile is None:
        return JsonResponse(
            {ERROR_KEY: ERROR_USER_NOT_FOUND}, status=HTTPStatus.NOT_FOUND
        )
    if profile.pk != request.user.pk:
        return JsonResponse(
            {ERROR_KEY: ERROR_FORBIDDEN}, status=HTTPStatus.FORBIDDEN
        )

    payload = _parse_json_body(request)
    if payload is None:
        return HttpResponseBadRequest(ERROR_INVALID_JSON)
    if not payload:
        payload = request.POST.dict()

    skill_id = payload.get(PAYLOAD_SKILL_ID)
    name = (payload.get(PAYLOAD_NAME) or "").strip()

    created = False
    if skill_id:
        skill = Skill.objects.filter(pk=skill_id).first()
        if skill is None:
            return JsonResponse(
                {ERROR_KEY: ERROR_SKILL_NOT_FOUND}, status=HTTPStatus.NOT_FOUND
            )
    elif name:
        skill, created = Skill.objects.get_or_create(name=name)
    else:
        return HttpResponseBadRequest(ERROR_SKILL_ARGS_REQUIRED)

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
    """Удалить навык из профиля текущего пользователя.

    Все ответы — JSON, поэтому ``get_object_or_404`` использовать нельзя:
    проверяем существование объектов через ``.first()`` и отдаём
    ``JsonResponse`` с нужным статусом.
    """
    profile = User.objects.filter(pk=user_id).first()
    if profile is None:
        return JsonResponse(
            {ERROR_KEY: ERROR_USER_NOT_FOUND}, status=HTTPStatus.NOT_FOUND
        )
    if profile.pk != request.user.pk:
        return JsonResponse(
            {ERROR_KEY: ERROR_FORBIDDEN}, status=HTTPStatus.FORBIDDEN
        )
    skill = Skill.objects.filter(pk=skill_id).first()
    if skill is None:
        return JsonResponse(
            {ERROR_KEY: ERROR_SKILL_NOT_FOUND}, status=HTTPStatus.NOT_FOUND
        )
    if not profile.skills.filter(pk=skill.pk).exists():
        return JsonResponse(
            {ERROR_KEY: ERROR_SKILL_NOT_IN_PROFILE}, status=HTTPStatus.BAD_REQUEST
        )
    profile.skills.remove(skill)
    return JsonResponse({"status": "ok"})
