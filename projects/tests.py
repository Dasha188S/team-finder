"""Автотесты приложения projects."""
from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import User

from .models import Project


@override_settings(MEDIA_ROOT="/tmp/team-finder-media-test")
class ProjectListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="proj@example.com",
            password="pwd1234567",
            name="Pj",
            surname="Owner",
        )
        for i in range(15):
            Project.objects.create(
                owner=cls.owner,
                name=f"P{i:02d}",
                description=f"Desc {i}",
                status="open",
            )

    def test_root_redirects_to_project_list(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/projects/list/")

    def test_pagination_12_per_page(self):
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["projects"]), 12)

    def test_projects_sorted_newest_first(self):
        response = self.client.get(reverse("projects:list"))
        projects = list(response.context["projects"])
        self.assertEqual(projects[0].name, "P14")
        self.assertEqual(projects[-1].name, "P03")


@override_settings(MEDIA_ROOT="/tmp/team-finder-media-test")
class ProjectCreateEditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="cre@example.com",
            password="pwd1234567",
            name="Cre",
            surname="Ate",
        )
        self.other = User.objects.create_user(
            email="otr@example.com",
            password="pwd1234567",
            name="Otr",
            surname="User",
        )

    def test_create_project_requires_login(self):
        response = self.client.get(reverse("projects:create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    def test_create_project_sets_owner_and_participant(self):
        self.client.login(username="cre@example.com", password="pwd1234567")
        response = self.client.post(
            reverse("projects:create"),
            {
                "name": "NewProj",
                "description": "x",
                "github_url": "",
                "status": "open",
            },
        )
        self.assertEqual(response.status_code, 302)
        project = Project.objects.get(name="NewProj")
        self.assertEqual(project.owner, self.user)
        self.assertIn(self.user, project.participants.all())

    def test_edit_project_only_by_owner(self):
        project = Project.objects.create(
            owner=self.user, name="Mine", description="x", status="open"
        )
        self.client.login(username="otr@example.com", password="pwd1234567")
        response = self.client.post(
            reverse("projects:edit", args=[project.pk]),
            {
                "name": "Hacked",
                "description": "x",
                "github_url": "",
                "status": "open",
            },
        )
        self.assertEqual(response.status_code, 302)
        project.refresh_from_db()
        self.assertEqual(project.name, "Mine")  # Не должно поменяться

    def test_github_url_validation(self):
        self.client.login(username="cre@example.com", password="pwd1234567")
        response = self.client.post(
            reverse("projects:create"),
            {
                "name": "X",
                "description": "",
                "github_url": "https://gitlab.com/x",
                "status": "open",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "должна вести на github")


@override_settings(MEDIA_ROOT="/tmp/team-finder-media-test")
class ProjectActionsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="own@example.com",
            password="pwd1234567",
            name="Own",
            surname="Er",
        )
        self.user = User.objects.create_user(
            email="usr@example.com",
            password="pwd1234567",
            name="Usr",
            surname="Or",
        )
        self.project = Project.objects.create(
            owner=self.owner, name="Demo", description="x", status="open"
        )

    def test_complete_project_by_owner(self):
        self.client.login(username="own@example.com", password="pwd1234567")
        url = reverse("projects:complete", args=[self.project.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "project_status": "closed"})
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "closed")

    def test_complete_project_forbidden_for_non_owner(self):
        self.client.login(username="usr@example.com", password="pwd1234567")
        response = self.client.post(reverse("projects:complete", args=[self.project.pk]))
        self.assertEqual(response.status_code, 403)

    def test_complete_already_closed_returns_400(self):
        self.project.status = "closed"
        self.project.save()
        self.client.login(username="own@example.com", password="pwd1234567")
        response = self.client.post(reverse("projects:complete", args=[self.project.pk]))
        self.assertEqual(response.status_code, 400)

    def test_toggle_participate_adds_and_removes(self):
        self.client.login(username="usr@example.com", password="pwd1234567")
        url = reverse("projects:toggle_participate", args=[self.project.pk])

        r1 = self.client.post(url)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json(), {"status": "ok", "participant": True})
        self.assertIn(self.user, self.project.participants.all())

        r2 = self.client.post(url)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json(), {"status": "ok", "participant": False})
        self.assertNotIn(self.user, self.project.participants.all())

    def test_toggle_participate_requires_auth(self):
        response = self.client.post(
            reverse("projects:toggle_participate", args=[self.project.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    def test_project_detail_renders(self):
        response = self.client.get(reverse("projects:detail", args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo")
