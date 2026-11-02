import importlib

import pytest


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("JOB_AGENT_DB", str(tmp_path / "test.db"))
    import database
    importlib.reload(database)
    database.init_db()
    database.init_settings()
    return database


def test_save_job_ignores_duplicate_urls(db):
    first = db.save_job("Junior Developer", "Acme", "Melbourne", "Seek", "https://example.com/1", "desc")
    second = db.save_job("Junior Developer", "Acme", "Melbourne", "Seek", "https://example.com/1", "desc")
    assert first
    assert not second
    assert len(db.get_jobs()) == 1


def test_min_score_filter(db):
    db.save_job("Role A", "A", "Melbourne", "Seek", "https://example.com/a", "d")
    db.save_job("Role B", "B", "Melbourne", "Seek", "https://example.com/b", "d")
    jobs = {j["title"]: j["id"] for j in db.get_jobs()}
    db.update_analysis(jobs["Role A"], 80, "good", "", "", "", "apply")
    db.update_analysis(jobs["Role B"], 30, "weak", "", "", "", "skip")
    titles = [j["title"] for j in db.get_jobs(min_score=50)]
    assert titles == ["Role A"]


def test_status_update_and_hide(db):
    db.save_job("Role C", "C", "Melbourne", "Seek", "https://example.com/c", "d")
    job_id = db.get_jobs()[0]["id"]
    db.update_status(job_id, "applied", "sent via site")
    assert db.get_job(job_id)["status"] == "applied"
    db.hide_job(job_id)
    assert db.get_jobs() == []


def test_settings_round_trip(db):
    db.set_setting("min_score", "60")
    assert db.get_setting("min_score") == "60"
    assert db.get_setting("does_not_exist", "fallback") == "fallback"
