def test_supervisor_normalization():
    supervisor_id = ""
    normalized = supervisor_id if supervisor_id else None

    assert normalized is None


def test_salary_conversion():
    salary = "70000"
    assert float(salary) == 70000.0

def test_skill_parsing_edge_cases():
    skills = " python , , ML ,AI  ,"
    parsed = [s.strip().lower() for s in skills.split(",") if s.strip()]

    assert parsed == ["python", "ml", "ai"]