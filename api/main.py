# api/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import shutil
import os

from embedder import pdf_to_text, chunk_text
from retriever import store_chunks, find_relevant_chunks
from llm_client import build_prompt, ask_llm

app = FastAPI(title="RAG API", version="1.0.0")

# --- Request/Response modelleri ---

class QueryRequest(BaseModel):
    question: str
    model: str = "mistral"
    top_k: int = 5

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]  # Cevabın dayandığı chunk'lar

# --- Endpoint'ler ---

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    PDF yükle ve hemen index'le.
    
    Küçük dosyalar için anlık, büyük dosyalar için Airflow kullan.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF yüklenebilir")
    
    # Dosyayı kaydet
    save_path = f"/data/pdfs/{file.filename}"
    os.makedirs("/data/pdfs", exist_ok=True)
    
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Pipeline çalıştır
    text = pdf_to_text(save_path)
    chunks = chunk_text(text)
    store_chunks(chunks, source_file=file.filename)
    
    return {
        "message": "PDF başarıyla yüklendi ve index'lendi",
        "filename": file.filename,
        "chunk_count": len(chunks)
    }

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Soruyu al, ilgili chunk'ları bul, LLM'e sor, cevap döndür.
    
    Bu endpoint'in akışı = RAG'in özü.
    """
    # 1. İlgili chunk'ları bul
    relevant_chunks = find_relevant_chunks(
        query=request.question, 
        top_k=request.top_k
    )
    
    if not relevant_chunks:
        return QueryResponse(
            answer="Soru ile ilgili doküman bulunamadı.",
            sources=[]
        )
    
    # 2. Prompt oluştur
    prompt = build_prompt(relevant_chunks, request.question)
    
    # 3. LLM'den cevap al
    answer = await ask_llm(prompt, model=request.model)
    
    return QueryResponse(answer=answer, sources=relevant_chunks)

@app.get("/health")
def health():
    return {"status": "ok"}