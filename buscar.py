from dotenv import load_dotenv
from supabase import create_client
from langchain_google_genai import GoogleGenerativeAIEmbeddings

import os

TASK_TYPE_QUERY = "RETRIEVAL_QUERY"

load_dotenv()
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
modelo = GoogleGenerativeAIEmbeddings(
    model = "models/gemini-embedding-001",
    task_type = TASK_TYPE_QUERY
)

def buscar(pregunta:str, top_k:int = 3, umbral:float = 0.0) -> list[dict]:
    query_embedding = modelo.embed_query(pregunta)
    result = supabase.rpc("match_politicas_gemini", {
        "query_embedding": query_embedding,
        "match_count": top_k,
        "similarity_threshold": umbral
    }).execute()
    return result.data

def main(): # Estilo de un chat interactivo
    print("Modo interactivo (Salir o exit para terminar)")
    while True:
        p = input("\nPregunta: ").strip()
        if p.lower() in ("salir", "exit", ""):
            break
        for r in buscar(p, 3, 0.7):
            print(f"{r['similarity']} {r['content']}") # Puede imprimir solo el artículo

if __name__ == '__main__':
    main()