"""Автотесты приложения users."""
import json

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Skill, User


@override_settings(MEDIA_ROOT="/tmp/team-finder-media-test")
class UserModelTests(TestCase):
    def test_create_user_generates_avatar_and_hashes_password(self):
        user = User.objects.create_user(
            email="alice@example.com",
            password="strong-pass-1",
            name="Alice",
            surname="Wonderland",
        )
        self.assertTrue(user.check_password("strong-pass-1"))
        self.assertNotEqual(user.password, "strong-pass-1")
        self.assertTrue(user.avatar)
        self.assertTrue(user.avatar.name.endswith(".png"))

    def test_email_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_create_superuser_flags(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="admin12345",
            name="Admin",
            surname="Root",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


@override_settings(MEDIA_ROOT="/tmp/team-finder-media-test")
class AuthFlowTests(TestCase):
    def test_register_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Bob",
                "surname": "Builder",
                "email": "bob@example.com",
                "password": "build-it-strong-1",
            },
        )
        self.assertRedirects(response, "/users/login/")
        self.assertTrue(User.objects.filter(email="bob@example.com").exists())

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            email="dup@example.com",
            password="qwerty12345",
            name="Dup",
            surname="User",
        )
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Dup",
                "surname": "Two",
                "email": "dup@example.com",
                "password": "qwerty12345",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "уже зарегистрирован")

    def test_login_success_and_logout(self):
        User.objects.create_user(
            email="login@example.com",
            password="strong-pass-1",
            name="Log",
            surname="In",
        )
        login_resp = self.client.post(
            reverse("users:login"),
            {"email": "login@example.com", "password": "strong-pass-1"},
        )
        self.assertRedirects(login_resp, "/projects/list/")

        logout_resp = self.client.get(reverse("users:logout"))
        self.assertRedirects(logout_resp, "/projects/list/")

    def test_login_wrong_password_shows_error(self):
        User.objects.create_user(
            email="login2@example.com",
            password="correct-pass-1",
            name="Log",
            surname="In",
        )
        response = self.client.post(
            reverse("users:login"),
            {"email": "login2@example.com", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Неверный email или пароль")


@override_settings(MEDIA_ROOT="/tmp/team-finder-media-test")
class ParticipantsListTests(TestCase):
    def setUp(self):
        self.python_user = User.objects.create_user(
            email="py@example.com",
            password="pwd1234567",
            name="Py",
            surname="Dev",
        )
        self.go_user = User.objects.create_user(
            email="go@example.com",
            password="pwd1234567",
            name="Go",
            surname="Dev",
        )
        python_skill = Skill.objects.create(name="Python")
        Skill.objects.create(name="Go")
        self.python_user.skills.add(python_skill)

    def test_list_renders(self):
        response = self.client.get(reverse("users:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Py")
        self.assertContains(response, "Go")

    def test_skill_filter(self):
        response = self.client.get(reverse("users:list"), {"skill": "Python"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Py Dev")
        self.assertNotContains(response, "Go Dev")


@override_settings(MEDIA_ROOT="/tmp/team-finder-media-test")
class SkillsAutocompleteAndManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="pwd1234567",
            name="Own",
            surname="Er",
        )
        self.other = User.objects.create_user(
            email="other@example.com",
            password="pwd1234567",
            name="Oth",
            surname="Er",
        )
        Skill.objects.create(name="Django")
        Skill.objects.create(name="Docker")
        Skill.objects.create(name="DevOps")

    def test_autocomplete_returns_first_ten(self):
        for i in range(15):
            Skill.objects.create(name=f"Auto{i:02d}")
        response = self.client.get(reverse("users:skills_autocomplete"), {"q": "Auto"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 10)
        self.assertEqual(data[0]["name"], "Auto00")

    def test_add_skill_by_name_creates_new(self):
        self.client.login(username="owner@example.com", password="pwd1234567")
        url = reverse("users:skills_add", args=[self.user.pk])
        response = self.client.post(
            url,
            data=json.dumps({"name": "Rust"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["created"])
        self.assertTrue(body["added"])
        self.assertTrue(self.user.skills.filter(name="Rust").exists())

    def test_add_skill_forbidden_for_other_user(self):
        self.client.login(username="other@example.com", password="pwd1234567")
        url = reverse("users:skills_add", args=[self.user.pk])
        response = self.client.post(
            url,
            data=json.dumps({"name": "Rust"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_remove_skill(self):
        skill = Skill.objects.get(name="Django")
        self.user.skills.add(skill)
        self.client.login(username="owner@example.com", password="pwd1234567")
        url = reverse("users:skills_remove", args=[self.user.pk, skill.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user.skills.filter(pk=skill.pk).exists())


@override_settings(MEDIA_ROOT="/tmp/team-finder-media-test")
class EditProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="edit@example.com",
            password="pwd1234567",
            name="Ed",
            surname="It",
        )
        self.client.login(username="edit@example.com", password="pwd1234567")

    def test_edit_profile_normalises_phone(self):
        response = self.client.post(
            reverse("users:edit_profile"),
            {
                "name": "Ed",
                "surname": "It",
                "about": "test",
                "phone": "89110000010",
                "github_url": "https://github.com/ed-it",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+79110000010")

    def test_edit_profile_rejects_non_github_url(self):
        response = self.client.post(
            reverse("users:edit_profile"),
            {
                "name": "Ed",
                "surname": "It",
                "about": "",
                "phone": "",
                "github_url": "https://gitlab.com/ed-it",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "должна вести на github")

    def test_edit_profile_rejects_invalid_phone(self):
        response = self.client.post(
            reverse("users:edit_profile"),
            {
                "name": "Ed",
                "surname": "It",
                "about": "",
                "phone": "12345",
                "github_url": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "формате")
