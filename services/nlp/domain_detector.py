import json
import os
import re
from services.nlp import embedding_service

DOMAINS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "occupations", "domains.json")


def load_domain_taxonomy() -> list[dict]:
    """
    Loads domain taxonomy definitions from data/occupations/domains.json.
    """
    if os.path.exists(DOMAINS_FILE_PATH):
        try:
            with open(DOMAINS_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def detect_domains_and_roles(resume_text: str, sections: dict = None) -> tuple[list[dict], list[dict]]:
    """
    Infers candidate professional domains and probable roles with confidence scores.
    
    Returns:
        tuple: (domains: list[dict], probable_roles: list[dict])
    """
    if not resume_text or not resume_text.strip():
        return [], []

    domains_data = load_domain_taxonomy()
    if not domains_data:
        return [], []

    text_lower = resume_text.lower()
    summary_text = (sections or {}).get("summary", "") or resume_text[:500]

    domain_scores = []
    role_scores = []

    for domain_item in domains_data:
        domain_name = domain_item.get("domain", "")
        keywords = domain_item.get("keywords", [])
        anchor_phrases = domain_item.get("anchor_phrases", [])
        typical_roles = domain_item.get("typical_roles", [])

        # 1. Keyword density match score
        kw_matches = 0
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower):
                kw_matches += 1

        kw_score = min(1.0, kw_matches / max(1, len(keywords) * 0.4))

        # 2. Semantic anchor similarity score
        semantic_scores = []
        for anchor in anchor_phrases:
            sim = embedding_service.similarity(summary_text, anchor)
            semantic_scores.append(sim)
        
        sem_score = max(semantic_scores) if semantic_scores else 0.0

        # Hybrid Domain Score: 60% keyword match + 40% semantic similarity
        composite_score = round(0.6 * kw_score + 0.4 * sem_score, 2)

        if composite_score > 0.15:
            domain_scores.append({
                "domain": domain_name,
                "confidence": composite_score
            })

            # Check for specific role title mentions
            for role in typical_roles:
                role_lower = role.lower()
                if role_lower in text_lower or re.search(r'\b' + re.escape(role_lower) + r'\b', text_lower):
                    role_scores.append({
                        "role": role,
                        "confidence": round(min(1.0, composite_score + 0.15), 2)
                    })
                elif composite_score >= 0.4:
                    role_scores.append({
                        "role": role,
                        "confidence": round(composite_score * 0.8, 2)
                    })

    # Sort by confidence descending
    domain_scores.sort(key=lambda x: x["confidence"], reverse=True)

    # Deduplicate and sort roles by confidence
    seen_roles = set()
    unique_roles = []
    role_scores.sort(key=lambda x: x["confidence"], reverse=True)
    for r in role_scores:
        if r["role"] not in seen_roles:
            seen_roles.add(r["role"])
            unique_roles.append(r)

    # Top domains and roles
    return domain_scores[:3], unique_roles[:4]
