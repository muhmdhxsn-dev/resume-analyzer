from typing import Dict, List, Optional

# Priority weights for sorting
PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

# Secondary category tie-breaker order
CATEGORY_ORDER = {
    "contact_information": 0,
    "job_match_required": 1,
    "experience": 2,
    "summary": 3,
    "projects": 4,
    "skills": 5,
    "job_match_preferred": 6,
    "education": 7,
    "certifications": 8,
    "length": 9,
    "job_match": 10
}


def create_recommendation(
    rec_id: str,
    category: str,
    priority: str,
    title: str,
    problem: str,
    why_it_matters: str,
    action: str,
    source: str = "resume_quality"
) -> Dict[str, str]:
    """Helper to construct a structured recommendation dictionary."""
    return {
        "id": rec_id,
        "category": category,
        "priority": priority,
        "title": title,
        "problem": problem,
        "why_it_matters": why_it_matters,
        "action": action,
        "source": source
    }


def generate_general_recommendations(analysis: dict) -> List[Dict[str, str]]:
    """
    Generates structured, evidence-based recommendations based on Phase 5 features & analysis.
    """
    features = analysis.get("features", {})
    recs = []

    # 1. Contact Information
    if not features.get("has_email"):
        recs.append(create_recommendation(
            rec_id="rec_contact_email",
            category="contact_information",
            priority="HIGH",
            title="Add Professional Email Address",
            problem="No professional email address was detected in your resume header.",
            why_it_matters="Recruiters and hiring managers rely on your email address as the primary point of contact for interview invitations.",
            action="Add a professional email address (e.g., firstname.lastname@email.com) prominently in your resume header section.",
            source="resume_quality"
        ))

    if not features.get("has_phone"):
        recs.append(create_recommendation(
            rec_id="rec_contact_phone",
            category="contact_information",
            priority="HIGH",
            title="Add Phone Number",
            problem="No phone number was detected in your contact details.",
            why_it_matters="Recruiters frequently schedule initial phone screenings or send SMS notifications regarding application updates.",
            action="Include a valid, active phone number with your country code in your resume header.",
            source="resume_quality"
        ))

    if not features.get("has_linkedin"):
        recs.append(create_recommendation(
            rec_id="rec_contact_linkedin",
            category="contact_information",
            priority="LOW",
            title="Add LinkedIn Profile Link",
            problem="No LinkedIn profile link was detected.",
            why_it_matters="Recruiters often verify candidate profiles on LinkedIn to evaluate professional recommendations and endorsement networks.",
            action="Add a customized LinkedIn profile URL (e.g., linkedin.com/in/yourname) to your contact section.",
            source="resume_quality"
        ))

    if not features.get("has_github") and (features.get("skill_count", 0) > 0 or features.get("has_projects")):
        recs.append(create_recommendation(
            rec_id="rec_contact_github",
            category="contact_information",
            priority="LOW",
            title="Add GitHub Profile Link",
            problem="No GitHub profile link was detected.",
            why_it_matters="For technical roles, code repositories provide tangible proof of your programming ability and software contributions.",
            action="If you have technical projects or code samples, include your GitHub profile URL (e.g., github.com/yourusername) in your header.",
            source="resume_quality"
        ))

    # 2. Summary
    if not features.get("has_summary"):
        recs.append(create_recommendation(
            rec_id="rec_summary_missing",
            category="summary",
            priority="HIGH",
            title="Add a Professional Summary",
            problem="Your resume does not contain a professional summary section.",
            why_it_matters="A concise summary immediately frames your professional identity, core expertise, and value proposition for busy recruiters.",
            action="Add a 2–4 sentence professional summary at the top of your resume describing your background, top technical skills, experience level, and target role.",
            source="resume_quality"
        ))
    elif features.get("summary_word_count", 0) < 20:
        recs.append(create_recommendation(
            rec_id="rec_summary_short",
            category="summary",
            priority="MEDIUM",
            title="Expand Professional Summary",
            problem="Your summary section is very brief (under 20 words).",
            why_it_matters="A brief summary may fail to adequately communicate your core competencies, key domain focus, and career direction.",
            action="Expand your summary to 2–4 sentences detailing your primary technical stack, years of experience, and key professional strengths.",
            source="resume_quality"
        ))

    # 3. Skills
    sc = features.get("skill_count", 0)
    if sc < 3 and features.get("has_text"):
        recs.append(create_recommendation(
            rec_id="rec_skills_low",
            category="skills",
            priority="MEDIUM",
            title="Expand Skills Section",
            problem=f"Fewer than 3 recognized skills were detected ({sc} detected).",
            why_it_matters="Recruiters and automated screening systems filter candidates based on key technical competencies and tools.",
            action="If you possess additional technical or professional skills that are not currently listed, expand your Skills section with relevant tools, libraries, and frameworks.",
            source="resume_quality"
        ))

    # 4. Experience
    if not features.get("has_experience") and features.get("has_text"):
        recs.append(create_recommendation(
            rec_id="rec_experience_missing",
            category="experience",
            priority="HIGH",
            title="Strengthen Work Experience Section",
            problem="Your experience section is missing or provides very limited details.",
            why_it_matters="Work experience is the most critical evaluation factor for recruiters assessing your practical capability.",
            action="Add relevant professional roles, internships, or employment history detailing your responsibilities, technologies used, and key accomplishments.",
            source="resume_quality"
        ))
    else:
        if not features.get("experience_has_action_verb") and features.get("has_experience"):
            recs.append(create_recommendation(
                rec_id="rec_experience_verbs",
                category="experience",
                priority="MEDIUM",
                title="Use Strong Action Verbs in Bullet Points",
                problem="Few strong action verbs were detected in your experience bullet points.",
                why_it_matters="Action verbs create an impactful, active narrative that clearly communicates your direct contributions.",
                action="Begin your experience bullet points with strong action verbs such as developed, implemented, designed, optimized, automated, or led.",
                source="resume_quality"
            ))

        if not features.get("experience_has_metric") and features.get("has_experience"):
            recs.append(create_recommendation(
                rec_id="rec_experience_metrics",
                category="experience",
                priority="HIGH",
                title="Add Quantified Accomplishments to Experience",
                problem="Your experience section contains few measurable results or metrics.",
                why_it_matters="Quantified accomplishments provide concrete proof of your impact and make achievements memorable for hiring managers.",
                action="Where truthful and available, rewrite 2–3 experience bullet points to include measurable outcomes (e.g., percentages improved, users served, time saved, or performance gains).",
                source="resume_quality"
            ))

    # 5. Projects
    if not features.get("has_projects") and features.get("has_text"):
        recs.append(create_recommendation(
            rec_id="rec_projects_missing",
            category="projects",
            priority="MEDIUM",
            title="Add Dedicated Projects Section",
            problem="No projects section was detected.",
            why_it_matters="Documented projects demonstrate practical hands-on application of your technical skills.",
            action="Add 1–3 relevant personal, academic, or open-source projects describing the problem solved, stack used, and your contribution.",
            source="resume_quality"
        ))

    # 6. Education
    if not features.get("has_education") and features.get("has_text"):
        recs.append(create_recommendation(
            rec_id="rec_education_missing",
            category="education",
            priority="HIGH",
            title="Add Education Section",
            problem="No education section was detected.",
            why_it_matters="Academic qualifications verify foundational training and degree eligibility.",
            action="Include an Education section listing your degree(s), major, institution name, and graduation year.",
            source="resume_quality"
        ))

    # 7. Certifications
    if not features.get("has_certifications") and features.get("has_text"):
        recs.append(create_recommendation(
            rec_id="rec_certifications_missing",
            category="certifications",
            priority="LOW",
            title="Consider Adding Relevant Certifications",
            problem="No certifications section was detected.",
            why_it_matters="Industry certifications offer validated proof of specialized knowledge.",
            action="If you hold relevant professional certifications or licenses, add a Certifications section to highlight your credentials.",
            source="resume_quality"
        ))

    # 8. Length
    pc = features.get("page_count")
    words = features.get("total_word_count", 0)
    if pc and pc > 3:
        recs.append(create_recommendation(
            rec_id="rec_length_long",
            category="length",
            priority="LOW",
            title="Condense Resume Length",
            problem=f"Your resume spans {pc} pages.",
            why_it_matters="Recruiters spend an average of 6–10 seconds on an initial scan; lengthy resumes dilute key accomplishments.",
            action="Trim older or less relevant positions and condense your resume to 1–2 pages for maximum readability.",
            source="resume_quality"
        ))
    elif features.get("has_text") and words < 100:
        recs.append(create_recommendation(
            rec_id="rec_length_short",
            category="length",
            priority="LOW",
            title="Expand Resume Depth",
            problem="Your resume is extremely concise (under 100 words).",
            why_it_matters="An overly brief resume may miss critical accomplishments and technical evidence.",
            action="Consider expanding relevant accomplishments, projects, skills, or professional context rather than adding filler.",
            source="resume_quality"
        ))

    return recs


