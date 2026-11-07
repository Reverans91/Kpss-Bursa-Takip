
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# KPSS Bursa Takip - ilan tarama sistemi

DOSYA = Path("ilanlar.json")

QUERIES = [
    "Bursa kamu personel alımı",
    "Bursa belediye personel alımı",
    "Bursa KPSS memur alımı",
    "Bursa sözleşmeli personel alımı",
    "Bursa ön lisans kamu alımı",
    "Bursa kamu işçi alımı",
    "Bursa büro personeli alımı",
    "Bursa bilgisayar işletmeni alımı",
    "Bursa zabıta memuru alımı",
    "Bursa kamu personel ilanı"
]

# Google News üzerinden resmî kaynaklara yönelik aramalar
OFFICIAL_QUERIES = [
    "site:kariyerkapisi.gov.tr Bursa personel alımı",
    "site:osym.gov.tr KPSS Bursa tercih",
    "site:iskur.gov.tr Bursa kamu işçi alımı",
    "site:resmigazete.gov.tr Bursa personel alımı",
    "site:kamuilan.sbb.gov.tr Bursa personel alımı",
    "site:bursa.bel.tr personel alımı",
    "site:bursa.gov.tr personel alımı",
    "site:uludag.edu.tr personel alımı Bursa"
]

ALL_QUERIES = QUERIES + OFFICIAL_QUERIES

def google_news_search(query):
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=tr&gl=TR&ceid=TR:tr"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read())

    results = []

    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        date = item.findtext("pubDate", "").strip()
        source = item.findtext("source", "Google News")

        if not title or not link:
            continue

        results.append({
            "title": title,
            "source": source,
            "url": link,
            "date": date,
            "match_status": "İlan şartları kontrol edilmeli",
            "search_query": query
        })

    return results


def load_existing():
    if not DOSYA.exists():
        return []

    try:
        with open(DOSYA, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("jobs", [])

    except (json.JSONDecodeError, OSError):
        return []


def main():
    existing_jobs = load_existing()

    # URL üzerinden tekrarları önle
    jobs = {
        job.get("url"): job
        for job in existing_jobs
        if job.get("url")
    }

    errors = []

    for query in ALL_QUERIES:
        try:
            results = google_news_search(query)

            for job in results:
                jobs[job["url"]] = job

            print(f"Başarılı: {query} - {len(results)} ilan")

        except Exception as error:
            message = f"{query}: {str(error)}"
            errors.append(message)
            print("Tarama hatası:", message)

    data = {
        "updated_at": datetime.now().astimezone().isoformat(),
        "source": "Google News RSS",
        "total_jobs": len(jobs),
        "errors": errors,
        "jobs": list(jobs.values())
    }

    with open(DOSYA, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print("--------------------------------")
    print("Tarama tamamlandı.")
    print("Toplam ilan:", len(jobs))
    print("Tarama hatası:", len(errors))
    print("Dosya:", DOSYA)
    print("--------------------------------")


if __name__ == "__main__":
    main()
