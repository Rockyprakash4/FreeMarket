from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from accounts.models import User, Profile
from marketplace.models import Category, Project, Service
from proposals.models import Proposal
from orders.models import Order, Milestone
from payments.models import Payment
from disputes.models import Dispute
from reviews.models import Review
from apps.core.ai_engine import (
    extract_skills_from_text,
    match_freelancers_for_project,
    analyze_freelancer_profile,
    estimate_project_budget_and_timeline,
)


class AIEngineTestCase(TestCase):
    """Verifies all AI algorithms: Matching, Budget Estimator, Profile Analyzer."""

    def test_extract_skills_from_text(self):
        text = "Looking for a seasoned developer skilled in Python, Django, Docker, and PostgreSQL with React frontends."
        skills = extract_skills_from_text(text)
        self.assertIn("Python", skills)
        self.assertIn("Django", skills)
        self.assertIn("Docker", skills)
        self.assertIn("Postgresql", skills)
        self.assertIn("React", skills)

    def test_ai_budget_and_timeline_estimator(self):
        result = estimate_project_budget_and_timeline(
            description="Build a high performance e-commerce platform with stripe integration and inventory tracking",
            category_name="web-development",
            skills_list=["Python", "Django", "PostgreSQL", "Docker", "Stripe"],
            complexity="expert",
        )
        self.assertGreater(result["min_budget"], 0)
        self.assertGreaterEqual(result["max_budget"], result["min_budget"])
        self.assertGreater(result["recommended_budget"], 0)
        self.assertGreater(result["min_days"], 0)
        self.assertGreaterEqual(result["max_days"], result["min_days"])
        self.assertGreater(len(result["factors"]), 0)

    def test_talent_matching_algorithm(self):
        cat = Category.objects.create(name="Web Dev", slug="web-dev")

        client_user = User.objects.create_user(
            username="test_client", email="client@test.com", password="password123", role=User.Role.CLIENT
        )
        project = Project.objects.create(
            client=client_user,
            title="Django React Platform",
            description="Need full stack expert in Python Django and React",
            category=cat,
            required_skills="Python, Django, React, Docker",
            budget=Decimal("1500.00"),
            deadline=timezone.now().date(),
            complexity="intermediate",
        )

        f1 = User.objects.create_user(
            username="best_dev", email="best@test.com", password="password123", role=User.Role.FREELANCER
        )
        p1 = f1.profile
        p1.skills = "Python, Django, React, Docker, PostgreSQL"
        p1.experience_level = "senior"
        p1.hourly_rate = Decimal("60.00")
        p1.rating = Decimal("4.9")
        p1.verification_status = Profile.VerificationStatus.VERIFIED
        p1.save()

        f2 = User.objects.create_user(
            username="junior_dev", email="junior@test.com", password="password123", role=User.Role.FREELANCER
        )
        p2 = f2.profile
        p2.skills = "HTML, CSS"
        p2.experience_level = "entry"
        p2.hourly_rate = Decimal("20.00")
        p2.rating = Decimal("3.0")
        p2.save()

        matches = match_freelancers_for_project(project)
        self.assertGreaterEqual(len(matches), 1)

        top_match = matches[0]
        self.assertEqual(top_match["freelancer"].username, "best_dev")
        self.assertGreater(top_match["match_score"], 60)
        self.assertIn("explanation", top_match)
        self.assertIn("Python", top_match["matching_skills"])

    def test_freelancer_profile_analyzer(self):
        user = User.objects.create_user(
            username="analyzer_dev", email="dev@test.com", password="password123", role=User.Role.FREELANCER
        )
        profile = user.profile
        profile.headline = "Senior Full Stack Django & React Engineer"
        profile.bio = "Experienced developer building robust scalable backends with 8+ years architecting microservices and cloud deployments."
        profile.skills = "Python, Django, PostgreSQL, Docker, React"
        profile.hourly_rate = Decimal("75.00")
        profile.experience_level = "senior"
        profile.save()

        analysis = analyze_freelancer_profile(profile)
        self.assertGreaterEqual(analysis["score"], 50)
        self.assertIsInstance(analysis["feedback"], list)


