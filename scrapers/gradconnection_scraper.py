import requests
import time
import sqlite3
from bs4 import BeautifulSoup
from database import save_job

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-AU,en;q=0.9",
}

INTERNSHIP_PAGES = [
    "https://au.gradconnection.com/internships/engineering-software/melbourne/",
    "https://au.gradconnection.com/internships/computer-science/melbourne/",
    "https://au.gradconnection.com/internships/information-technology/melbourne/",
    "https://au.gradconnection.com/internships/engineering-software/",
    "https://au.gradconnection.com/internships/computer-science/",
]

def fetch_grad_description(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, 'html.parser')
        desc = (soup.find('div', {'class': lambda x: x and 'job-description' in str(x).lower()}) or
                soup.find('div', {'id': 'job-description'}) or
                soup.find('section', {'class': lambda x: x and 'description' in str(x).lower()}))
        return desc.get_text(separator='\n', strip=True)[:3000] if desc else ""
    except:
        return ""

def scrape_gradconnection():
    print("Scraping GradConnection for internships...")
    new_jobs = []
    seen_urls = set()

    for page_url in INTERNSHIP_PAGES:
        try:
            r = requests.get(page_url, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                print(f"  GradConnection {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, 'html.parser')

            cards = (soup.find_all('div', {'class': lambda x: x and 'listing-item' in str(x)}) or
                     soup.find_all('div', {'class': lambda x: x and 'job-listing' in str(x)}) or
                     soup.find_all('article'))

            print(f"  {page_url.split('/')[-3]}: {len(cards)} cards")

            for card in cards[:12]:
                try:
                    all_links = card.find_all('a', href=True)
                    link = next((a for a in all_links
                                 if '/internships/' in a.get('href', '') or
                                 '/jobs/' in a.get('href', '')), None)

                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    if len(title) < 4 or len(title) > 150:
                        continue

                    href = link.get('href', '')
                    job_url = f"https://au.gradconnection.com{href}" if href.startswith('/') else href

                    if job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)

                    company_el = (card.find('a', {'class': lambda x: x and 'employer' in str(x).lower()}) or
                                  card.find('span', {'class': lambda x: x and 'company' in str(x).lower()}) or
                                  card.find('p', {'class': lambda x: x and 'employer' in str(x).lower()}))
                    company = company_el.get_text(strip=True) if company_el else "See job listing"

                    short_desc = card.get_text(separator=' ', strip=True)[:300]

                    job_id = save_job(
                        title=title, company=company, location="Melbourne, VIC",
                        source="GradConnection", url=job_url,
                        description=short_desc, job_type="Internship"
                    )
                    if job_id:
                        time.sleep(0.5)
                        full_desc = fetch_grad_description(job_url)
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
            print(f"  GradConnection error: {e}")

    print(f"GradConnection: {len(new_jobs)} new internships")
    return new_jobs
