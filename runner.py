import json
from database import get_setting, init_settings

def run_all():
    print("\n========== Job Agent v2 Running ==========")

    # Load settings from database
    try:
        init_settings()
        sources = json.loads(get_setting('sources', '{"seek":true,"indeed":true,"gradconnection":true}'))
        keywords = json.loads(get_setting('keywords', '[]'))
        job_type = get_setting('job_type', 'internship')
        min_score = int(get_setting('min_score', '45'))
        min_doc_score = int(get_setting('min_doc_score', '55'))
        location = get_setting('primary_location', 'Melbourne VIC')
        print(f"Settings: job_type={job_type}, location={location}, min_score={min_score}")
        print(f"Keywords ({len(keywords)}): {', '.join(keywords[:3])}...")
    except Exception as e:
        print(f"Settings load error: {e}")
        sources = {"seek": True, "indeed": True, "gradconnection": True}
        min_score = 45
        min_doc_score = 55

    all_jobs = []

    if sources.get('seek', True):
        try:
            from scrapers.seek_scraper import scrape_seek
            all_jobs.extend(scrape_seek())
        except Exception as e:
            print(f"Seek error: {e}")

    if sources.get('indeed', True):
        try:
            from scrapers.indeed_scraper import scrape_indeed
            all_jobs.extend(scrape_indeed())
        except Exception as e:
            print(f"Indeed error: {e}")

    if sources.get('gradconnection', True):
        try:
            from scrapers.gradconnection_scraper import scrape_gradconnection
            all_jobs.extend(scrape_gradconnection())
        except Exception as e:
            print(f"GradConnection error: {e}")

    print(f"\nTotal new jobs: {len(all_jobs)}")

    if all_jobs:
        print("Running AI analysis...")
        from ai.analyser import process_job
        for job in all_jobs:
            try:
                process_job(
                    job_id=job['id'],
                    title=job['title'],
                    company=job['company'],
                    description=job['description'],
                    min_score=min_doc_score
                )
            except Exception as e:
                print(f"  Failed to process {job['title']}: {e}")

    print("========== Done ==========\n")
    return len(all_jobs)

if __name__ == "__main__":
    from database import init_db
    init_db()
    run_all()