def generate_job_recommendations(job_match: dict, evidence_analysis: Optional[dict] = None) -> List[Dict[str, str]]:
    """
    Generates structured, job-specific recommendations based on Phase 6 Job Match data
    and Phase 8 Evidence Gaps.
    """
    if not job_match or not job_match.get("has_job_description"):
        return []

    recs = []
    missing_req = job_match.get("missing_required_skills", [])
    missing_pref = job_match.get("missing_preferred_skills", [])
    matched = job_match.get("matched_skills", [])

    # 1. Missing Required Skills (HIGH Priority)
    if missing_req:
        skills_str = ", ".join(missing_req)
        recs.append(create_recommendation(
            rec_id="rec_job_missing_required",
            category="job_match_required",
            priority="HIGH",
            title="Address Missing Required Job Skills",
            problem=f"The following required skills were not detected in your resume: {skills_str}.",
            why_it_matters="Required skills are mandatory qualification criteria for this position. Missing them significantly lowers your job match score.",
            action=f"{skills_str} are listed as required for this role but were not detected. If you have genuine experience with these technologies that is not currently represented, make that experience more visible in your Skills, Experience, or Projects sections. If you do not have experience with these skills, consider gaining practical experience before claiming them.",
            source="job_match"
        ))

    # 2. Phase 8 Evidence Gaps: Weak evidence for job skills (HIGH / MEDIUM Priority)
    if evidence_analysis and evidence_analysis.get("evidence_gaps"):
        for gap in evidence_analysis["evidence_gaps"]:
            skill = gap["skill"]
            req_type = str(gap.get("requirement_type", gap.get("type", "required"))).lower()
            prio = "HIGH" if req_type == "required" else "MEDIUM"
            recs.append(create_recommendation(
                rec_id=f"rec_evidence_gap_{skill.lower().replace(' ', '_')}",
                category=f"job_match_{req_type}",
                priority=prio,
                title=f"Strengthen {skill} Resume Evidence",
                problem=f"{skill} is listed in your Skills section but is not supported by Experience or Project bullet points.",
                why_it_matters="Recruiters value practical proof of skill application over standalone keyword lists.",
                action=f"If you have genuine {skill} experience, add a bullet point in your Experience or Projects section demonstrating how you applied {skill}. If you do not have practical experience, consider gaining hands-on experience before claiming it.",
                source="job_match"
            ))

    # 3. Missing Preferred Skills (MEDIUM Priority)
    if missing_pref:
        skills_str = ", ".join(missing_pref)
        recs.append(create_recommendation(
            rec_id="rec_job_missing_preferred",
            category="job_match_preferred",
            priority="MEDIUM",
            title="Highlight Preferred Job Skills",
            problem=f"The following preferred skills were not detected in your resume: {skills_str}.",
            why_it_matters="Preferred skills set top candidates apart from the general applicant pool.",
            action=f"{skills_str} are listed as preferred skills for this position. If you possess genuine experience with these tools, consider highlighting them in your relevant experience or project entries. Otherwise, this is a lower-priority gap than required skills.",
            source="job_match"
        ))

    # 4. Matched Skills Optimization (LOW Priority)
    if matched and len(matched) >= 2:
        matched_sample = ", ".join(matched[:3])
        recs.append(create_recommendation(
            rec_id="rec_job_matched_skills",
            category="job_match",
            priority="LOW",
            title="Strengthen Evidence for Matched Job Skills",
            problem=f"Skills like {matched_sample} match the job description, but ensure they are backed by concrete evidence.",
            why_it_matters="Listing skills in a standalone list is helpful, but demonstrating how you applied them in real projects creates far stronger credibility.",
            action=f"Ensure your matched skills ({matched_sample}) are supported by concrete accomplishment bullet points in your Experience or Projects sections rather than appearing only in your Skills list.",
            source="job_match"
        ))

    return recs


