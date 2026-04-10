# api/llm_client.py
import httpx
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_URL = f"http://{OLLAMA_HOST}:11434"

def build_prompt(context_chunks: list[str], question: str) -> str:
    """
    RAG prompt'u oluşturur.
    
    Kritik nokta: LLM'e "sadece bu bilgiyi kullan" diyoruz.
    Böylece halüsinasyon (uydurma) riski azalır.
    """
    context = "\n\n---\n\n".join(context_chunks)
    
    prompt = f"""Aşağıdaki bağlamı kullanarak soruyu yanıtla.
Eğer bağlamda cevap yoksa "Bu bilgi dokümanlarda bulunamadı" de.

BAĞLAM:
{context}

SORU: {question}

CEVAP:"""
    
    return prompt

async def ask_llm(prompt: str, model: str = "mistral") -> str:
    """
    Ollama API'sine istek atar.
    
    async kullanıyoruz çünkü:
    - LLM cevap üretmesi saniyeler sürebilir
    - Bu sürede diğer istekleri de karşılayabilelim (non-blocking)
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False  # Şimdilik tam cevap bekleyelim
            }
        )
        
        data = response.json()
        return data["response"]