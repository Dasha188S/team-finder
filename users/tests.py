"""Автотесты приложения users."""
import json
from http import HTTPStatus

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Skill, User

# === Общие константы ========================================================

MEDIA_TEST_ROOT = "/tmp/team-finder-media-test"

# Пароли. Один — стандартный для большинства фикстур,
# второй — отдельный, для проверки логина с неверным паролем.
DEFAULT_PASSWORD = "demo-pwd-1234567"
ALT_PASSWORD = "strong-pass-1"
WRONG_PASSWORD = "wrong"
LOGIN_CORRECT_PASSWORD = "correct-pass-1"
BUILDER_PASSWORD = "build-it-strong-1"
QWERTY_PASSWORD = "qwerty12345"
ADMIN_PASSWORD = "admin12345"

# Имена/фамилии (используются повторно в фикстурах).
ALICE_NAME, ALICE_SURNAME = "Alice", "Wonderland"
ADMIN_NAME, ADMIN_SURNAME = "Admin", "Root"
BOB_NAME, BOB_SURNAME = "Bob", "Builder"
DUP_NAME, DUP_SURNAME_ONE, DUP_SURNAME_TWO = "Dup", "User", "Two"
LOGIN_NAME, LOGIN_SURNAME = "Log", "In"
PY_NAME, GO_NAME = "Py", "Go"
DEV_SURNAME = "Dev"
OWNER_NAME, OWNER_SURNAME = "Own", "Er"
OTHER_NAME, OTHER_SURNAME = "Oth", "Er"
EDIT_NAME, EDIT_SURNAME = "Ed", "It"

# Email-ы тестовых пользователей.
ALICE_EMAIL = "alice@example.com"
ADMIN_EMAIL = "admin@example.com"
BOB_EMAIL = "bob@example.com"
DUP_EMAIL = "dup@example.com"
LOGIN_EMAIL = "login@example.com"
LOGIN_EMAIL_2 = "login2@example.com"
PY_EMAIL = "py@example.com"
GO_EMAIL = "go@example.com"
OWNER_EMAIL = "owner@example.com"
OTHER_EMAIL = "other@example.com"
EDIT_EMAIL = "edit@example.com"

# Названия навыков.
SKILL_PYTHON = "Python"
SKILL_GO_NAME = "Go"
SKILL_DJANGO = "Django"
SKILL_DOCKER = "Docker"
SKILL_DEVOPS = "DevOps"
SKILL_RUST = "Rust"

# Параметры автодополнения.
AUTOCOMPLETE_PREFIX = "Auto"
AUTOCOMPLETE_TOTAL_SKILLS = 15
AUTOCOMPLETE_LIMIT = 10
AUTOCOMPLETE_FIRST_NAME = f"{AUTOCOMPLETE_PREFIX}00"

# URL и редиректы.
LOGIN_REDIRECT_URL = "/projects/list/"
REGISTER_REDIRECT_URL = "/users/login/"

# Поля профиля для тестов редактирования.
PROFILE_ABOUT = "test"
PROFILE_GITHUB_OK = "https://github.com/ed-it"
PROFILE_GITHUB_BAD = "https://gitlab.com/ed-it"
PROFILE_PHONE_RAW = "89110000010"
PROFILE_PHONE_NORMALIZED = "+79110000010"
PROFILE_PHONE_INVALID = "12345"

# Подстроки, которые ищем в HTML-ответах.
DUPLICATE_EMAIL_FRAGMENT = "уже зарегистрирован"
INVALID_CREDENTIALS_FRAGMENT = "Неверный email или пароль"
NON_GITHUB_FRAGMENT = "должна вести на github"
PHONE_FORMAT_FRAGMENT = "формате"


