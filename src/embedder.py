# api/embedder.py
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF
from typing import List

# Model bir kere yükle, her seferinde yeniden yükleme
# "paraphrase-multilingual" → Türkçe dahil çok dilli destek!
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def pdf_to_text(pdf_path: str) -> str:
    """PDF'den ham metin çıkarır."""
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Metni örtüşen parçalara böler.
    
    Neden overlap (örtüşme)?
    Bir cümlenin yarısı bir chunk'ta, diğer yarısı başka chunk'ta kalmasın.
    50 karakterlik örtüşme bu sorunu çözer.
    """
    words = text.split()
    chunks = []
    i = 0
    
    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)
        i += chunk_size - overlap  # overlap kadar geri al
    
    return chunks

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Metinleri vektöre çevirir.
    
    "Merhaba dünya" → [0.23, -0.41, 0.88, ...]  (384 boyutlu vektör)
    
    Anlamca benzer metinler → birbirine yakın vektörler
    Bu sayede "köpek" araması "kedi" chunk'larını da bulabilir.
    """
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()