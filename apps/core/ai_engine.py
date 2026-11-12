"""
SkillSphere AI Intelligence Engine
Provides real, testable algorithmic and natural-language matching,
resume skill extraction, profile analyzer, and smart project budget estimator.
"""

import re
import os
from decimal import Decimal
from typing import Dict, List, Any, Optional

# Comprehensive tech taxonomy for AI extraction and matching
TECH_TAXONOMY = {
    "Python": ["python", "django", "fastapi", "flask", "pandas", "numpy", "pytorch", "tensorflow"],
    "JavaScript/TypeScript": ["javascript", "typescript", "js", "ts", "node", "nodejs", "react", "next.js", "nextjs", "vue", "angular", "express"],
    "Frontend": ["html", "css", "tailwind", "tailwind css", "bootstrap", "sass", "ui/ux", "figma", "responsive"],
    "Backend & APIs": ["rest", "rest api", "graphql", "grpc", "microservices", "celery", "redis"],
    "Databases": ["mongodb", "postgresql", "postgres", "mysql", "sqlite", "redis", "elasticsearch", "sql"],
    "Cloud & DevOps": ["aws", "gcp", "azure", "docker", "kubernetes", "k8s", "ci/cd", "github actions", "terraform", "linux", "nginx"],
    "AI & Data": ["machine learning", "deep learning", "nlp", "llm", "langchain", "rag", "computer vision", "scikit-learn"],
    "Mobile": ["react native", "flutter", "ios", "android", "swift", "kotlin"],
    "Security": ["cybersecurity", "penetration testing", "owasp", "oauth", "jwt", "cryptography"],
}

ALL_KNOWN_SKILLS = set()
for category, skills in TECH_TAXONOMY.items():
    for s in skills:
        ALL_KNOWN_SKILLS.add(s.lower())


def extract_text_from_file(file_path: str) -> str:
    """Extract readable text from PDF, DOCX, or TXT file."""
    if not os.path.exists(file_path):
        return ""

    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            pass

    elif ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception:
            pass

    elif ext == ".docx":
        try:
            import docx
            doc = docx.Document(file_path)
            for p in doc.paragraphs:
                if p.text:
                    text += p.text + "\n"
        except Exception:
            pass

    return text.strip()


def extract_skills_from_text(raw_text: str) -> List[str]:
    """Identify standardized technical skills found in text."""
    found_skills = set()
    cleaned = re.sub(r"[^\w\s\.\+\#-]", " ", raw_text.lower())
    words = set(cleaned.split())

    # Check unigrams and known multi-word phrases
    for standard_skill in ALL_KNOWN_SKILLS:
        if " " in standard_skill or "." in standard_skill:
            if standard_skill in cleaned:
                found_skills.add(standard_skill.title())
        elif standard_skill in words:
            found_skills.add(standard_skill.title())

    return sorted(list(found_skills))


