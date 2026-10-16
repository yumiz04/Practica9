from dotenv import load_dotenv
from supabase import create_client

import os

load_dotenv()

ARCHIVO = "politicas_empresa.txt"
TABLA = "politicas_chunks"

supabase = create_client(
    # os.environ["SUPABASE_URL"],
    # os.environ["SUPABASE_KEY"]
    os.environ.get("SUPABASE_URL"), # Se puede dar un valor por defecto
    os.environ.get("SUPABASE_KEY")
)

modelo = SentenceTransformer("all-MiniLM-L6-v2")

# Crear los chunks
def dividir_chunks(texto: str):
    # Crear algunas variables
    chunks = []
    capitulo_actual = None
    articulo_actual = None
    lineas_actuales: list[str] = []

    def cerrar_articulo():
        if articulo_actual and lineas_actuales:
            chunks.append({
                "capitulo": capitulo_actual,
                "articulo": articulo_actual,
                "content": f"{capitulo_actual}\n{articulo_actual}\n" + "\n".join(lineas_actuales).strip()
            })

    # Leer linea a linea de las politicas
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith("CAPÍTULO"):
            cerrar_articulo()
            articulo_actual, lineas_actuales = None, []
            capitulo_actual = linea
        elif linea.startswith("Artículo"):
            cerrar_articulo()
            articulo_actual, lineas_actuales = linea, []
        elif articulo_actual:
            lineas_actuales.append(linea)

    cerrar_articulo()
    return chunks

def main():
    with open(ARCHIVO, encoding="UTF-8") as f:
        texto = f.read()

    chunks = dividir_chunks(texto)
    print(f"Fragmentos realizados: {len(chunks)}")

    # for e in chunks:
    #     print(e ['content'])

    # Generar los embeddings
    embeddings = modelo.encode([c['content'] for c in chunks])

    # Formar una lista de registros (mas rapido que de uno a uno)
    filas = [
        {
            "archivo": ARCHIVO,
            "capitulo": c['capitulo'],
            "articulo": c['articulo'],
            "content": c['content'],
            "embedding": emb.tolist()
        }
        for c,emb in zip(chunks, embeddings) # Zip sirve para agrupar iterables
    ]

    # Eliminar todos los registros de la base de datos
    supabase.table(TABLA).delete().eq("archivo", ARCHIVO).execute()

    # Agregar a la base de datos
    supabase.table(TABLA).insert(filas).execute()

    print(f"Se insertaron {len(filas)} registros en la base de datos")

if __name__ == '__main__':
    main()