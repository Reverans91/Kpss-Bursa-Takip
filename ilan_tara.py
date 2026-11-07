import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

queries = [
    "Bursa kamu personel alımı",
    "Bursa belediye personel alımı",
    "Bursa KPSS memur alımı",
    "Bursa sözleşmeli personel alımı",
    "Bursa ön lisans kamu alımı"
]

jobs = {}

for query in queries:
    try:
        url = (
            "https://news.google.com/rss/search?q="
            + urllib.parse.quote(query)
            + "&hl=tr&gl=TR&ceid=TR:tr"
        )

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        root = ET.fromstring(
            urllib.request.urlopen(request, timeout=20).read()
        )

        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            date = item.findtext("pubDate", "")

            if "bursa" not in title.lower():
                continue

            if link:
                jobs[link] = {
                    "title": title,
                    "source": "Google News",
                    "url": link,
                    "date": date,
                    "match_status": "İlan şartları kontrol edilmeli"
                }

    except Exception as error:
        print("Tarama hatası:", error)

data = {
    "updated_at": datetime.now().astimezone().isoformat(),
    "jobs": list(jobs.values())
}

with open("ilanlar.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print("Bulunan ilan:", len(jobs))