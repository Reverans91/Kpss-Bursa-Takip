import json
import hashlib
import os
import re
import feedparser
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote

DOSYA = "ilanlar.json"
ILAN_MAX_YAS_GUN = 30


def yayin_tarihi(ilan):
    try:
        dt = parsedate_to_datetime(ilan.get("date", ""))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def tarihi_guncel_mi(ilan):
    dt = yayin_tarihi(ilan)

    if dt is None:
        return True

    return datetime.now(timezone.utc) - dt <= timedelta(days=ILAN_MAX_YAS_GUN)
# Aday profili
PROFILE = {
    "city": "Bursa",
    "education": "Ön lisans",
    "department": "İşletme Yönetimi",
    "kpss_type": "P93",
    "kpss_score": 67,
    "age_range": "30-35",
    "driver_license": "B",
    "certificates": [
        "Canva",
        "Bilgisayar İşletmenliği"
    ],
    "job_types": [
        "Kamu personeli",
        "Belediye personeli",
        "Üniversite personeli",
        "Servis Rehber Personeli"
    ]
}

# Kurum bağlantıları
RESMI_KAYNAKLAR = [
    {
        "name": "Kariyer Kapısı",
        "url": "https://kariyerkapisi.gov.tr/"
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
        "name": "Kamu İlanları",
        "url": "https://kamuilan.sbb.gov.tr/"
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
        "name": "Bursa Valiliği",
        "url": "https://www.bursa.gov.tr/"
    },
    {
        "name": "Bursa İl Sağlık Müdürlüğü",
        "url": "https://bursaism.saglik.gov.tr/"
    },
    {
        "name": "Bursa İl Milli Eğitim Müdürlüğü",
        "url": "https://bursa.meb.gov.tr/"
    }
]

# Google News tamamen kaldırıldı
ARAMALAR = []


