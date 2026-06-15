"""Автотесты приложения projects."""
from http import HTTPStatus

from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import User

from .models import Project

# === Общие константы ========================================================

MEDIA_TEST_ROOT = "/tmp/team-finder-media-test"

DEFAULT_PASSWORD = "demo-pwd-1234567"

# Email-ы тестовых пользователей.
OWNER_EMAIL = "proj@example.com"
CREATOR_EMAIL = "cre@example.com"
OTHER_EMAIL = "otr@example.com"
ACTION_OWNER_EMAIL = "own@example.com"
ACTION_USER_EMAIL = "usr@example.com"

# Имена/фамилии (используются повторно в фикстурах).
OWNER_NAME, OWNER_SURNAME = "Pj", "Owner"
CREATOR_NAME, CREATOR_SURNAME = "Cre", "Ate"
OTHER_NAME, OTHER_SURNAME = "Otr", "User"
ACTION_OWNER_NAME, ACTION_OWNER_SURNAME = "Own", "Er"
ACTION_USER_NAME, ACTION_USER_SURNAME = "Usr", "Or"

# Статусы проекта (дублируют значения модели в удобном для тестов виде).
STATUS_OPEN = "open"
STATUS_CLOSED = "closed"

# Параметры списка проектов.
TOTAL_PROJECTS = 15
PROJECTS_PER_PAGE = 12
NEWEST_PROJECT_NAME = "P14"
OLDEST_ON_FIRST_PAGE_NAME = "P03"

# Названия и описания проектов.
PROJECT_NAME_NEW = "NewProj"
PROJECT_NAME_MINE = "Mine"
PROJECT_NAME_HACKED = "Hacked"
PROJECT_NAME_SHORT = "X"
PROJECT_NAME_DEMO = "Demo"
PROJECT_DESCRIPTION = "x"

# Ссылки на GitHub.
GITHUB_BAD = "https://gitlab.com/x"

# URL-фрагменты и подстроки ответов.
LOGIN_URL_FRAGMENT = "/users/login/"
NON_GITHUB_FRAGMENT = "должна вести на github"

# Ожидаемые JSON-ответы.
RESPONSE_COMPLETE_OK = {"status": "ok", "project_status": STATUS_CLOSED}
RESPONSE_PARTICIPATE_ON = {"status": "ok", "participant": True}
RESPONSE_PARTICIPATE_OFF = {"status": "ok", "participant": False}


def make_project_payload(name, *, description=PROJECT_DESCRIPTION, github_url="",
                         status=STATUS_OPEN):
    """Собрать тело POST-запроса для формы создания/редактирования проекта."""
    return {
        "name": name,
        "description": description,
        "github_url": github_url,
        "status": status,
    }


@override_settings(MEDIA_ROOT=MEDIA_TEST_ROOT)
class ProjectListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email=OWNER_EMAIL,
            password=DEFAULT_PASSWORD,
            name=OWNER_NAME,
            surname=OWNER_SURNAME,
        )
        for i in range(TOTAL_PROJECTS):
            Project.objects.create(
                owner=cls.owner,
                name=f"P{i:02d}",
                description=f"Desc {i}",
                status=STATUS_OPEN,
            )

    def test_root_redirects_to_project_list(self):
        response = self.client.get("/")
        self.assertRedirects(response, reverse("projects:list"))

    def test_pagination_12_per_page(self):
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["projects"]), PROJECTS_PER_PAGE)

    def test_projects_sorted_newest_first(self):
        response = self.client.get(reverse("projects:list"))
        projects = list(response.context["projects"])
        self.assertEqual(projects[0].name, NEWEST_PROJECT_NAME)
        self.assertEqual(projects[-1].name, OLDEST_ON_FIRST_PAGE_NAME)


