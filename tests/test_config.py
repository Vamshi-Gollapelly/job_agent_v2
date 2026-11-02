import config


def test_load_resume_prefers_explicit_path(tmp_path):
    custom = tmp_path / "my_resume.txt"
    custom.write_text("CUSTOM RESUME", encoding="utf-8")
    assert config.load_resume(custom) == "CUSTOM RESUME"


def test_load_resume_falls_back_to_example(tmp_path, monkeypatch):
    monkeypatch.delenv("RESUME_PATH", raising=False)
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    (tmp_path / "resume.example.txt").write_text("EXAMPLE", encoding="utf-8")
    assert config.load_resume() == "EXAMPLE"


def test_secret_key_is_never_empty():
    assert config.FLASK_SECRET_KEY
    assert config.FLASK_SECRET_KEY != "job-agent-v2-secret"
