"""Estrategias de chunking y función de evaluación (Hit@k, MRR)."""
import re


def normalizar(texto: str) -> str:
    """Colapsa saltos de línea y espacios múltiples en un solo espacio."""
    return re.sub(r"\s+", " ", texto).strip()


# 1) Por artículo (la de clase / línea base)
def dividir_chunks(texto: str):
    chunks = []
    capitulo_actual = None
    articulo_actual = None
    lineas_actuales: list[str] = []

    def cerrar_articulo():
        if articulo_actual and lineas_actuales:
            chunks.append({
                "capitulo": capitulo_actual,
                "articulo": articulo_actual,
                "content": f"{capitulo_actual}\n{articulo_actual}\n"
                           + "\n".join(lineas_actuales).strip()
            })

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


# 2) Por renglones: 4 renglones por chunk, sin solapamiento
def chunk_por_renglones(texto: str, renglones_por_chunk: int = 4):
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    return [normalizar(" ".join(lineas[i:i + renglones_por_chunk]))
            for i in range(0, len(lineas), renglones_por_chunk)]


# 3) Por palabras: ventana de 100, paso de 50 (solape de 50)
def chunk_por_palabras(texto: str, tam: int = 100, solape: int = 50):
    palabras = normalizar(texto).split()
    paso = tam - solape
    chunks = []
    for i in range(0, len(palabras), paso):
        chunks.append(" ".join(palabras[i:i + tam]))
        if i + tam >= len(palabras):
            break
    return chunks


def _como_dicts(lista):
    return [{"capitulo": None, "articulo": None, "content": c} for c in lista]


ESTRATEGIAS = {
    "articulo": lambda t: dividir_chunks(t),
    "renglones": lambda t: _como_dicts(chunk_por_renglones(t, 4)),
    "palabras": lambda t: _como_dicts(chunk_por_palabras(t, 100, 50)),
}


def evaluar(golden, buscar, k: int = 3):
    """Hit@k y MRR. Acierto si alguna evidencia recuperada contiene la frase."""
    preguntas = [g for g in golden if g["evidencia"]]
    hits, rr = 0, 0.0
    for g in preguntas:
        resultados = buscar(g["pregunta"], k)
        evidencia = normalizar(g["evidencia"])
        posiciones = [i for i, r in enumerate(resultados, 1)
                      if evidencia in normalizar(r["content"])]
        if posiciones:
            hits += 1
            rr += 1 / posiciones[0]
    n = len(preguntas)
    return {"hit@k": hits / n, "mrr": rr / n}
