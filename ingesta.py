"""Ingesta: 3 estrategias de chunking x modelos disponibles + tiempos."""
import json
import os
import time

from dotenv import load_dotenv
from supabase import create_client

from chunking import ESTRATEGIAS
from modelos import MODELOS, disponibles, embed_documentos

load_dotenv()

ARCHIVO = "politicas_empresa.txt"
TABLA = "politicas_bench"
ARCHIVO_TIEMPOS = "tiempos_ingesta.json"
LOTE_INSERT = 20  # los vectores de Gemini (3072) pesan; lotes chicos

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def main():
    with open(ARCHIVO, encoding="UTF-8") as f:
        texto = f.read()

    activos = disponibles()
    omitidos = [k for k in MODELOS if k not in activos]
    print("Modelos a usar:", ", ".join(activos))
    if omitidos:
        print("Omitidos (falta API key):", ", ".join(omitidos))

    tiempos = {}

    for estrategia, fn in ESTRATEGIAS.items():
        chunks = fn(texto)
        print(f"\n[{estrategia}] {len(chunks)} chunks")

        filas = [{"archivo": ARCHIVO, "estrategia": estrategia,
                  "capitulo": c["capitulo"], "articulo": c["articulo"],
                  "content": c["content"]} for c in chunks]

        for clave in activos:
            cfg = MODELOS[clave]
            t0 = time.perf_counter()
            embs = embed_documentos(clave, [c["content"] for c in chunks])
            tiempos[f"{estrategia}|{clave}"] = time.perf_counter() - t0

            assert len(embs[0]) == cfg["dims"], (
                f"{clave}: el modelo devolvió {len(embs[0])} dims y la columna "
                f"espera {cfg['dims']}")
            for fila, emb in zip(filas, embs):
                fila[cfg["columna"]] = emb
            print(f"   {clave:7s} listo en {tiempos[f'{estrategia}|{clave}']:.2f} s")

        (supabase.table(TABLA).delete()
            .eq("archivo", ARCHIVO).eq("estrategia", estrategia).execute())
        for i in range(0, len(filas), LOTE_INSERT):
            supabase.table(TABLA).insert(filas[i:i + LOTE_INSERT]).execute()

    with open(ARCHIVO_TIEMPOS, "w", encoding="UTF-8") as f:
        json.dump(tiempos, f, indent=2)

    print("\nTiempo de embeddings (s):")
    for llave, t in tiempos.items():
        est, mod = llave.split("|")
        print(f"  {est:10s} {mod:7s} {t:7.2f}")
    print(f"\nTiempos guardados en {ARCHIVO_TIEMPOS} (los usa bench.py)")
    print("Nota: el tiempo de Gemini incluye red y pausas entre lotes.")


if __name__ == "__main__":
    main()