def eski_ilanlari_yukle():
    if not os.path.exists(DOSYA):
        return []

    try:
        with open(DOSYA, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        return data.get("jobs", [])

    except json.JSONDecodeError as e:
        raise RuntimeError(
            "ilanlar.json bozuk JSON içeriyor. "
            "Dosyayı kontrol etmeden üzerine yazılmadı."
        ) from e


def temizle(text):
    text = re.sub(r"<[^>]+>", " ", str(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def ilan_kimligi(ilan):
    url = ilan.get("url", "").strip()

    if url:
        return hashlib.sha256(
            url.encode("utf-8")
        ).hexdigest()

    metin = ilan.get("title", "") + ilan.get("source", "")

    return hashlib.sha256(
        metin.encode("utf-8")
    ).hexdigest()


def uygunluk_kontrol(ilan):
    title = temizle(ilan.get("title", ""))
    summary = temizle(ilan.get("summary", ""))

    text = (title + " " + summary).lower()

    warnings = []
    positives = []

    # Bursa kontrolü
    if "bursa" not in text:
        warnings.append(
            "İlanın Bursa'da olduğu doğrulanmalı"
        )
    else:
        positives.append("Bursa ifadesi bulundu")

    # Ön lisans kontrolü
    if any(word in text for word in [
        "ön lisans", "önlisans", "2 yıllık"
    ]):
        positives.append("Ön lisans ifadesi bulundu")
    else:
        warnings.append(
            "Ön lisans mezuniyet şartı kontrol edilmeli"
        )

    # KPSS puan türü
    if "p93" in text or "p 93" in text:
        positives.append("KPSS P93 ifadesi bulundu")
    else:
        warnings.append(
            "KPSS puan türü ilan metninden kontrol edilmeli"
        )

    # KPSS puanı
    warnings.append(
        "KPSS taban puanı ve 67 puanın yeterliliği kontrol edilmeli"
    )

    # Yaş kontrolü
    warnings.append(
        "Yaş sınırı 30-35 yaş aralığına göre kontrol edilmeli"
    )

    # Ehliyet
    if "b sınıfı" in text or "b ehliyet" in text:
        positives.append("B sınıfı ehliyet ifadesi bulundu")
    else:
        warnings.append(
            "Ehliyet şartı varsa B sınıfı olup olmadığı kontrol edilmeli"
        )

    # Bölüm
    if "işletme yönetimi" in text:
        positives.append("İşletme Yönetimi ifadesi bulundu")
    else:
        warnings.append(
            "İlanın kabul ettiği bölümler/nitelik kodları kontrol edilmeli"
        )

    # Servis rehber personeli
    if any(word in text for word in [
        "servis rehber personel",
        "servis rehber",
        "rehber personel"
    ]):
        positives.append(
            "Servis Rehber Personeli ifadesi bulundu"
        )

    # Sertifikalar
    if "bilgisayar işletmen" in text:
        positives.append(
            "Bilgisayar İşletmenliği ifadesi bulundu"
        )

    if "canva" in text:
        positives.append("Canva ifadesi bulundu")

    ilan["match_status"] = "Şartları kontrol et"
    ilan["warnings"] = warnings
    ilan["match_reasons"] = positives

    return ilan


def google_news_rss(query):
    url = (
        "https://news.google.com/rss/search?q="
        + quote(query + " when:30d")
        + "&hl=tr&gl=TR&ceid=TR:tr"
    )

    feed = feedparser.parse(url)

    if feed.bozo and not feed.entries:
        raise RuntimeError(
            "RSS okunamadı: " + str(feed.bozo_exception)
        )

    results = []

    for entry in feed.entries:
        title = temizle(entry.get("title", ""))
        link = entry.get("link", "")
        date = entry.get("published", "")
        summary = temizle(entry.get("summary", ""))

        if not title or not link:
            continue

        # Bursa ile ilgisi olmayan başlıkları ele
        if "bursa" not in (
            title + " " + summary
        ).lower():
            continue

        ilan = {
            "title": title,
            "source": entry.get(
                "source", {}
            ).get("title", "Google News"),
            "url": link,
            "date": date,
            "summary": summary,
            "search_query": query,
            "first_seen": datetime.now(
                timezone.utc
            ).isoformat()
        }

        results.append(uygunluk_kontrol(ilan))

    return results


def main():
    eski_ilanlar = eski_ilanlari_yukle()

    ilanlar = {}

    for ilan in eski_ilanlar:
        if tarihi_guncel_mi(ilan):
            key = ilan_kimligi(ilan)
            ilanlar[key] = ilan

    hatalar = []
    yeni_sayisi = 0

    for arama in ARAMALAR:
        try:
            bulunanlar = google_news_rss(arama)

            for ilan in bulunanlar:
                key = ilan_kimligi(ilan)

                if key not in ilanlar:
                    yeni_sayisi += 1

                # Aynı URL varsa son bilgileri güncelle
                ilanlar[key] = ilan

            print(
                "Tarandı:",
                arama,
                "- bulunan:",
                len(bulunanlar)
            )

        except Exception as error:
            hatalar.append({
                "query": arama,
                "error": str(error)
            })

            print("Tarama hatası:", arama, error)

    tum_ilanlar = list(ilanlar.values())

    # En yeni ilanları göster
    tum_ilanlar.sort(
        key=lambda x: x.get("date", ""),
        reverse=True
    )

    data = {
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "source": "Google News RSS",
        "total_jobs": len(tum_ilanlar),
        "new_jobs": yeni_sayisi,
        "errors": hatalar,
        "official_sources": RESMI_KAYNAKLAR,
        "profile": PROFILE,
        "jobs": tum_ilanlar
    }

    with open(DOSYA, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("--------------------------------")
    print("Tarama tamamlandı")
    print("Yeni ilan:", yeni_sayisi)
    print("Toplam ilan:", len(tum_ilanlar))
    print("Hata sayısı:", len(hatalar))
    print("--------------------------------")


if __name__ == "__main__":
    main()