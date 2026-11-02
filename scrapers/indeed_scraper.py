import requests
import time
import sqlite3
from bs4 import BeautifulSoup
from database import save_job

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-AU,en;q=0.9",
}

INTERNSHIP_TERMS = [
    "software+developer+intern",
    "software+engineer+intern",
    "java+intern",
    "android+developer+intern",
    "backend+developer+intern",
    "IT+intern",
    "technology+internship",
]

def fetch_indeed_description(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, 'html.parser')
        desc = (soup.find('div', {'id': 'jobDescriptionText'}) or
                soup.find('div', {'class': lambda x: x and 'jobsearch-jobDescriptionText' in str(x)}))
        return desc.get_text(separator='\n', strip=True)[:3000] if desc else ""
    except:
        return ""

def scrape_indeed():
    print("Scraping Indeed for internships...")
    new_jobs = []
    seen_urls = set()

    for term in INTERNSHIP_TERMS:
        url = f"https://au.indeed.com/jobs?q={term}&l=Melbourne+VIC&sort=date&fromage=14&jt=internship"
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                print(f"  Indeed {r.status_code} for {term}")
                continue

            soup = BeautifulSoup(r.text, 'html.parser')
            cards = soup.find_all('div', {'class': lambda x: x and 'job_seen_beacon' in str(x)})
            if not cards:
                cards = soup.find_all('div', {'data-testid': 'slider_item'})

            print(f"  '{term}': {len(cards)} cards")

            for card in cards[:8]:
                try:
                    title_el = (card.find('h2', {'class': lambda x: x and 'jobTitle' in str(x)}) or
                                card.find('a', {'data-testid': 'job-title'}))
                    if not title_el:
                        continue

                    a_tag = title_el.find('a') if title_el.name != 'a' else title_el
                    if not a_tag:
                        continue

                    title = a_tag.get_text(strip=True)
                    href = a_tag.get('href', '')
                    job_url = f"https://au.indeed.com{href}" if href.startswith('/') else href
                    job_url = job_url.split('&')[0]

                    if job_url in seen_urls or not job_url:
                        continue
                    seen_urls.add(job_url)

                    company_el = (card.find('span', {'data-testid': 'company-name'}) or
                                  card.find('span', {'class': lambda x: x and 'companyName' in str(x)}))
                    company = company_el.get_text(strip=True) if company_el else "See job listing"

                    loc_el = (card.find('div', {'data-testid': 'text-location'}) or
                              card.find('div', {'class': lambda x: x and 'companyLocation' in str(x)}))
                    location = loc_el.get_text(strip=True) if loc_el else "Melbourne, VIC"

                    sal_el = card.find('div', {'class': lambda x: x and 'salary' in str(x).lower()})
                    salary = sal_el.get_text(strip=True) if sal_el else ""

                    short_desc = card.get_text(separator=' ', strip=True)[:300]

                    job_id = save_job(
                        title=title, company=company, location=location,
                        source="Indeed", url=job_url, description=short_desc,
                        salary=salary, job_type="Internship"
                    )
                    if job_id:
                        time.sleep(0.5)
                        full_desc = fetch_indeed_description(job_url)
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

            time.sleep(1.5)

        except Exception as e:
            print(f"  Indeed error: {e}")

    print(f"Indeed: {len(new_jobs)} new internships")
    return new_jobs