def match_freelancers_for_project(project, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    AI Talent Matching Algorithm:
    Ranks active freelancers for a project based on skills, budget fit,
    experience level, ratings, and availability.
    """
    from accounts.models import User, Profile

    required_skills = [s.strip().lower() for s in project.get_skills_list()]
    req_set = set(required_skills)

    freelancers = User.objects.filter(
        role=User.Role.FREELANCER, is_active=True
    ).select_related("profile")

    candidates = []

    for dev in freelancers:
        profile = getattr(dev, "profile", None)
        if not profile:
            continue

        dev_skills = [s.strip().lower() for s in profile.get_skills_list()]
        dev_set = set(dev_skills)

        # 1. Skill Match Score (up to 45 points)
        matched_skills = req_set.intersection(dev_set)
        partial_matches = set()
        for r in req_set:
            if r not in matched_skills:
                for d in dev_set:
                    if r in d or d in r:
                        partial_matches.add(r)
                        break

        total_req = len(req_set) if req_set else 1
        skill_score = (len(matched_skills) * 1.0 + len(partial_matches) * 0.5) / total_req
        skill_points = min(45.0, skill_score * 45.0)

        # 2. Experience Level Compatibility (up to 20 points)
        # Entry=1, Intermediate=2, Expert=3
        exp_weight = {"entry": 1, "intermediate": 2, "expert": 3}
        proj_exp = exp_weight.get(getattr(project, "complexity", "intermediate"), 2)
        dev_exp = exp_weight.get(profile.experience_level, 2)

        if dev_exp >= proj_exp:
            exp_points = 20.0
        elif dev_exp == proj_exp - 1:
            exp_points = 14.0
        else:
            exp_points = 8.0

        # 3. Budget Fit (up to 15 points)
        hourly = float(profile.hourly_rate or 0)
        proj_budget = float(project.budget or 100)
        # Assuming ~10-40 hours project, check if rate is reasonable
        if hourly <= 0:
            budget_points = 10.0
            budget_fit = "Flexible"
        else:
            estimated_cost = hourly * 15.0
            ratio = estimated_cost / max(proj_budget, 1.0)
            if 0.5 <= ratio <= 1.3:
                budget_points = 15.0
                budget_fit = "Strong Match"
            elif ratio < 0.5:
                budget_points = 12.0
                budget_fit = "Economical"
            elif ratio <= 1.8:
                budget_points = 10.0
                budget_fit = "Moderate Stretch"
            else:
                budget_points = 6.0
                budget_fit = "Higher Premium"

        # 4. Rating & Reputation (up to 12 points)
        rating = profile.rating or 5.0
        reviews = profile.reviews_count or 0
        rating_points = (rating / 5.0) * 10.0
        if reviews >= 5:
            rating_points += 2.0
        elif reviews >= 1:
            rating_points += 1.0
        else:
            # Fair baseline for newly registered developers
            rating_points += 1.0
        rating_points = min(12.0, rating_points)

        # 5. Availability (up to 8 points)
        if profile.availability == Profile.Availability.FULL_TIME:
            avail_points = 8.0
        elif profile.availability == Profile.Availability.PART_TIME:
            avail_points = 6.0
        else:
            avail_points = 2.0

        total_score = int(round(skill_points + exp_points + budget_points + rating_points + avail_points))
        total_score = max(25, min(99, total_score))

        # Generate explanatory recommendation text
        matched_display = [s.title() for s in matched_skills]
        if matched_display:
            skills_str = ", ".join(matched_display[:3])
            expl = f"{dev.get_display_name()} demonstrates direct expertise in {skills_str} with {profile.get_experience_level_display().lower()} proficiency. Budget profile indicates a {budget_fit.lower()} with current {profile.get_availability_display().lower()}."
        else:
            expl = f"{dev.get_display_name()} brings {profile.get_experience_level_display()} engineering background with a {budget_fit.lower()} for this {project.category.name if project.category else 'software'} scope."

        candidates.append({
            "freelancer": dev,
            "profile": profile,
            "match_score": total_score,
            "matching_skills": [s.title() for s in matched_skills],
            "missing_skills": [s.title() for s in req_set - matched_skills],
            "budget_fit": budget_fit,
            "explanation": expl,
        })

    candidates.sort(key=lambda x: x["match_score"], reverse=True)
    return candidates[:top_k]


def analyze_freelancer_profile(profile, resume_file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    AI Profile & Skill Analyzer:
    Evaluates profile completeness, extracts skills from resume,
    identifies missing complementary skills, and returns improvement suggestions.
    """
    score = 0
    feedback = []
    extracted_resume_skills = []

    # 1. Profile Core Fields Assessment
    if profile.headline and len(profile.headline) >= 15:
        score += 15
    else:
        feedback.append("Add a detailed professional headline (e.g. 'Senior Full-Stack Django & React Engineer').")

    if profile.bio and len(profile.bio) >= 100:
        score += 20
    elif profile.bio:
        score += 10
        feedback.append("Expand your bio with background context, projects built, and problem-solving focus.")
    else:
        feedback.append("Write a comprehensive professional overview to build client confidence.")

    current_skills = profile.get_skills_list()
    if len(current_skills) >= 5:
        score += 20
    elif len(current_skills) >= 2:
        score += 10
        feedback.append("List at least 5 core technical competencies.")
    else:
        feedback.append("Add your key programming languages, frameworks, and databases.")

    if profile.hourly_rate and profile.hourly_rate > 0:
        score += 10
    else:
        feedback.append("Set a transparent hourly rate to help clients match budgets.")

    if profile.portfolio_website or profile.github_url or profile.linkedin_url:
        score += 15
    else:
        feedback.append("Include external GitHub repository or live portfolio links.")

    if profile.user.avatar:
        score += 10
    else:
        feedback.append("Upload a professional profile photo.")

    # 2. Resume Text Extraction & Skill Identification
    if resume_file_path and os.path.exists(resume_file_path):
        extracted_text = extract_text_from_file(resume_file_path)
        if extracted_text:
            profile.resume_text = extracted_text[:8000]
            extracted_resume_skills = extract_skills_from_text(extracted_text)
            score += 10

    # 3. Missing In-Demand Skill Recommendations
    existing_lower = {s.lower() for s in current_skills}
    suggested_skills = []

    # Check adjacent complementary skills
    if any(k in existing_lower for k in ["python", "django", "fastapi"]):
        for rec in ["Docker", "PostgreSQL", "Redis", "Tailwind CSS", "Celery"]:
            if rec.lower() not in existing_lower:
                suggested_skills.append(rec)
    if any(k in existing_lower for k in ["react", "next.js", "javascript", "typescript"]):
        for rec in ["Tailwind CSS", "TypeScript", "Next.js", "GraphQL", "REST API"]:
            if rec.lower() not in existing_lower:
                suggested_skills.append(rec)
    if any(k in existing_lower for k in ["ai", "machine learning", "pytorch"]):
        for rec in ["LangChain", "Vector DB", "FastAPI", "Docker", "PyTorch"]:
            if rec.lower() not in existing_lower:
                suggested_skills.append(rec)

    # De-duplicate suggestions
    suggested_skills = list(dict.fromkeys(suggested_skills))[:5]

    score = min(100, max(20, score))
    profile.ai_profile_score = score
    profile.ai_suggestions = "\n".join(feedback)
    profile.save(update_fields=["ai_profile_score", "ai_suggestions", "resume_text"])

    return {
        "score": score,
        "feedback": feedback,
        "extracted_resume_skills": extracted_resume_skills,
        "suggested_skills": suggested_skills,
    }


def estimate_project_budget_and_timeline(
    description: str,
    category_name: str,
    skills_list: List[str],
    complexity: str = "intermediate"
) -> Dict[str, Any]:
    """
    Smart Project Budget & Timeline Estimator:
    Calculates estimated budget range and timeline based on project requirements.
    """
    word_count = len(description.split()) if description else 20
    skills_count = len(skills_list) if skills_list else 3

    # Base base rates by category
    base_budget_map = {
        "web-development": 350.0,
        "ai-machine-learning": 500.0,
        "cloud-devops": 450.0,
        "mobile-development": 400.0,
        "cybersecurity": 500.0,
        "ui-ux-design": 300.0,
    }
    cat_key = category_name.lower().replace(" ", "-") if category_name else "web-development"
    base_cost = base_budget_map.get(cat_key, 350.0)

    # Complexity multipliers
    comp_multiplier = {
        "entry": 0.8,
        "intermediate": 1.25,
        "expert": 2.1,
    }.get(complexity, 1.2)

    # Scope factor based on description depth and skills count
    scope_multiplier = 1.0 + (min(word_count, 300) / 300.0) * 0.4 + (min(skills_count, 8) / 8.0) * 0.3

    estimated_median = round(base_cost * comp_multiplier * scope_multiplier, -1)
    min_budget = round(estimated_median * 0.8, -1)
    max_budget = round(estimated_median * 1.35, -1)

    # Timeline estimation in days
    base_days = 7
    if complexity == "entry":
        base_days = 5
    elif complexity == "expert":
        base_days = 18
    else:
        base_days = 10

    scope_days = int(round(base_days * (scope_multiplier ** 0.8)))
    min_days = max(3, int(scope_days * 0.8))
    max_days = int(scope_days * 1.4)

    factors = [
        f"Category baseline derived from {category_name or 'Software'} market rates.",
        f"Complexity weighted as '{complexity.title()}' requiring corresponding architecture.",
        f"Scope factored for {skills_count} specialized technical competencies and {word_count} words of specification.",
    ]

    return {
        "min_budget": Decimal(str(min_budget)),
        "max_budget": Decimal(str(max_budget)),
        "recommended_budget": Decimal(str(estimated_median)),
        "min_days": min_days,
        "max_days": max_days,
        "recommended_days": scope_days,
        "factors": factors,
    }
