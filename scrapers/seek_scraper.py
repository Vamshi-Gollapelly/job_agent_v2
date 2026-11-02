import requests
import time
import sqlite3
from bs4 import BeautifulSoup
from database import save_job

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}

INTERNSHIP_TERMS = [
    "software+developer+intern",
    "software+engineer+intern",
    "java+intern",
    "android+intern",
    "backend+intern",
    "IT+internship",
    "technology+intern",
    "graduate+intern+software",
]

def fetch_job_description(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, 'html.parser')
        desc = (soup.find('div', {'data-testid': 'jobad-details-content'}) or
                soup.find('div', {'class': lambda x: x and 'job-details' in str(x).lower()}) or
                soup.find('div', {'id': lambda x: x and 'job' in str(x).lower()}))
        return desc.get_text(separator='\n', strip=True)[:3000] if desc else ""
    except:
        return ""

def scrape_seek():
    print("Scraping Seek for internships...")
    new_jobs = []
    seen_urls = set()

    for term in INTERNSHIP_TERMS:
        url = f"https://www.seek.com.au/jobs?keywords={term}&where=Melbourne+VIC&sortmode=ListedDate"
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                print(f"  Seek {r.status_code} for {term}")
                continue

            soup = BeautifulSoup(r.text, 'html.parser')
            cards = (soup.find_all('article', {'data-testid': 'job-card'}) or
                     soup.find_all('article', {'data-card-type': 'JobCard'}) or
                     soup.find_all('article'))

            print(f"  '{term}': {len(cards)} cards")

            for card in cards[:8]:
                try:
                    title_el = (card.find('a', {'data-testid': 'job-title'}) or
                                card.find('h3', {'data-automation': 'jobTitle'}) or
                                card.find('a', href=lambda h: h and '/job/' in str(h)))
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    href = title_el.get('href', '')
                    if not href:
                        continue

                    job_url = f"https://www.seek.com.au{href}" if href.startswith('/') else href
                    job_url = job_url.split('?')[0]

                    if job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)

                    company_el = (card.find('a', {'data-testid': 'company-name'}) or
                                  card.find('span', {'data-testid': 'company-name'}) or
                                  card.find('a', {'data-automation': 'jobCompany'}))
                    company = company_el.get_text(strip=True) if company_el else "See job listing"

                    loc_el = (card.find('span', {'data-testid': 'job-card-location'}) or
                              card.find('span', {'data-automation': 'jobCardLocation'}))
                    location = loc_el.get_text(strip=True) if loc_el else "Melbourne, VIC"

                    sal_el = card.find('span', {'data-testid': 'job-card-salary'})
                    salary = sal_el.get_text(strip=True) if sal_el else ""

                    short_desc = card.get_text(separator=' ', strip=True)[:300]

                    job_id = save_job(
                        title=title, company=company, location=location,
                        source="Seek", url=job_url, description=short_desc,
                        salary=salary, job_type="Internship"
                    )
                    if job_id:
                        time.sleep(0.5)
                        full_desc = fetch_job_description(job_url)
                        if full_desc:
                            conn = sqlite3.connect('jobs.db')
                            conn.execute('UPDATE jobs SET description=? WHERE id=?', (full_desc, job_id))
                            conn.commit()
                            conn.close()
                            short_desc = full_desc

                        new_jobs.append({'id': job_id, 'title': title,
                                         'company': company, 'description': short_desc})
                        print(f"    Saved: {title} @ {company}")

                except Exception as e:
                    print(f"    Card error: {e}")

            time.sleep(1)

        except Exception as e:
            print(f"  Seek error: {e}")

    print(f"Seek: {len(new_jobs)} new internships")
    return new_jobs