@override_settings(MEDIA_ROOT=MEDIA_TEST_ROOT)
class UserModelTests(TestCase):
    def test_create_user_generates_avatar_and_hashes_password(self):
        user = User.objects.create_user(
            email=ALICE_EMAIL,
            password=ALT_PASSWORD,
            name=ALICE_NAME,
            surname=ALICE_SURNAME,
        )
        self.assertTrue(user.check_password(ALT_PASSWORD))
        self.assertNotEqual(user.password, ALT_PASSWORD)
        self.assertTrue(user.avatar)
        self.assertTrue(user.avatar.name.endswith(".png"))

    def test_email_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_create_superuser_flags(self):
        admin = User.objects.create_superuser(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            name=ADMIN_NAME,
            surname=ADMIN_SURNAME,
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


@override_settings(MEDIA_ROOT=MEDIA_TEST_ROOT)
class AuthFlowTests(TestCase):
    def test_register_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": BOB_NAME,
                "surname": BOB_SURNAME,
                "email": BOB_EMAIL,
                "password": BUILDER_PASSWORD,
            },
        )
        self.assertRedirects(response, REGISTER_REDIRECT_URL)
        self.assertTrue(User.objects.filter(email=BOB_EMAIL).exists())

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            email=DUP_EMAIL,
            password=QWERTY_PASSWORD,
            name=DUP_NAME,
            surname=DUP_SURNAME_ONE,
        )
        response = self.client.post(
            reverse("users:register"),
            {
                "name": DUP_NAME,
                "surname": DUP_SURNAME_TWO,
                "email": DUP_EMAIL,
                "password": QWERTY_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, DUPLICATE_EMAIL_FRAGMENT)

    def test_login_success_and_logout(self):
        User.objects.create_user(
            email=LOGIN_EMAIL,
            password=ALT_PASSWORD,
            name=LOGIN_NAME,
            surname=LOGIN_SURNAME,
        )
        login_resp = self.client.post(
            reverse("users:login"),
            {"email": LOGIN_EMAIL, "password": ALT_PASSWORD},
        )
        self.assertRedirects(login_resp, LOGIN_REDIRECT_URL)

        logout_resp = self.client.get(reverse("users:logout"))
        self.assertRedirects(logout_resp, LOGIN_REDIRECT_URL)

    def test_login_wrong_password_shows_error(self):
        User.objects.create_user(
            email=LOGIN_EMAIL_2,
            password=LOGIN_CORRECT_PASSWORD,
            name=LOGIN_NAME,
            surname=LOGIN_SURNAME,
        )
        response = self.client.post(
            reverse("users:login"),
            {"email": LOGIN_EMAIL_2, "password": WRONG_PASSWORD},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, INVALID_CREDENTIALS_FRAGMENT)


@override_settings(MEDIA_ROOT=MEDIA_TEST_ROOT)
class ParticipantsListTests(TestCase):
    def setUp(self):
        self.python_user = User.objects.create_user(
            email=PY_EMAIL,
            password=DEFAULT_PASSWORD,
            name=PY_NAME,
            surname=DEV_SURNAME,
        )
        self.go_user = User.objects.create_user(
            email=GO_EMAIL,
            password=DEFAULT_PASSWORD,
            name=GO_NAME,
            surname=DEV_SURNAME,
        )
        python_skill = Skill.objects.create(name=SKILL_PYTHON)
        Skill.objects.create(name=SKILL_GO_NAME)
        self.python_user.skills.add(python_skill)

    def test_list_renders(self):
        response = self.client.get(reverse("users:list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, PY_NAME)
        self.assertContains(response, GO_NAME)

    def test_skill_filter(self):
        response = self.client.get(reverse("users:list"), {"skill": SKILL_PYTHON})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, f"{PY_NAME} {DEV_SURNAME}")
        self.assertNotContains(response, f"{GO_NAME} {DEV_SURNAME}")


@override_settings(MEDIA_ROOT=MEDIA_TEST_ROOT)
class SkillsAutocompleteAndManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email=OWNER_EMAIL,
            password=DEFAULT_PASSWORD,
            name=OWNER_NAME,
            surname=OWNER_SURNAME,
        )
        self.other = User.objects.create_user(
            email=OTHER_EMAIL,
            password=DEFAULT_PASSWORD,
            name=OTHER_NAME,
            surname=OTHER_SURNAME,
        )
        Skill.objects.create(name=SKILL_DJANGO)
        Skill.objects.create(name=SKILL_DOCKER)
        Skill.objects.create(name=SKILL_DEVOPS)

    def test_autocomplete_returns_first_ten(self):
        for i in range(AUTOCOMPLETE_TOTAL_SKILLS):
            Skill.objects.create(name=f"{AUTOCOMPLETE_PREFIX}{i:02d}")
        response = self.client.get(
            reverse("users:skills_autocomplete"),
            {"q": AUTOCOMPLETE_PREFIX},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data), AUTOCOMPLETE_LIMIT)
        self.assertEqual(data[0]["name"], AUTOCOMPLETE_FIRST_NAME)

    def test_add_skill_by_name_creates_new(self):
        self.client.login(username=OWNER_EMAIL, password=DEFAULT_PASSWORD)
        url = reverse("users:skills_add", args=[self.user.pk])
        response = self.client.post(
            url,
            data=json.dumps({"name": SKILL_RUST}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        body = response.json()
        self.assertTrue(body["created"])
        self.assertTrue(body["added"])
        self.assertTrue(self.user.skills.filter(name=SKILL_RUST).exists())

    def test_add_skill_forbidden_for_other_user(self):
        self.client.login(username=OTHER_EMAIL, password=DEFAULT_PASSWORD)
        url = reverse("users:skills_add", args=[self.user.pk])
        response = self.client.post(
            url,
            data=json.dumps({"name": SKILL_RUST}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_remove_skill(self):
        skill = Skill.objects.get(name=SKILL_DJANGO)
        self.user.skills.add(skill)
        self.client.login(username=OWNER_EMAIL, password=DEFAULT_PASSWORD)
        url = reverse("users:skills_remove", args=[self.user.pk, skill.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(self.user.skills.filter(pk=skill.pk).exists())


@override_settings(MEDIA_ROOT=MEDIA_TEST_ROOT)
class EditProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email=EDIT_EMAIL,
            password=DEFAULT_PASSWORD,
            name=EDIT_NAME,
            surname=EDIT_SURNAME,
        )
        self.client.login(username=EDIT_EMAIL, password=DEFAULT_PASSWORD)

    def test_edit_profile_normalises_phone(self):
        response = self.client.post(
            reverse("users:edit_profile"),
            {
                "name": EDIT_NAME,
                "surname": EDIT_SURNAME,
                "about": PROFILE_ABOUT,
                "phone": PROFILE_PHONE_RAW,
                "github_url": PROFILE_GITHUB_OK,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, PROFILE_PHONE_NORMALIZED)

    def test_edit_profile_rejects_non_github_url(self):
        response = self.client.post(
            reverse("users:edit_profile"),
            {
                "name": EDIT_NAME,
                "surname": EDIT_SURNAME,
                "about": "",
                "phone": "",
                "github_url": PROFILE_GITHUB_BAD,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, NON_GITHUB_FRAGMENT)

    def test_edit_profile_rejects_invalid_phone(self):
        response = self.client.post(
            reverse("users:edit_profile"),
            {
                "name": EDIT_NAME,
                "surname": EDIT_SURNAME,
                "about": "",
                "phone": PROFILE_PHONE_INVALID,
                "github_url": "",
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, PHONE_FORMAT_FRAGMENT)