@override_settings(MEDIA_ROOT=MEDIA_TEST_ROOT)
class ProjectCreateEditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email=CREATOR_EMAIL,
            password=DEFAULT_PASSWORD,
            name=CREATOR_NAME,
            surname=CREATOR_SURNAME,
        )
        self.other = User.objects.create_user(
            email=OTHER_EMAIL,
            password=DEFAULT_PASSWORD,
            name=OTHER_NAME,
            surname=OTHER_SURNAME,
        )

    def test_create_project_requires_login(self):
        response = self.client.get(reverse("projects:create"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(LOGIN_URL_FRAGMENT, response.url)

    def test_create_project_sets_owner_and_participant(self):
        self.client.login(username=CREATOR_EMAIL, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("projects:create"),
            make_project_payload(PROJECT_NAME_NEW),
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        project = Project.objects.get(name=PROJECT_NAME_NEW)
        self.assertEqual(project.owner, self.user)
        self.assertIn(self.user, project.participants.all())

    def test_edit_project_only_by_owner(self):
        project = Project.objects.create(
            owner=self.user,
            name=PROJECT_NAME_MINE,
            description=PROJECT_DESCRIPTION,
            status=STATUS_OPEN,
        )
        self.client.login(username=OTHER_EMAIL, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("projects:edit", args=[project.pk]),
            make_project_payload(PROJECT_NAME_HACKED),
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        project.refresh_from_db()
        self.assertEqual(project.name, PROJECT_NAME_MINE)  # Не должно поменяться

    def test_github_url_validation(self):
        self.client.login(username=CREATOR_EMAIL, password=DEFAULT_PASSWORD)
        response = self.client.post(
            reverse("projects:create"),
            make_project_payload(PROJECT_NAME_SHORT, github_url=GITHUB_BAD),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, NON_GITHUB_FRAGMENT)


@override_settings(MEDIA_ROOT=MEDIA_TEST_ROOT)
class ProjectActionsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email=ACTION_OWNER_EMAIL,
            password=DEFAULT_PASSWORD,
            name=ACTION_OWNER_NAME,
            surname=ACTION_OWNER_SURNAME,
        )
        self.user = User.objects.create_user(
            email=ACTION_USER_EMAIL,
            password=DEFAULT_PASSWORD,
            name=ACTION_USER_NAME,
            surname=ACTION_USER_SURNAME,
        )
        self.project = Project.objects.create(
            owner=self.owner,
            name=PROJECT_NAME_DEMO,
            description=PROJECT_DESCRIPTION,
            status=STATUS_OPEN,
        )

    def test_complete_project_by_owner(self):
        self.client.login(username=ACTION_OWNER_EMAIL, password=DEFAULT_PASSWORD)
        url = reverse("projects:complete", args=[self.project.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json(), RESPONSE_COMPLETE_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, STATUS_CLOSED)

    def test_complete_project_forbidden_for_non_owner(self):
        self.client.login(username=ACTION_USER_EMAIL, password=DEFAULT_PASSWORD)
        response = self.client.post(reverse("projects:complete", args=[self.project.pk]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_complete_already_closed_returns_400(self):
        self.project.status = STATUS_CLOSED
        self.project.save()
        self.client.login(username=ACTION_OWNER_EMAIL, password=DEFAULT_PASSWORD)
        response = self.client.post(reverse("projects:complete", args=[self.project.pk]))
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_toggle_participate_adds_and_removes(self):
        self.client.login(username=ACTION_USER_EMAIL, password=DEFAULT_PASSWORD)
        url = reverse("projects:toggle_participate", args=[self.project.pk])

        r1 = self.client.post(url)
        self.assertEqual(r1.status_code, HTTPStatus.OK)
        self.assertEqual(r1.json(), RESPONSE_PARTICIPATE_ON)
        self.assertIn(self.user, self.project.participants.all())

        r2 = self.client.post(url)
        self.assertEqual(r2.status_code, HTTPStatus.OK)
        self.assertEqual(r2.json(), RESPONSE_PARTICIPATE_OFF)
        self.assertNotIn(self.user, self.project.participants.all())

    def test_toggle_participate_requires_auth(self):
        response = self.client.post(
            reverse("projects:toggle_participate", args=[self.project.pk])
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(LOGIN_URL_FRAGMENT, response.url)

    def test_project_detail_renders(self):
        response = self.client.get(reverse("projects:detail", args=[self.project.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, PROJECT_NAME_DEMO)