class SkillSphereMarketplaceLifecycleTestCase(TestCase):
    """Verifies end-to-end lifecycle: Project posting -> Proposal -> Escrow Order -> Delivery -> Approval & Payout."""

    def setUp(self):
        self.client_user = User.objects.create_user(
            username="alice_client", email="alice@test.com", password="password123", role=User.Role.CLIENT
        )
        self.dev_user = User.objects.create_user(
            username="bob_freelancer", email="bob@test.com", password="password123", role=User.Role.FREELANCER
        )
        self.admin_user = User.objects.create_superuser(
            username="super_admin", email="admin@test.com", password="password123"
        )
        self.category = Category.objects.create(name="Full Stack Web", slug="full-stack-web")

    def test_project_proposal_escrow_workflow(self):
        project = Project.objects.create(
            client=self.client_user,
            title="Custom CRM Dashboard",
            description="Build CRM with client portals",
            category=self.category,
            required_skills="Python, Django, Tailwind",
            budget=Decimal("1000.00"),
            deadline=timezone.now().date(),
        )
        self.assertEqual(project.status, Project.Status.OPEN)

        proposal = Proposal.objects.create(
            project=project,
            freelancer=self.dev_user,
            cover_letter="I can deliver this in 7 days.",
            proposed_price=Decimal("900.00"),
            estimated_delivery_days=7,
        )
        self.assertEqual(proposal.status, Proposal.Status.PENDING)

        proposal.status = Proposal.Status.ACCEPTED
        proposal.save()

        project.status = Project.Status.IN_PROGRESS
        project.save()

        platform_fee = (proposal.proposed_price * Decimal("0.10")).quantize(Decimal("0.01"))
        freelancer_payout = proposal.proposed_price - platform_fee

        order = Order.objects.create(
            project=project,
            proposal=proposal,
            client=self.client_user,
            freelancer=self.dev_user,
            total_amount=proposal.proposed_price,
            platform_fee=platform_fee,
            freelancer_payout=freelancer_payout,
            status=Order.Status.ACTIVE,
        )

        payment = Payment.objects.create(
            order=order,
            payer=self.client_user,
            amount=proposal.proposed_price,
            platform_fee=platform_fee,
            net_payout=freelancer_payout,
            status=Payment.Status.HELD_IN_ESCROW,
        )

        self.assertEqual(order.platform_fee, Decimal("90.00"))
        self.assertEqual(order.freelancer_payout, Decimal("810.00"))
        self.assertEqual(payment.status, Payment.Status.HELD_IN_ESCROW)

        order.status = Order.Status.DELIVERED
        order.delivery_notes = "Here is the GitHub repository and deployed link."
        order.save()

        order.revision_requested = True
        order.revision_notes = "Please add export to CSV button."
        order.revision_count += 1
        order.status = Order.Status.IN_REVISION
        order.save()
        self.assertEqual(order.revision_count, 1)

        order.status = Order.Status.COMPLETED
        order.completed_at = timezone.now()
        order.revision_requested = False
        order.save()

        payment.status = Payment.Status.RELEASED
        payment.save()

        self.dev_user.profile.total_earned = Decimal(str(self.dev_user.profile.total_earned or 0)) + Decimal(str(order.freelancer_payout))
        self.dev_user.profile.save()

        self.client_user.profile.total_spent = Decimal(str(self.client_user.profile.total_spent or 0)) + Decimal(str(order.total_amount))
        self.client_user.profile.save()

        self.assertEqual(order.status, Order.Status.COMPLETED)
        self.assertEqual(payment.status, Payment.Status.RELEASED)
        self.assertEqual(self.dev_user.profile.total_earned, Decimal("810.00"))
        self.assertEqual(self.client_user.profile.total_spent, Decimal("900.00"))

        review = Review.objects.create(
            order=order,
            reviewer=self.client_user,
            reviewee=self.dev_user,
            rating=5,
            comment="Exceptional work delivered promptly!",
        )
        self.assertEqual(review.rating, 5)
        self.assertFalse(review.is_reported)


