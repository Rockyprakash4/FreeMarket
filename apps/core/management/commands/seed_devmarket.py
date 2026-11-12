from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from marketplace.models import Category, Project, Service
from accounts.models import Profile
from proposals.models import Proposal
from orders.models import Order, Milestone
from payments.models import Payment
from reviews.models import Review
from disputes.models import Dispute
from messaging.models import Conversation, Message
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Seed SkillSphere with realistic categories, demo users, services, projects, orders, milestones, disputes, and reviews"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding SkillSphere categories...")
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

        self.stdout.write("\nSeeding verified users...")
        # 1. Admin
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@skillsphere.io",
                "first_name": "Executive",
                "last_name": "Admin",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_verified": True,
            },
        )
        admin_user.set_password("AdminPassword123!")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_verified = True
        admin_user.save()

        # 2. Client Alex
        client_user, created = User.objects.get_or_create(
            username="alex_client",
            defaults={
                "email": "alex@techventures.io",
                "first_name": "Alex",
                "last_name": "Mercer",
                "role": User.Role.CLIENT,
                "location": "Austin, TX, USA",
                "is_verified": True,
            },
        )
        client_user.set_password("DevMarket2026!")
        client_user.is_verified = True
        client_user.save()
        client_user.profile.headline = "Founder & CTO @ TechVentures"
        client_user.profile.bio = "Building high-growth AI and SaaS products. Looking for reliable full-stack developers and DevOps engineers."
        client_user.profile.total_spent = Decimal("4500.00")
        client_user.profile.save()

        # 3. Freelancer Sarah
        dev_user, _ = User.objects.get_or_create(
            username="sarah_dev",
            defaults={
                "email": "sarah.chen@skillsphere.io",
                "first_name": "Sarah",
                "last_name": "Chen",
                "role": User.Role.FREELANCER,
                "location": "San Francisco, CA, USA",
                "is_verified": True,
            },
        )
        dev_user.set_password("DevMarket2026!")
        dev_user.is_verified = True
        dev_user.save()
        dev_user.profile.headline = "Senior Full-Stack Engineer | Python, React & Cloud"
        dev_user.profile.bio = "Over 7 years of experience building resilient web applications, REST/GraphQL APIs, and scalable microservices. Passionate about clean code, strong test coverage, and intuitive UX."
        dev_user.profile.skills = "Python, Django, React, TypeScript, Tailwind CSS, PostgreSQL, MongoDB, Docker"
        dev_user.profile.experience_level = Profile.ExperienceLevel.EXPERT
        dev_user.profile.hourly_rate = Decimal("75.00")
        dev_user.profile.verification_status = Profile.VerificationStatus.VERIFIED
        dev_user.profile.ai_profile_score = 95
        dev_user.profile.rating = 4.95
        dev_user.profile.reviews_count = 14
        dev_user.profile.total_earned = Decimal("8200.00")
        dev_user.profile.github_url = "https://github.com"
        dev_user.profile.portfolio_website = "https://sarahchen.dev"
        dev_user.profile.save()

        # 4. Freelancer David
        cloud_user, _ = User.objects.get_or_create(
            username="david_cloud",
            defaults={
                "email": "david.k@cloudcraft.io",
                "first_name": "David",
                "last_name": "Kim",
                "role": User.Role.FREELANCER,
                "location": "Seattle, WA, USA",
                "is_verified": True,
            },
        )
        cloud_user.set_password("DevMarket2026!")
        cloud_user.is_verified = True
        cloud_user.save()
        cloud_user.profile.headline = "DevOps & Cloud Architect | Kubernetes, AWS, Terraform"
        cloud_user.profile.bio = "Specializing in high-availability cloud architecture, zero-downtime CI/CD pipelines, container orchestration, and security compliance."
        cloud_user.profile.skills = "AWS, Kubernetes, Docker, Terraform, CI/CD, Python, Linux, Bash"
        cloud_user.profile.experience_level = Profile.ExperienceLevel.EXPERT
        cloud_user.profile.hourly_rate = Decimal("90.00")
        cloud_user.profile.verification_status = Profile.VerificationStatus.VERIFIED
        cloud_user.profile.ai_profile_score = 92
        cloud_user.profile.rating = 5.0
        cloud_user.profile.reviews_count = 9
        cloud_user.profile.total_earned = Decimal("6100.00")
        cloud_user.profile.github_url = "https://github.com"
        cloud_user.profile.save()

        # Seed Freelance Services (Gigs)
        self.stdout.write("\nSeeding freelance service packages...")
        service1, _ = Service.objects.get_or_create(
            title="Production-Ready Django REST API with JWT & Docker",
            freelancer=dev_user,
            defaults={
                "category": created_categories["web-development"],
                "description": "Complete production API architecture with clean views, PostgreSQL/MongoDB support, automated pytest suites, and Docker containerization.",
                "price": Decimal("250.00"),
                "delivery_time_days": 4,
                "technologies": "Django, Python, REST API, Docker, Pytest",
                "views_count": 42,
            },
        )

        service2, _ = Service.objects.get_or_create(
            title="Multi-Region Kubernetes CI/CD Pipeline Automation",
            freelancer=cloud_user,
            defaults={
                "category": created_categories["cloud-devops"],
                "description": "Automate deployment manifests, Helm charts, GitHub Actions workflows, and Prometheus/Grafana metric alerts for high availability.",
                "price": Decimal("400.00"),
                "delivery_time_days": 5,
                "technologies": "Kubernetes, AWS, Terraform, Docker, Helm",
                "views_count": 31,
            },
        )

        # Seed Sample Projects
        self.stdout.write("\nSeeding sample projects...")
        p1, _ = Project.objects.get_or_create(
            title="Build Modern SaaS Analytics Dashboard in Next.js & Django REST",
            client=client_user,
            defaults={
                "category": created_categories["web-development"],
                "description": "We are seeking a senior full-stack developer to build a modern analytics dashboard for our B2B SaaS platform.\n\nRequirements:\n- Interactive charts and KPI metrics\n- Role-based team permissions\n- Clean REST API endpoints with Django\n- Modern frontend with React/Next.js and Tailwind CSS\n- Responsive across desktop, tablet, and mobile",
                "required_skills": "Python, Django, React, Next.js, Tailwind CSS, REST API",
                "complexity": Project.Complexity.INTERMEDIATE,
                "budget": Decimal("1800.00"),
                "project_type": Project.ProjectType.FIXED,
                "deadline": date.today() + timedelta(days=21),
                "status": Project.Status.OPEN,
            },
        )

        p2, _ = Project.objects.get_or_create(
            title="LLM Intelligent Agent Integration for Customer Support Automation",
            client=client_user,
            defaults={
                "category": created_categories["ai-machine-learning"],
                "description": "Looking for an AI engineer to integrate an LLM agent that processes incoming user queries, queries our knowledge base via vector embeddings, and summarizes action items.\n\nKey expectations:\n- Python backend with LangChain/LlamaIndex or direct API\n- Guardrails and response validation\n- Fast latency and structured JSON outputs",
                "required_skills": "Python, PyTorch, LLM, LangChain, Vector DB, FastAPI",
                "complexity": Project.Complexity.EXPERT,
                "budget": Decimal("2400.00"),
                "project_type": Project.ProjectType.FIXED,
                "deadline": date.today() + timedelta(days=30),
                "status": Project.Status.OPEN,
            },
        )

        # Seed an Active Order with Milestones
        self.stdout.write("\nSeeding active contract with milestones...")
        sample_order, o_created = Order.objects.get_or_create(
            client=client_user,
            freelancer=dev_user,
            total_amount=Decimal("1200.00"),
            defaults={
                "project": p1,
                "platform_fee": Decimal("120.00"),
                "freelancer_payout": Decimal("1080.00"),
                "status": Order.Status.ACTIVE,
                "delivery_notes": "First staging build completed on branch feature/analytics.",
                "delivery_url": "https://github.com/techventures/analytics-dashboard",
            },
        )

        if o_created:
            Payment.objects.create(
                order=sample_order,
                payer=client_user,
                amount=Decimal("1200.00"),
                platform_fee=Decimal("120.00"),
                net_payout=Decimal("1080.00"),
                status=Payment.Status.HELD_IN_ESCROW,
            )

            # Milestones
            Milestone.objects.create(
                order=sample_order,
                order_num=1,
                title="Phase 1: API Architecture & Data Schema",
                description="REST endpoints and model relationships completed.",
                amount=Decimal("600.00"),
                due_date=date.today() + timedelta(days=7),
                status=Milestone.Status.APPROVED,
                approved_at=timezone.now(),
            )
            Milestone.objects.create(
                order=sample_order,
                order_num=2,
                title="Phase 2: Frontend Dashboard & Chart Visualizations",
                description="Interactive metrics charts with responsive Tailwind UI.",
                amount=Decimal("600.00"),
                due_date=date.today() + timedelta(days=14),
                status=Milestone.Status.IN_PROGRESS,
            )

        self.stdout.write(self.style.SUCCESS("\nSkillSphere successfully seeded with comprehensive data!"))
