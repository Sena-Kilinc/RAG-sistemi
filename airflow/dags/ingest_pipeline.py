# airflow/dags/ingest_pipeline.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import sys

# API modüllerine erişim
sys.path.insert(0, "/api")

# DAG konfigürasyonu
default_args = {
    "owner": "airflow",
    "retries": 2,                          # Hata durumunda 2 kez dene
    "retry_delay": timedelta(minutes=5),   # Denemeler arası 5 dk bekle
}

def scan_new_pdfs(**context):
    """
    /data/pdfs klasörünü tara, işlenmemiş PDF'leri bul.
    
    XCom (Cross-Communication) ile bir sonraki task'a veri aktar.
    """
    pdf_dir = "/data/pdfs"
    processed_file = "/data/processed.txt"
    
    # Daha önce işlenenleri oku
    processed = set()
    if os.path.exists(processed_file):
        with open(processed_file) as f:
            processed = set(f.read().splitlines())
    
    # Yeni PDF'leri bul
    all_pdfs = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    new_pdfs = [f for f in all_pdfs if f not in processed]
    
    print(f"Yeni PDF sayısı: {len(new_pdfs)}")
    
    # Sonraki task'a ilet (XCom)
    context["ti"].xcom_push(key="new_pdfs", value=new_pdfs)
    return new_pdfs

def process_pdfs(**context):
    """
    Yeni PDF'leri işle: metin çıkar → chunk → embed → kaydet.
    
    Her PDF için ayrı işlem — hata bir PDF'yi etkiler, hepsini değil.
    """
    from embedder import pdf_to_text, chunk_text
    from retriever import store_chunks
    
    # Önceki task'tan PDF listesini al
    new_pdfs = context["ti"].xcom_pull(key="new_pdfs", task_ids="scan_pdfs")
    
    processed_file = "/data/processed.txt"
    
    for pdf_name in new_pdfs:
        try:
            pdf_path = f"/data/pdfs/{pdf_name}"
            print(f"İşleniyor: {pdf_name}")
            
            text = pdf_to_text(pdf_path)
            chunks = chunk_text(text)
            store_chunks(chunks, source_file=pdf_name)
            
            # İşlendi olarak işaretle
            with open(processed_file, "a") as f:
                f.write(pdf_name + "\n")
            
            print(f"✅ {pdf_name}: {len(chunks)} chunk eklendi")
            
        except Exception as e:
            print(f"❌ {pdf_name} hata: {e}")
            # Hata loglansın ama pipeline devam etsin

# DAG tanımı
with DAG(
    dag_id="pdf_ingestion_pipeline",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@hourly",   # Her saat çalış
    catchup=False,                 # Geçmiş çalıştırmaları atla
    tags=["rag", "ingestion"],
) as dag:
    
    scan_task = PythonOperator(
        task_id="scan_pdfs",
        python_callable=scan_new_pdfs,
    )
    
    process_task = PythonOperator(
        task_id="process_pdfs",
        python_callable=process_pdfs,
    )
    
    # Task sırası: önce tara, sonra işle
    scan_task >> process_task