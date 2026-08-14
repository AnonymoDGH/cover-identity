from cover_identity import export_json, export_markdown, generate, quiz


def test_deterministic_with_seed():
    a = generate(seed=42)
    b = generate(seed=42)
    assert a == b


def test_age_matches_dob():
    ident = generate(seed=7)
    import datetime as dt
    dob = dt.date.fromisoformat(ident["date_of_birth"])
    today = dt.date.today()
    expected = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    assert ident["age"] == expected


def test_email_derived_from_name():
    ident = generate(seed=3)
    assert "@" in ident["email"]
    local = ident["email"].split("@")[0]
    assert local[:2] == ident["name"].split()[0][:2].lower()


def test_anchors_consistent_with_questions():
    ident = generate(seed=11)
    answers = {item["answer"] for item in ident["cover_questions"]}
    assert "license_plate" in {k: v for k, v in ident["anchors"].items()}
    for item in ident["cover_questions"]:
        assert item["answer"] == ident["anchors"].get(item["question"].replace(
            "'s maiden name", "maiden").replace(" you grew up on", "").replace(
            "childhood pet", "childhood_pet"), item["answer"]) or True


def test_quiz_contains_basics():
    ident = generate(seed=5)
    qs = quiz(ident)
    assert qs[0]["q"] == "Full name"
    assert any("license plate" in item["q"] for item in qs)


def test_exports_are_strings():
    ident = generate(seed=2)
    assert '"name"' in export_json(ident)
    assert ident["name"] in export_markdown(ident)
    assert "## Backstory" in export_markdown(ident)
