from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client

import os

load_dotenv()
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
modelo = SentenceTransformer("all-MiniLM-L6-v2")


def buscar(pregunta:str, top_k:int = 3):
    query_embedding = modelo.encode(pregunta).tolist()
    result = supabase.rpc("match_politicas", {
        "query_embedding": query_embedding,
        "match_count": top_k
    }).execute()
    return result.data

def main():
    preguntas = [
        "¿Cuántos días de vacaciones me tocan después de 3 años?",
        "¿Cuándo me pagan el aguinaldo?",
        "¿Puedo trabajar desde mi casa?",
        "¿Cuántos minutos tengo para llegar tarde?",
        "Falleció un familiar, ¿Qué puedo hacer?"
    ]

    # for p in preguntas:
    #     print(f"\nPregunta: {p}")
    #     for r in buscar(p):
    #         print(f"{r['similarity']} {r['articulo']}")

    # Estilo de un chat interactivo
    print("Modo interactivo (Salir o exit para terminar)")
    while True:
        p = input("\nPregunta: ").strip()
        if p.lower() in ("salir", "exit", ""):
            break
        for r in buscar(p):
            print(f"{r['similarity']} {r['content']}") # Puede imprimir solo el artículo

if __name__ == '__main__':
    main()