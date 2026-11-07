
import json
import os
import re
import hashlib
import requests
import feedparser
from datetime import datetime, timezone
from urllib.parse import quote

DOSYA = "ilanlar.json"

# Resmî kurum ve başvuru kaynakları
RESMI_KAYNAKLAR = [
    {
        "name": "Kariyer Kapısı",
        "url": "https://isealimkariyerkapisi.cbiko.gov.tr/"
    },
    {
        "name": "ÖSYM",
        "url": "https://www.osym.gov.tr/"
    },
    {
        "name": "İŞKUR",
        "url": "https://www.iskur.gov.tr/"
    },
    {
        "name": "Resmî Gazete",
        "url": "https://www.resmigazete.gov.tr/"
    },
    {
        "name": "Bursa Büyükşehir Belediyesi",
        "url": "https://www.bursa.bel.tr/"
    },
    {
        "name": "Bursa Uludağ Üniversitesi",
        "url": "https://www.uludag.edu.tr/"
    },
    {
        "name": "Bursa Teknik Üniversitesi",
        "url": "https://www.btu.edu.tr/"
    },
    {
        "name": "Bursa İş Ofisi",
        "url": "https://bursaisofisi.bursa.bel.tr/Home/ilanarama"
    }
]

# Bursa ve kamu personeli için arama terimleri
ARAMALAR = [
    "Bursa kamu personel alımı",
    "Bursa memur alımı KPSS",
    "Bursa büro personeli alımı",
    "Bursa ön lisans personel alımı",
    "Bursa belediye personel alımı",
    "Bursa sözleşmeli personel alımı",
    "Bursa kamu işçi alımı İŞKUR",
    "Bursa bilgisayar işletmeni alımı",
    "Bursa veri hazırlama kontrol işletmeni",
    "Bursa İşletme Yönetimi mezunu personel alımı",
    "Bursa KPSS P93 alımı",
    "Bursa KPSS 67 puan personel alımı",
    "Bursa kamu şoför alımı B ehliyet",
    "Bursa grafik tasarım personel alımı",
    "Bursa Halk Eğitim sertifika kamu alımı"
]

# Ön lisans mezunlarına yönelik kelimeler
EGITIM_KELIMELERI = [
    "ön lisans", "önlisans", "associate",
    "büro personeli", "memur", "bilgisayar işletmeni",
    "veri hazırlama", "kontrol işletmeni",
    "destek personeli", "şoför", "işçi",
    "personel alımı", "kamu işçisi"
]

# Bu ifadeler ilanı otomatik elemek için değil,
# kullanıcıya dikkat uyarısı göstermek için kullanılır.
UYARI_KELIMELERI = [
    "lisans mezunu", "4 yıllık", "yüksek lisans",
    "KPSS P3", "KPSSP3", "KPSS P1",
    "KPSS P2", "KPSS P94", "lise mezunu",
    "35 yaşını doldurmamış", "30 yaşını doldurmamış",
    "sertifika zorunlu", "belge zorunlu"
]

def eski_ilanlari_yukle():
    if not os.path.exists(DOSYA):
        return []

    try:
        with open(DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
            return veri.get("jobs", [])
    except Exception:
        return []

def ilan_kimligi(ilan):
    metin = (
        ilan.get("title", "") +
        ilan.get("url", "")
    )
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()

def uygunluk_kontrol(ilan):
    metin = (
        ilan.get("title", "") + " " +
        ilan.get("summary", "")
    ).lower()

    uyarilar = []

    if not any(k.lower() in metin for k in EGITIM_KELIMELERI):
        uyarilar.append("Ön lisans şartı kontrol edilmeli")

    if any(k.lower() in metin for k in UYARI_KELIMELERI):
        uyarilar.append("KPSS, yaş, mezuniyet veya sertifika şartı kontrol edilmeli")

    if "67" in metin:
        uyarilar.append("67 puan şartı/alt sınırı kontrol edilmeli")

    if "p93" not in metin and "p 93" not in metin:
        uyarilar.append("KPSS P93 şartı ilanın metninde doğrulanmalı")

    ilan["match_status"] = (
        "Şartları kontrol et" if uyarilar
        else "İncelenecek ilan"
    )
    ilan["warnings"] = uyarilar

    return ilan

def google_news_rss(aranan):
    url = (
        "https://news.google.com/rss/search?q="
        + quote(aranan + " when:30d")
        + "&hl=tr&gl=TR&ceid=TR:tr"
    )

    feed = feedparser.parse(url)
    bulunan = []

    for entry in feed.entries:
        ilan = {
            "title": entry.get("title", ""),
            "source": entry.get("source", {}).get(
                "title", "Google News RSS"
            ),
            "url": entry.get("link", ""),
            "date": entry.get("published", ""),
            "search_query": aranan,
            "summary": entry.get("summary", "")
        }

        bulunan.append(uygunluk_kontrol(ilan))

    return bulunan

def resmi_kaynaklari_ekle():
    return [
        {
            "title": kaynak["name"],
            "source": "Resmî kurum bağlantısı",
            "url": kaynak["url"],
            "date": "",
            "search_query": "Resmî kaynak",
            "match_status": "Kurum ilanlarını kontrol et",
            "warnings": []
        }
        for kaynak in RESMI_KAYNAKLAR
    ]

def main():
    ilanlar = eski_ilanlari_yukle()
    kimlikler = {ilan_kimligi(i) for i in ilanlar}

    yeni_ilanlar = []
    hatalar = []

    for arama in ARAMALAR:
        try:
            sonuçlar = google_news_rss(arama)

            for ilan in sonuçlar:
                kimlik = ilan_kimligi(ilan)

                if kimlik not in kimlikler:
                    kimlikler.add(kimlik)
                    yeni_ilanlar.append(ilan)

        except Exception as e:
            hatalar.append({
                "arama": arama,
                "hata": str(e)
            })

    tum_ilanlar = yeni_ilanlar + ilanlar

    veri = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Google News RSS + resmî kurum bağlantıları",
        "total_jobs": len(tum_ilanlar),
        "new_jobs": len(yeni_ilanlar),
        "errors": hatalar,
        "official_sources": resmi_kaynaklari_ekle(),
        "profile": {
            "city": "Bursa",
            "education": "Ön lisans",
            "department": "İşletme Yönetimi",
            "kpss_type": "P93",
            "kpss_score": 67,
            "age_range": "30-35",
            "driver_license": "B",
            "certificates": ["Canva", "Grafik tasarım"]
        },
        "jobs": tum_ilanlar
    }

    with open(DOSYA, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)

    print("Tarama tamamlandı.")
    print("Yeni ilan:", len(yeni_ilanlar))
    print("Toplam ilan:", len(tum_ilanlar))
    print("Hata:", len(hatalar))

if __name__ == "__main__":
    main()
