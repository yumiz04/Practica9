"""Configuración y carga de los 3 modelos de embeddings.

- minilm : all-MiniLM-L6-v2        (local, 384 dim)
- bge    : BAAI/bge-m3             (local, 1024 dim)
- gemini : gemini-embedding-001    (API de pago/cuota, 3072 dim)

Gemini es opcional: si no hay GOOGLE_API_KEY (o GEMINI_API_KEY) se omite.
"""
import os
import time

from dotenv import load_dotenv

load_dotenv()

MODELOS = {
    "minilm": {"nombre": "all-MiniLM-L6-v2", "columna": "emb_minilm",
               "dims": 384, "tipo": "local"},
    "bge": {"nombre": "BAAI/bge-m3", "columna": "emb_bge",
            "dims": 1024, "tipo": "local"},
    "gemini": {"nombre": "models/gemini-embedding-001", "columna": "emb_gemini",
               "dims": 3072, "tipo": "api"},
}

_modelos = {}      # modelos ya cargados
_cache_query = {}  # (clave, pregunta) -> vector, para no repetir llamadas


def _api_key():
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


def disponibles():
    """Claves de modelos que se pueden usar con la configuración actual."""
    return [k for k in MODELOS if k != "gemini" or _api_key()]


def cargar(clave: str, task_type: str | None = None):
    """Carga (una sola vez) el modelo. task_type solo aplica a Gemini."""
    tt = task_type if clave == "gemini" else None
    llave = (clave, tt)
    if llave not in _modelos:
        nombre = MODELOS[clave]["nombre"]
        if clave == "gemini":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            _modelos[llave] = GoogleGenerativeAIEmbeddings(
                model=nombre, task_type=tt, google_api_key=_api_key())
        else:
            from sentence_transformers import SentenceTransformer
            _modelos[llave] = SentenceTransformer(nombre)
    return _modelos[llave]


def _reintentar(fn, intentos: int = 5, espera: float = 2.0):
    """Reintenta con espera creciente (útil para límites de la API de Gemini)."""
    for i in range(intentos):
        try:
            return fn()
        except Exception as e:
            if i == intentos - 1:
                raise
            print(f"   (reintento {i + 1}/{intentos - 1} por: {e})")
            time.sleep(espera * 2 ** i)


def embed_documentos(clave: str, textos: list[str], tam_lote: int = 20):
    """Vectoriza chunks para guardarlos. Devuelve lista de listas de floats."""
    if clave == "gemini":
        modelo = cargar("gemini", "RETRIEVAL_DOCUMENT")
        todos = []
        for i in range(0, len(textos), tam_lote):
            lote = textos[i:i + tam_lote]
            todos.extend(_reintentar(lambda: modelo.embed_documents(lote)))
            if i + tam_lote < len(textos):
                time.sleep(0.5)
        return todos
    modelo = cargar(clave)
    return modelo.encode(textos, normalize_embeddings=True).tolist()


def embed_consulta(clave: str, pregunta: str):
    """Vectoriza una pregunta (con caché para no repetir llamadas)."""
    llave = (clave, pregunta)
    if llave not in _cache_query:
        if clave == "gemini":
            modelo = cargar("gemini", "RETRIEVAL_QUERY")
            _cache_query[llave] = _reintentar(lambda: modelo.embed_query(pregunta))
        else:
            modelo = cargar(clave)
            _cache_query[llave] = modelo.encode(
                pregunta, normalize_embeddings=True).tolist()
    return _cache_query[llave]
