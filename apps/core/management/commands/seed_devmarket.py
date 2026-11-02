from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from marketplace.models import Category, Project
from accounts.models import Profile
from proposals.models import Proposal
from orders.models import Order
from payments.models import Payment
from datetime import date, timedelta
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = "Seed DevMarket with realistic categories, demo users, sample projects, and active data"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding DevMarket categories...")
        categories_data = [
            {
                "name": "Web Development",
                "slug": "web-development",
                "description": "Full-stack web apps, React, Vue, Next.js, Django, FastAPI, APIs",
                "icon": "code",
                "order": 1,
            },
            {
                "name": "AI & Machine Learning",
                "slug": "ai-machine-learning",
                "description": "LLM integrations, agentic workflows, PyTorch, computer vision, NLP",
                "icon": "cpu",
                "order": 2,
            },
            {
                "name": "Cloud & DevOps",
                "slug": "cloud-devops",
                "description": "AWS, GCP, Azure, Docker, Kubernetes, CI/CD, Terraform infrastructure",
                "icon": "cloud",
                "order": 3,
            },
            {
                "name": "Mobile Development",
                "slug": "mobile-development",
                "description": "iOS, Android, React Native, Flutter, Swift, Kotlin native apps",
                "icon": "smartphone",
                "order": 4,
            },
            {
                "name": "UI/UX Design",
                "slug": "ui-ux-design",
                "description": "Figma design systems, wireframing, interactive prototypes, user research",
                "icon": "palette",
                "order": 5,
            },
            {
                "name": "Cybersecurity",
                "slug": "cybersecurity",
                "description": "Penetration testing, security audits, authentication, OWASP compliance",
                "icon": "shield",
                "order": 6,
            },
        ]

        created_categories = {}
        for cdata in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cdata["slug"],
                defaults={
                    "name": cdata["name"],
                    "description": cdata["description"],
                    "icon": cdata["icon"],
                    "order": cdata["order"],
                    "is_featured": True,
                },
            )
            created_categories[cat.slug] = cat
            status = "Created" if created else "Exists"
            self.stdout.write(f"  Category: {cat.name} ({status})")

        self.stdout.write("\nSeeding demo users...")
        # 1. Superuser
        if not User.objects.filter(username="admin").exists():
            admin_user = User.objects.create_superuser(
                username="admin",
                email="admin@devmarket.com",
                password="AdminPassword123!",
                first_name="Marketplace",
                last_name="Administrator",
                role=User.Role.ADMIN,
            )
            self.stdout.write("  Created superuser 'admin' with password 'AdminPassword123!'")
        else:
            self.stdout.write("  Superuser 'admin' already exists")

        # 2. Demo Client
        client_user, created = User.objects.get_or_create(
            username="alex_client",
            defaults={
                "email": "alex@techventures.io",
                "first_name": "Alex",
                "last_name": "Mercer",
                "role": User.Role.CLIENT,
                "location": "Austin, TX, USA",
            },
        )
        if created:
            client_user.set_password("DevMarket2026!")
            client_user.save()
            client_user.profile.headline = "Founder & CTO @ TechVentures"
            client_user.profile.bio = "Building high-growth AI and SaaS products. Looking for reliable full-stack developers and DevOps engineers."
            client_user.profile.total_spent = Decimal("4500.00")
            client_user.profile.save()
            self.stdout.write("  Created demo client 'alex_client' (password: DevMarket2026!)")

        # 3. Demo Freelancer 1
        dev_user, created = User.objects.get_or_create(
            username="sarah_dev",
            defaults={
                "email": "sarah.chen@devmail.com",
                "first_name": "Sarah",
                "last_name": "Chen",
                "role": User.Role.FREELANCER,
                "location": "San Francisco, CA, USA",
            },
        )
        if created:
            dev_user.set_password("DevMarket2026!")
            dev_user.save()
            dev_user.profile.headline = "Senior Full-Stack Engineer | Python, React & Cloud"
            dev_user.profile.bio = "Over 7 years of experience building resilient web applications, REST/GraphQL APIs, and scalable microservices. Passionate about clean code, strong test coverage, and intuitive UX."
            dev_user.profile.skills = "Python, Django, React, TypeScript, Tailwind CSS, PostgreSQL, MongoDB, Docker"
            dev_user.profile.experience_level = Profile.ExperienceLevel.EXPERT
            dev_user.profile.hourly_rate = Decimal("75.00")
            dev_user.profile.rating = 4.95
            dev_user.profile.reviews_count = 14
            dev_user.profile.total_earned = Decimal("8200.00")
            dev_user.profile.github_url = "https://github.com"
            dev_user.profile.portfolio_website = "https://sarahchen.dev"
            dev_user.profile.save()
            self.stdout.write("  Created demo freelancer 'sarah_dev' (password: DevMarket2026!)")

        # 4. Demo Freelancer 2
        cloud_user, created = User.objects.get_or_create(
            username="david_cloud",
            defaults={
                "email": "david.k@cloudcraft.io",
                "first_name": "David",
                "last_name": "Kim",
                "role": User.Role.FREELANCER,
                "location": "Seattle, WA, USA",
            },
        )
        if created:
            cloud_user.set_password("DevMarket2026!")
            cloud_user.save()
            cloud_user.profile.headline = "DevOps & Cloud Architect | Kubernetes, AWS, Terraform"
            cloud_user.profile.bio = "Specializing in high-availability cloud architecture, zero-downtime CI/CD pipelines, container orchestration, and security compliance."
            cloud_user.profile.skills = "AWS, Kubernetes, Docker, Terraform, CI/CD, Python, Linux, Bash"
            cloud_user.profile.experience_level = Profile.ExperienceLevel.EXPERT
            cloud_user.profile.hourly_rate = Decimal("90.00")
            cloud_user.profile.rating = 5.0
            cloud_user.profile.reviews_count = 9
            cloud_user.profile.total_earned = Decimal("6100.00")
            cloud_user.profile.github_url = "https://github.com"
            cloud_user.profile.save()
            self.stdout.write("  Created demo freelancer 'david_cloud' (password: DevMarket2026!)")

        # Seed sample projects
        self.stdout.write("\nSeeding sample projects...")
        sample_projects = [
            {
                "title": "Build Modern SaaS Analytics Dashboard in Next.js & Django REST",
                "category": created_categories["web-development"],
                "description": "We are seeking a senior full-stack developer to build a modern analytics dashboard for our B2B SaaS platform.\n\nRequirements:\n- Interactive charts and KPI metrics\n- Role-based team permissions\n- Clean REST API endpoints with Django\n- Modern frontend with React/Next.js and Tailwind CSS\n- Responsive across desktop, tablet, and mobile",
                "required_skills": "Python, Django, React, Next.js, Tailwind CSS, REST API",
                "budget": Decimal("1800.00"),
                "project_type": Project.ProjectType.FIXED,
                "deadline": date.today() + timedelta(days=21),
                "status": Project.Status.OPEN,
            },
            {
                "title": "LLM Intelligent Agent Integration for Customer Support Automation",
                "category": created_categories["ai-machine-learning"],
                "description": "Looking for an AI engineer to integrate an LLM agent that processes incoming user queries, queries our knowledge base via vector embeddings, and summarizes action items.\n\nKey expectations:\n- Python backend with LangChain/LlamaIndex or direct API\n- Guardrails and response validation\n- Fast latency and structured JSON outputs",
                "required_skills": "Python, PyTorch, LLM, LangChain, Vector DB, FastAPI",
                "budget": Decimal("2400.00"),
                "project_type": Project.ProjectType.FIXED,
                "deadline": date.today() + timedelta(days=30),
                "status": Project.Status.OPEN,
            },
            {
                "title": "Multi-Region Kubernetes Cluster Deployment with Terraform & CI/CD",
                "category": created_categories["cloud-devops"],
                "description": "Need an experienced DevOps engineer to design and automate an EKS/GKE cluster deployment using Terraform, with automated GitHub Actions CI/CD workflows, monitoring via Prometheus/Grafana, and SSL termination.",
                "required_skills": "AWS, Kubernetes, Terraform, Docker, GitHub Actions, Linux",
                "budget": Decimal("1500.00"),
                "project_type": Project.ProjectType.FIXED,
                "deadline": date.today() + timedelta(days=14),
                "status": Project.Status.OPEN,
            },
        ]

        for pdata in sample_projects:
            proj, p_created = Project.objects.get_or_create(
                title=pdata["title"],
                client=client_user,
                defaults={
                    "category": pdata["category"],
                    "description": pdata["description"],
                    "required_skills": pdata["required_skills"],
                    "budget": pdata["budget"],
                    "project_type": pdata["project_type"],
                    "deadline": pdata["deadline"],
                    "status": pdata["status"],
                },
            )
            status = "Created" if p_created else "Exists"
            self.stdout.write(f"  Project: '{proj.title}' ({status})")

        self.stdout.write(self.style.SUCCESS("\nDevMarket successfully seeded!"))

