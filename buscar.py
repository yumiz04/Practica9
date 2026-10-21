"""Búsqueda: línea base (tabla de clase) y variantes (politicas_bench).

Uso:
  python buscar.py                                   # línea base (tabla de clase)
  python buscar.py --modelo bge --estrategia palabras
  python buscar.py --modelo gemini --estrategia articulo --umbral 0.68
"""
import argparse
import os

from dotenv import load_dotenv
from supabase import create_client

from modelos import MODELOS, cargar, embed_consulta
from chunking import ESTRATEGIAS

load_dotenv()
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


# Línea base (parte 1): tabla politicas_chunks, artículo + MiniLM
def buscar(pregunta: str, top_k: int = 3):
    query_embedding = cargar("minilm").encode(pregunta).tolist()
    result = supabase.rpc("match_politicas", {
        "query_embedding": query_embedding,
        "match_count": top_k
    }).execute()
    return result.data


# Variantes (partes 2 y 3): tabla politicas_bench
def crear_buscar(estrategia: str, clave: str, umbral: float = 0.0):
    """Devuelve una función buscar(pregunta, k). Con umbral > 0 descarta los
    resultados cuya similitud sea menor (puede devolver lista vacía)."""
    def _buscar(pregunta: str, top_k: int = 3):
        emb = embed_consulta(clave, pregunta)
        result = supabase.rpc(f"buscar_{clave}", {
            "query_embedding": emb,
            "estrategia_f": estrategia,
            "match_count": top_k
        }).execute()
        datos = result.data
        if umbral > 0:
            datos = [r for r in datos if r["similarity"] >= umbral]
        return datos

    return _buscar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", choices=list(MODELOS))
    ap.add_argument("--estrategia", choices=list(ESTRATEGIAS), default="articulo")
    ap.add_argument("--umbral", type=float, default=0.0)
    args = ap.parse_args()

    if args.modelo:
        fn = crear_buscar(args.estrategia, args.modelo, args.umbral)
        print(f"Modo interactivo: {args.modelo} / {args.estrategia} "
              f"(umbral {args.umbral})")
    else:
        fn = buscar
        print("Modo interactivo: línea base (politicas_chunks + MiniLM)")
    print("Escribe salir o exit para terminar")

    while True:
        p = input("\nPregunta: ").strip()
        if p.lower() in ("salir", "exit", ""):
            break
        resultados = fn(p)
        if not resultados:
            print("(sin resultados por encima del umbral)")
        for r in resultados:
            print(f"{r['similarity']:.3f} {r['content']}")


if __name__ == "__main__":
    main()
