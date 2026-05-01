def test_skill_parsing():
    skills = "python, ml, ai"
    parsed = [s.strip().lower() for s in skills.split(",") if s.strip()]

    assert parsed == ["python", "ml", "ai"]


def test_empty_skills():
    skills = ""
    parsed = [s.strip() for s in skills.split(",") if s.strip()]

    assert parsed == []