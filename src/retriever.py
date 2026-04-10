# api/retriever.py
import chromadb
import os
from embedder import embed_texts

# ChromaDB istemcisi — Docker'daki servise bağlan
client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "localhost"),
    port=8000
)

# "Collection" = bir tablo gibi düşün
# metadata ile hangi PDF'den geldiğini de saklıyoruz
collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}  # Benzerlik ölçütü: cosine distance
)

def store_chunks(chunks: list[str], source_file: str):
    """
    Chunk'ları ChromaDB'ye yazar.
    
    Her chunk için:
    - id: benzersiz kimlik
    - embedding: 384 boyutlu vektör  
    - document: ham metin (cevap üretirken lazım)
    - metadata: hangi dosyadan, kaçıncı chunk
    """
    embeddings = embed_texts(chunks)
    
    collection.add(
        ids=[f"{source_file}_chunk_{i}" for i in range(len(chunks))],
        embeddings=embeddings,
        documents=chunks,
        metadatas=[{"source": source_file, "chunk_index": i} 
                   for i in range(len(chunks))]
    )
    print(f"✅ {len(chunks)} chunk ChromaDB'ye yazıldı.")

def find_relevant_chunks(query: str, top_k: int = 5) -> list[str]:
    """
    Soruya en yakın chunk'ları bulur.
    
    1. Soruyu vektöre çevir
    2. ChromaDB tüm vektörlerle kıyasla
    3. En yakın top_k tanesini döndür
    
    Bu işlem O(log n) — milyonlarca chunk'ta bile hızlı!
    """
    query_embedding = embed_texts([query])[0]
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # distances → 0'a yakın = çok benzer, 1'e yakın = çok farklı
    chunks = results["documents"][0]
    distances = results["distances"][0]
    
    # Çok alakasız chunk'ları filtrele (cosine distance > 0.7)
    relevant = [
        chunk for chunk, dist in zip(chunks, distances) 
        if dist < 0.7
    ]
    
    return relevant