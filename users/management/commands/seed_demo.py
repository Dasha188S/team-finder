"""Управляющая команда: наполняет БД тестовыми пользователями и проектами.

Использование:
    python manage.py seed_demo            # idempotent: создаёт недостающие записи
    python manage.py seed_demo --reset    # удаляет демо-данные и создаёт заново

Создаются: суперпользователь admin@team-finder.local + 5 обычных пользователей,
у каждого хотя бы один проект, набор навыков и связи участия. Этого достаточно
для прохождения чек-листа ревьюера.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project
from users.models import Skill, User

DEMO_PASSWORD = "demo-pass-12345"
ADMIN_EMAIL = "admin@team-finder.local"
ADMIN_PASSWORD = "admin12345"

DEMO_USERS = [
    {
        "email": "anna@team-finder.local",
        "name": "Анна",
        "surname": "Иванова",
        "phone": "+79110000001",
        "github_url": "https://github.com/anna-demo",
        "about": "Frontend-разработчик, люблю React и UX-дизайн.",
        "skills": ["Python", "JavaScript", "React"],
    },
    {
        "email": "boris@team-finder.local",
        "name": "Борис",
        "surname": "Смирнов",
        "phone": "+79110000002",
        "github_url": "https://github.com/boris-demo",
        "about": "Backend-разработчик, Python/Django, PostgreSQL.",
        "skills": ["Python", "Django", "PostgreSQL"],
    },
    {
        "email": "viktoria@team-finder.local",
        "name": "Виктория",
        "surname": "Орлова",
        "phone": "+79110000003",
        "github_url": "https://github.com/viktoria-demo",
        "about": "Mobile-разработчик, увлечена Flutter и Kotlin.",
        "skills": ["Kotlin", "Flutter", "Dart"],
    },
    {
        "email": "grigory@team-finder.local",
        "name": "Григорий",
        "surname": "Петров",
        "phone": "+79110000004",
        "github_url": "https://github.com/grigory-demo",
        "about": "ML-инженер, NLP и компьютерное зрение.",
        "skills": ["Python", "PyTorch", "ML"],
    },
    {
        "email": "darya@team-finder.local",
        "name": "Дарья",
        "surname": "Жуйкова",
        "phone": "+79110000005",
        "github_url": "https://github.com/darya-demo",
        "about": "Fullstack-разработчик, Go и TypeScript.",
        "skills": ["Go", "TypeScript", "Docker"],
    },
]

DEMO_PROJECTS = [
    {
        "owner_email": "anna@team-finder.local",
        "name": "Дизайн-система TeamFinder",
        "description": (
            "Открытая дизайн-система с компонентами на React и Storybook. "
            "Ищем frontend-разработчиков и UX-дизайнеров."
        ),
        "github_url": "https://github.com/anna-demo/teamfinder-ui",
        "status": "open",
        "participants": ["boris@team-finder.local"],
    },
    {
        "owner_email": "boris@team-finder.local",
        "name": "API для заметок",
        "description": (
            "REST-API для приложения заметок на Django REST Framework. "
            "Цель — научиться работать с DRF и тестами."
        ),
        "github_url": "https://github.com/boris-demo/notes-api",
        "status": "open",
        "participants": ["anna@team-finder.local", "darya@team-finder.local"],
    },
    {
        "owner_email": "viktoria@team-finder.local",
        "name": "Мобильный планировщик дня",
        "description": (
            "Кросс-платформенное приложение на Flutter для планирования задач "
            "и привычек. Нужны мобильные разработчики и тестировщик."
        ),
        "github_url": "https://github.com/viktoria-demo/day-planner",
        "status": "open",
        "participants": [],
    },
    {
        "owner_email": "grigory@team-finder.local",
        "name": "Анализатор резюме",
        "description": (
            "Инструмент, который анализирует резюме разработчика "
            "и предлагает релевантные вакансии. Стек: PyTorch + FastAPI."
        ),
        "github_url": "",
        "status": "closed",
        "participants": ["boris@team-finder.local"],
    },
    {
        "owner_email": "darya@team-finder.local",
        "name": "TeamFinder инфраструктура",
        "description": (
            "Шаблон Docker Compose и GitHub Actions для пет-проектов "
            "на Django + PostgreSQL."
        ),
        "github_url": "https://github.com/darya-demo/teamfinder-infra",
        "status": "open",
        "participants": ["anna@team-finder.local", "viktoria@team-finder.local"],
    },
]


class Command(BaseCommand):
    help = "Создаёт тестовых пользователей, проекты и навыки для ревью."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить демо-данные перед созданием.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Удаляю демо-данные...")
            User.objects.filter(email__in=[u["email"] for u in DEMO_USERS]).delete()
            User.objects.filter(email=ADMIN_EMAIL).delete()
            Skill.objects.all().delete()

        admin = self._ensure_admin()
        users = self._ensure_users()
        self._ensure_projects(users)

        self.stdout.write(self.style.SUCCESS("Готово!"))
        self.stdout.write("")
        self.stdout.write("Тестовые учётные записи:")
        self.stdout.write(f"  admin: {admin.email} / {ADMIN_PASSWORD}")
        for u in DEMO_USERS:
            self.stdout.write(f"  user:  {u['email']} / {DEMO_PASSWORD}")

    def _ensure_admin(self) -> User:
        admin, created = User.objects.get_or_create(
            email=ADMIN_EMAIL,
            defaults={
                "name": "Админ",
                "surname": "TeamFinder",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "about": "Администратор демо-стенда.",
            },
        )
        if created:
            admin.set_password(ADMIN_PASSWORD)
            admin.save()
        return admin

    def _ensure_users(self) -> dict[str, User]:
        result: dict[str, User] = {}
        for data in DEMO_USERS:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "name": data["name"],
                    "surname": data["surname"],
                    "phone": data["phone"],
                    "github_url": data["github_url"],
                    "about": data["about"],
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            for skill_name in data["skills"]:
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                user.skills.add(skill)
            result[user.email] = user
        return result

    def _ensure_projects(self, users: dict[str, User]) -> None:
        for data in DEMO_PROJECTS:
            owner = users[data["owner_email"]]
            project, _ = Project.objects.get_or_create(
                owner=owner,
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "github_url": data["github_url"],
                    "status": data["status"],
                },
            )
            project.participants.add(owner)
            for email in data["participants"]:
                if email in users:
                    project.participants.add(users[email])
