from dotenv import load_dotenv
from supabase import create_client
from langchain_google_genai import GoogleGenerativeAIEmbeddings

import os
import time

load_dotenv()

ARCHIVO = "politicas_empresa.txt"
TABLA = "politicas_chunks"
TASK_TYPE_INDEX = "RETRIEVAL_DOCUMENT" # Recuperación de datos
DIMS = 3072

supabase = create_client(
    # os.environ["SUPABASE_URL"],
    # os.environ["SUPABASE_KEY"]
    os.environ.get("SUPABASE_URL"), # Se puede dar un valor por defecto
    os.environ.get("SUPABASE_KEY")
)

modelo = GoogleGenerativeAIEmbeddings(
    model = "models/gemini-embedding-001",
    task_type = TASK_TYPE_INDEX
    # En automático toma la API KEY de Gemini
)

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

# Cuidar el dinero, vectorizar de cierta cantidad en cierta cantidad
# Función para codificar vectores de 20 en 20
def embed_en_lotes(texto:str, tam_lote:int = 20):
    todos = []
    for i in range(0, len(texto), tam_lote):
        lote = texto[i: i + tam_lote]
        embeddings_lote = modelo.embed_documents(lote) # En lugar de encode
        todos.extend(embeddings_lote)
        if i+tam_lote < len(texto):
            time.sleep(0.5)
    return todos

def main():
    with open(ARCHIVO, encoding="UTF-8") as f:
        texto = f.read()

    chunks = dividir_chunks(texto)
    print(f"Fragmentos realizados: {len(chunks)}")

    # for e in chunks:
    #     print(e ['content'])

    # Generar los embeddings
    embeddings = embed_en_lotes(chunks) # SE VA A REVISAR

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