class ServiceGigsTestCase(TestCase):
    """Verifies pre-packaged Freelance Services (Gigs) direct purchasing and escrow creation."""

    def test_direct_service_order_and_escrow(self):
        seller = User.objects.create_user(
            username="gig_dev", email="gig@test.com", password="password123", role=User.Role.FREELANCER
        )
        buyer = User.objects.create_user(
            username="gig_buyer", email="buyer@test.com", password="password123", role=User.Role.CLIENT
        )
        cat = Category.objects.create(name="DevOps", slug="devops")

        service = Service.objects.create(
            freelancer=seller,
            category=cat,
            title="Kubernetes Cluster Setup on AWS",
            description="Production grade multi-az k8s cluster with ingress.",
            price=Decimal("500.00"),
            delivery_time_days=4,
            technologies="Kubernetes, AWS, Terraform, Docker",
        )

        total = service.price
        fee = (total * Decimal("0.10")).quantize(Decimal("0.01"))
        net = total - fee

        order = Order.objects.create(
            service=service,
            client=buyer,
            freelancer=seller,
            total_amount=total,
            platform_fee=fee,
            freelancer_payout=net,
            status=Order.Status.ACTIVE,
        )

        payment = Payment.objects.create(
            order=order,
            payer=buyer,
            amount=total,
            platform_fee=fee,
            net_payout=net,
            status=Payment.Status.HELD_IN_ESCROW,
        )

        self.assertEqual(order.title, "Kubernetes Cluster Setup on AWS")
        self.assertEqual(order.platform_fee, Decimal("50.00"))
        self.assertEqual(order.freelancer_payout, Decimal("450.00"))
        self.assertEqual(payment.status, Payment.Status.HELD_IN_ESCROW)


class MilestoneTestCase(TestCase):
    """Verifies multi-milestone contract lifecycle and individual approvals."""

    def test_milestone_progression(self):
        client = User.objects.create_user(username="m_client", email="mc@test.com", password="password123", role=User.Role.CLIENT)
        dev = User.objects.create_user(username="m_dev", email="md@test.com", password="password123", role=User.Role.FREELANCER)

        order = Order.objects.create(
            client=client,
            freelancer=dev,
            total_amount=Decimal("1200.00"),
            platform_fee=Decimal("120.00"),
            freelancer_payout=Decimal("1080.00"),
            status=Order.Status.ACTIVE,
        )

        m1 = Milestone.objects.create(
            order=order,
            title="UI/UX Architecture & Prototypes",
            amount=Decimal("400.00"),
            status=Milestone.Status.PENDING,
        )
        self.assertEqual(m1.status, Milestone.Status.PENDING)

        m1.status = Milestone.Status.SUBMITTED
        m1.deliverable_notes = "Figma prototypes ready for inspection."
        m1.submitted_at = timezone.now()
        m1.save()

        m1.status = Milestone.Status.APPROVED
        m1.approved_at = timezone.now()
        m1.save()

        self.assertEqual(m1.status, Milestone.Status.APPROVED)
        self.assertIsNotNone(m1.approved_at)


class DisputeArbitrationTestCase(TestCase):
    """Verifies dispute resolution workflow and admin arbitration refund/payout actions."""

    def test_dispute_and_admin_arbitration(self):
        client = User.objects.create_user(username="d_client", email="dc@test.com", password="password123", role=User.Role.CLIENT)
        dev = User.objects.create_user(username="d_dev", email="dd@test.com", password="password123", role=User.Role.FREELANCER)
        admin = User.objects.create_superuser(username="d_admin", email="da@test.com", password="password123")

        order = Order.objects.create(
            client=client,
            freelancer=dev,
            total_amount=Decimal("800.00"),
            platform_fee=Decimal("80.00"),
            freelancer_payout=Decimal("720.00"),
            status=Order.Status.ACTIVE,
        )
        payment = Payment.objects.create(
            order=order,
            payer=client,
            amount=Decimal("800.00"),
            platform_fee=Decimal("80.00"),
            net_payout=Decimal("720.00"),
            status=Payment.Status.HELD_IN_ESCROW,
        )

        dispute = Dispute.objects.create(
            order=order,
            raised_by=client,
            reason=Dispute.Reason.DEADLINE,
            description="Freelancer missed 3 consecutive milestones without communication.",
            status=Dispute.Status.OPEN,
        )
        order.status = Order.Status.DISPUTED
        order.save()

        self.assertEqual(order.status, Order.Status.DISPUTED)
        self.assertEqual(dispute.status, Dispute.Status.OPEN)

        dispute.status = Dispute.Status.RESOLVED_REFUND
        dispute.resolved_by = admin
        dispute.resolved_at = timezone.now()
        dispute.resolution_notes = "Evidence confirms prolonged abandonment. Full escrow refunded to client."
        dispute.save()

        order.status = Order.Status.CANCELLED
        order.save()

        payment.status = Payment.Status.REFUNDED
        payment.save()

        self.assertEqual(dispute.status, Dispute.Status.RESOLVED_REFUND)
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(payment.status, Payment.Status.REFUNDED)
