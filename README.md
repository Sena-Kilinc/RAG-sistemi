# 🧠 RAG Document Intelligence System

> Dokümanlarınızı yükleyin, sorularınızı sorun. Yapay zeka, belgelerinizi anlayarak doğru cevapları üretir.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6B35?style=flat-square)
![Airflow](https://img.shields.io/badge/Airflow-2.8-017CEE?style=flat-square&logo=apacheairflow&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-000000?style=flat-square)

---

## 📋 İçindekiler

- [Proje Hakkında](#-proje-hakkında)
- [Mimari](#-mimari)
- [Teknoloji Stack](#-teknoloji-stack)
- [Proje Yapısı](#-proje-yapısı)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [API Referansı](#-api-referansı)
- [Airflow Pipeline](#-airflow-pipeline)
- [Geliştirme](#-geliştirme)
- [Sorun Giderme](#-sorun-giderme)

---

## 🎯 Proje Hakkında

Bu proje, **Retrieval-Augmented Generation (RAG)** mimarisi kullanarak PDF dokümanlarınız üzerinde doğal dil sorguları çalıştırmanızı sağlayan, tamamen **yerel çalışan** (cloud gerektirmeyen) bir yapay zeka sistemidir.

### Ne yapar?

1. PDF yüklersiniz
2. Sistem metni parçalara böler ve vektörleştirir
3. Soru sorarsınız
4. Sistem semantik arama ile ilgili paragrafları bulur
5. Yerel LLM bu bilgilerle doğru cevabı üretir

### Neden bu proje?

- ✅ **100% Yerel** — Verileriniz dışarı çıkmaz
- ✅ **Cloud maliyeti yok** — Kendi donanımınızda çalışır
- ✅ **Production-ready** — Docker, async API, pipeline orchestration
- ✅ **Türkçe desteği** — Çok dilli embedding modeli

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────┐
│                    OFFLINE PIPELINE                      │
│                   (Apache Airflow)                       │
│                                                          │
│  PDF → Text Extraction → Chunking → Embedding → ChromaDB│
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                     ONLINE PIPELINE                      │
│                       (FastAPI)                          │
│                                                          │
│  User Query → Embed Query → Similarity Search → LLM     │
└─────────────────────────────────────────────────────────┘

┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│  FastAPI │  │ ChromaDB │  │  Ollama  │  │   Airflow    │
│  :8000   │  │  :8001   │  │  :11434  │  │    :8080     │
└──────────┘  └──────────┘  └──────────┘  └──────────────┘
      └──────────────┴──────────────┴──────────────┘
                      Docker Network
```

### RAG Nasıl Çalışır?

**Indexleme aşaması (offline):**
```
PDF Dosyası
    │
    ▼
PyMuPDF ile metin çıkarma
    │
    ▼
500 token'lık chunk'lara bölme (50 token overlap)
    │
    ▼
sentence-transformers ile 384 boyutlu vektör üretme
    │
    ▼
ChromaDB'ye kaydetme (cosine similarity index)
```

**Sorgulama aşaması (online):**
```
Kullanıcı sorusu
    │
    ▼
Aynı model ile vektöre çevirme
    │
    ▼
ChromaDB'de en yakın 5 chunk'ı bulma
    │
    ▼
Prompt oluşturma: [Context] + [Soru]
    │
    ▼
Ollama (Mistral) ile cevap üretme
    │
    ▼
Cevap + Kaynak chunk'lar
```

---

## 🧰 Teknoloji Stack

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| **API** | FastAPI + Uvicorn | Async REST API, otomatik Swagger UI |
| **Embedding** | sentence-transformers | `paraphrase-multilingual-MiniLM-L12-v2` — Türkçe dahil 50+ dil |
| **Vector DB** | ChromaDB | Cosine similarity search, persistent storage |
| **LLM** | Ollama + Mistral 7B | Yerel çalışan, cloud gerektirmeyen |
| **Pipeline** | Apache Airflow | DAG tabanlı orchestration, scheduler |
| **Database** | PostgreSQL | Airflow metadata storage |
| **Container** | Docker + Compose | Tüm servisler izole, tek komutla başlatma |
| **PDF** | PyMuPDF (fitz) | Hızlı metin çıkarma |

---

## 📁 Proje Yapısı

```
rag-project/
│
├── docker-compose.yml          # Tüm servislerin orchestration'ı
│
├── api/                        # FastAPI uygulaması
│   ├── Dockerfile
│   ├── main.py                 # Endpoint'ler: /upload, /query, /health
│   └── requirements.txt
│
├── src/                        # Paylaşılan iş mantığı (api + airflow)
│   ├── embedder.py             # PDF okuma, chunking, embedding
│   ├── retriever.py            # ChromaDB CRUD işlemleri
│   └── llm_client.py          # Ollama API istemcisi
│
├── airflow/
│   └── dags/
│       └── ingest_pipeline.py  # PDF ingestion DAG'ı
│
└── data/
    └── pdfs/                   # Yüklenecek PDF'ler buraya
```

---

## 🚀 Kurulum

### Gereksinimler

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac/Linux)
- En az 8GB RAM (Mistral için)
- En az 10GB disk alanı

### 1. Repoyu klonla

```bash
git clone https://github.com/kullanici/rag-project.git
cd rag-project
```

### 2. `data/pdfs/` klasörünü oluştur

```bash
# Linux/Mac
mkdir -p data/pdfs

# Windows PowerShell
New-Item -ItemType Directory -Force -Path data\pdfs
```

### 3. Servisleri başlat

```bash
docker compose up --build -d
```

> ⏳ İlk build 5-10 dakika sürebilir. `sentence-transformers` kütüphanesi büyük.

### 4. Servislerin durumunu kontrol et

```bash
docker compose ps
```

Tüm servisler `Up` görünmeli:

```
NAME         STATUS
api-1        Up
chroma-1     Up
ollama-1     Up
airflow-1    Up
postgres-1   Up
```

### 5. LLM modelini indir

```bash
# Mistral 7B (~4.4GB) — önerilen
docker exec -it $(docker compose ps -q ollama) ollama pull mistral

# TinyLlama (~637MB) — düşük donanım için
docker exec -it $(docker compose ps -q ollama) ollama pull tinyllama
```

### 6. Modeli ön-ısıt (ilk istek yavaş olmasın)

```bash
# Linux/Mac
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral", "prompt": "merhaba", "stream": false}'

# Windows PowerShell
$body = '{"model": "mistral", "prompt": "merhaba", "stream": false}'
Invoke-WebRequest -Uri "http://localhost:11434/api/generate" `
  -Method POST -ContentType "application/json" -Body $body
```

---

## 📖 Kullanım

### Swagger UI (Önerilen)

Tarayıcıda açın: **http://localhost:8000/docs**

Tüm endpoint'leri görsel olarak test edebilirsiniz.

---

### PDF Yükleme

**Linux/Mac:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/your/document.pdf"
```

**Windows PowerShell:**
```powershell
curl -Uri "http://localhost:8000/upload" `
  -Method POST `
  -Form @{file = Get-Item "C:\path\to\document.pdf"}
```

**Başarılı cevap:**
```json
{
  "message": "PDF başarıyla yüklendi ve index'lendi",
  "filename": "document.pdf",
  "chunk_count": 47
}
```

---

### Soru Sorma

**Linux/Mac:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Bu dokümanda ana konu nedir?",
    "model": "mistral",
    "top_k": 5
  }'
```

**Windows PowerShell:**
```powershell
$body = '{
  "question": "Bu dokümanda ana konu nedir?",
  "model": "mistral",
  "top_k": 5
}'

Invoke-WebRequest -Uri "http://localhost:8000/query" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**Cevap:**
```json
{
  "answer": "Dokümanda makine öğrenmesi yöntemleri ve...",
  "sources": [
    "...ilgili paragraf 1...",
    "...ilgili paragraf 2..."
  ]
}
```

---

## 📡 API Referansı

### `POST /upload`

PDF dosyası yükler ve otomatik olarak index'ler.

| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| `file` | `multipart/form-data` | PDF dosyası |

### `POST /query`

Yüklenen dokümanlara soru sorar.

| Parametre | Tip | Varsayılan | Açıklama |
|-----------|-----|------------|----------|
| `question` | `string` | — | Sorulacak soru |
| `model` | `string` | `mistral` | Kullanılacak LLM (`mistral`, `tinyllama`) |
| `top_k` | `integer` | `5` | Getirilecek maksimum chunk sayısı |

### `GET /health`

Servisin ayakta olup olmadığını kontrol eder.

```json
{"status": "ok"}
```

---

## ⏱️ Airflow Pipeline

**Airflow UI:** http://localhost:8080

Varsayılan giriş bilgileri için:
```bash
docker compose logs airflow | grep "Login with"
```

### `pdf_ingestion_pipeline` DAG'ı

Her saat otomatik çalışır. `data/pdfs/` klasörüne yeni PDF koymanız yeterli.

```
scan_pdfs → process_pdfs
```

- **scan_pdfs:** Klasörü tarar, daha önce işlenmemiş PDF'leri bulur
- **process_pdfs:** Her PDF için metin çıkarma → chunking → embedding → ChromaDB yazma

### Manuel Çalıştırma

1. Airflow UI'da `pdf_ingestion_pipeline` DAG'ını bulun
2. ▶ **Trigger DAG** butonuna basın
3. DAG Run detaylarını izleyin

---

## 🛠️ Geliştirme

### Servisleri ayrı ayrı yeniden başlatma

```bash
# Sadece API'yi yeniden build et (kod değişikliği sonrası)
docker compose up --build -d api

# Sadece Airflow'u yeniden başlat (DAG değişikliği sonrası)
docker compose restart airflow
```

### Logları takip etme

```bash
# API logları
docker compose logs api --follow

# Airflow logları
docker compose logs airflow --follow

# Tüm servisler
docker compose logs --follow
```

### ChromaDB'deki verileri görme

```bash
curl http://localhost:8001/api/v1/collections
```

### Tüm verileri sıfırlama

```bash
docker compose down -v   # volume'ları da sil
docker compose up -d
```

---

## 🔧 Sorun Giderme

### `ReadTimeout` hatası

Ollama modeli yavaş cevap veriyor. Çözüm:

1. Modeli ön-ısıt (bkz. [Kurulum adım 6](#6-modeli-ön-ısıt-ilk-istek-yavaş-olmasın))
2. `tinyllama` modeli deneyin — çok daha hızlı
3. `llm_client.py`'de timeout değerini artırın: `timeout=300.0`

### `ModuleNotFoundError: No module named 'embedder'`

`src/` klasörünün mount edildiğinden ve `PYTHONPATH` ayarlandığından emin olun:

```yaml
environment:
  - PYTHONPATH=/src
volumes:
  - ./src:/src
```

### Airflow başlamıyor (SQLite + LocalExecutor hatası)

`docker-compose.yml`'de PostgreSQL kullandığınızdan emin olun:

```yaml
- AIRFLOW__CORE__EXECUTOR=LocalExecutor
- AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
```

### Port çakışması

```yaml
# docker-compose.yml'de portu değiştirin
ports:
  - "8001:8000"  # 8000 kullanılıyorsa
```

### `version` obsolete uyarısı

`docker-compose.yml` dosyanızdan `version: '3.9'` satırını kaldırın. Bu sadece uyarı, hata değil.

---

## 📈 Sonraki Adımlar

- [ ] **Streaming Response** — Cevapların kelime kelime gelmesi
- [ ] **Conversation Memory** — Önceki soruları hatırlama
- [ ] **JWT Authentication** — API güvenliği
- [ ] **Multi-document Search** — Birden fazla PDF'de arama
- [ ] **Frontend UI** — React/HTML sohbet arayüzü
- [ ] **Re-ranking** — Bulunan chunk'ları ikinci kez sıralama

---

## 📄 Lisans

MIT License — Özgürce kullanın, değiştirin, dağıtın.

---

<p align="center">
  Tamamen yerel, tamamen sizin. ☁️❌
</p>