def sort_recommendations(recommendations: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Sorts recommendations deterministically:
    1. Priority: HIGH -> MEDIUM -> LOW
    2. Category tie-breaker: Contact -> Job Required -> Experience -> Summary -> Projects -> Skills -> Job Preferred -> Education -> Certifications -> Length
    """
    def sort_key(rec: dict):
        p_val = PRIORITY_ORDER.get(rec.get("priority", "LOW"), 99)
        c_val = CATEGORY_ORDER.get(rec.get("category", ""), 99)
        return (p_val, c_val, rec.get("id", ""))

    return sorted(recommendations, key=sort_key)


def generate_recommendations(
    analysis: dict,
    job_match: Optional[dict] = None,
    evidence_analysis: Optional[dict] = None
) -> dict:
    """
    Main entrypoint for Phase 7 & 8 Recommendation Generation.
    Combines general resume improvement recommendations, job-specific recommendations, and evidence gaps.
    """
    general_recs = generate_general_recommendations(analysis)
    job_recs = generate_job_recommendations(job_match, evidence_analysis) if job_match else []

    all_recs = sort_recommendations(general_recs + job_recs)
    resume_improvements = sort_recommendations(general_recs)
    job_improvements = sort_recommendations(job_recs)

    high_count = sum(1 for r in all_recs if r["priority"] == "HIGH")
    med_count = sum(1 for r in all_recs if r["priority"] == "MEDIUM")
    low_count = sum(1 for r in all_recs if r["priority"] == "LOW")

    return {
        "all_recommendations": all_recs,
        "resume_improvements": resume_improvements,
        "job_improvements": job_improvements,
        "has_job_recommendations": bool(job_recs),
        "counts": {
            "high": high_count,
            "medium": med_count,
            "low": low_count,
            "total": len(all_recs)
        }
    }
