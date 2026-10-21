"""Banco de pruebas: línea base + 3 chunkings x modelos disponibles.

Imprime la tabla comparativa de la parte 5 y la guarda en resultados.csv.
Requiere haber corrido ingesta.py (para los tiempos de ingesta).
"""
import csv
import json
import os

from buscar import buscar, crear_buscar
from chunking import ESTRATEGIAS, evaluar
from modelos import MODELOS, disponibles

ARCHIVO_TIEMPOS = "tiempos_ingesta.json"
COSTO = {"local": "0 (local)", "api": "API de pago/cuota"}

# Marca para preguntas cuya evidencia aún no has buscado en politicas_empresa.txt.
# Se excluyen de la evaluación (y se avisa) para que no cuenten como fallo.
PENDIENTE = "PENDIENTE"

# Regla: la evidencia (3 a 6 palabras ideal) debe aparecer LITERALMENTE en
# politicas_empresa.txt. Las que dicen "del PDF" vienen del ejemplo del
# documento de la práctica: verifícalas contra tu archivo.
# evidencia = None  -> la pregunta NO tiene respuesta en el documento.
GOLDEN = [
    # --- Preguntas originales ---
    {"pregunta": "¿Cuántos días de vacaciones me tocan después de 3 años?",
     "evidencia": "Cada año adicional suma 2 días"},                      # del PDF
    {"pregunta": "¿Cuándo me pagan el aguinaldo?",
     "evidencia": "a más tardar el 20 de diciembre"},                     # del PDF
    {"pregunta": "¿Puedo trabajar desde mi casa?",
     "evidencia": "trabajar desde casa hasta 2 días por semana"},         # del PDF
    {"pregunta": "Se murió mi tío, ¿me dan permiso?",
     "evidencia": "fallecimiento del cónyuge, padres, hijos o hermanos"}, # del PDF
    {"pregunta": "¿Cuál es el código de vestimenta?",
     "evidencia": None},                                                  # sin respuesta
    {"pregunta": "¿Cuántos minutos tengo para llegar tarde?",
     "evidencia": PENDIENTE},
    {"pregunta": "Falleció un familiar, ¿Qué puedo hacer?",
     "evidencia": "fallecimiento del cónyuge, padres, hijos o hermanos"}, # del PDF
    {"pregunta": "Llegué tarde varias veces, ¿qué pasa?",
     "evidencia": "Tres retardos en un mismo mes"},                       # del PDF

    # --- Preguntas nuevas (paráfrasis) ---
    {"pregunta": "¿Cuando se realiza el depósito de la gratificación anual de fin de año?",
     "evidencia": "a más tardar el 20 de diciembre"},                     # del PDF
    {"pregunta": "En caso del fallecimiento de un familiar, ¿cuántos días de permiso con goce tengo?",
     "evidencia": "fallecimiento del cónyuge, padres, hijos o hermanos"}, # del PDF
    {"pregunta": "¿Tengo la posibilidad de trabajar a distancia desde mi hogar?",
     "evidencia": "trabajar desde casa hasta 2 días por semana"},         # del PDF
    {"pregunta": "Si acumulo retrasos de forma constante, ¿cuáles son las consecuencias?",
     "evidencia": "Tres retardos en un mismo mes"},                       # del PDF
    {"pregunta": "¿Cómo se retribuye económicamente si presto mis servicios durante un día festivo?",
     "evidencia": "tres veces su salario diario"},                        # del PDF
    {"pregunta": "¿Es factible monetizar los días de vacaciones en lugar de disfrutarlos físicamente?",
     "evidencia": "No se pueden vender ni cambiar por dinero"},           # del PDF
    {"pregunta": "¿Cuál es el código de vestimenta para asistir de forma presencial a las oficinas?",
     "evidencia": None},                                                  # sin respuesta (según el PDF)
    {"pregunta": "¿Cuál es el margen de tolerancia permitido al llegar al corporativo?",
     "evidencia": PENDIENTE},
    {"pregunta": "Si muere un pariente cercano, ¿cuál es el procedimiento y plazo para notificarlo?",
     "evidencia": PENDIENTE},
    {"pregunta": "¿Cuántos días libres con goce de salario corresponden por contraer nupcias?",
     "evidencia": PENDIENTE},
    {"pregunta": "¿Cuál es el monto mensual que otorga la empresa para cubrir gastos en esquema remoto?",
     "evidencia": PENDIENTE},
    {"pregunta": "¿Existe alguna restricción sobre el uso de smartphones durante las horas laborales?",
     "evidencia": PENDIENTE},
]



def similitud_top1(b, preguntas):
    """Similitud del primer resultado de cada pregunta (nan si no hay)."""
    out = []
    for p in preguntas:
        r = b(p, 1)
        out.append(r[0]["similarity"] if r else float("nan"))
    return out


def main():
    pendientes = [g for g in GOLDEN if g["evidencia"] == PENDIENTE]
    golden = [g for g in GOLDEN if g["evidencia"] != PENDIENTE]

    con_resp = [g["pregunta"] for g in golden if g["evidencia"]]
    sin_resp = [g["pregunta"] for g in golden if not g["evidencia"]]

    print(f"Preguntas totales: {len(GOLDEN)} | evaluadas con respuesta: {len(con_resp)} | "
          f"sin respuesta: {len(sin_resp)} | PENDIENTES (excluidas): {len(pendientes)}")
    if pendientes:
        print("  Completa la evidencia de:")
        for g in pendientes:
            print(f"   - {g['pregunta']}")
    print()

    tiempos = {}
    if os.path.exists(ARCHIVO_TIEMPOS):
        with open(ARCHIVO_TIEMPOS, encoding="UTF-8") as f:
            tiempos = json.load(f)
    else:
        print(f"(no hay {ARCHIVO_TIEMPOS}: corre ingesta.py para ver tiempos)\n")

    # Parte 1: línea base con tu tabla de clase y tu buscar original
    base = evaluar(golden, buscar, k=3)
    print(f"LÍNEA BASE  Hit@3={base['hit@k']:.2f}  MRR={base['mrr']:.2f}\n")

    # Partes 2, 3 y 5
    filas = []
    for estrategia in ESTRATEGIAS:
        for clave in disponibles():
            b = crear_buscar(estrategia, clave)
            m = evaluar(golden, b, k=3)
            s_con = similitud_top1(b, con_resp)
            s_sin = similitud_top1(b, sin_resp) if sin_resp else [float("nan")]
            min_con, max_sin = min(s_con), max(s_sin)
            separa = max_sin == max_sin and min_con > max_sin  # nan-safe
            filas.append({
                "estrategia": estrategia,
                "modelo": clave,
                "dims": MODELOS[clave]["dims"],
                "hit@3": round(m["hit@k"], 3),
                "mrr": round(m["mrr"], 3),
                "ingesta_s": round(tiempos[f"{estrategia}|{clave}"], 2)
                             if f"{estrategia}|{clave}" in tiempos else "",
                "costo": COSTO[MODELOS[clave]["tipo"]],
                "sim_min_con": round(min_con, 3),
                "sim_max_sin": round(max_sin, 3),
                "umbral_sugerido": round((min_con + max_sin) / 2, 3) if separa else "",
            })

    enc = (f"{'estrategia':10s} {'modelo':7s} {'dims':>5s} {'Hit@3':>6s} {'MRR':>6s} "
           f"{'ingesta s':>9s} {'sim min(con)':>13s} {'sim max(sin)':>13s} "
           f"{'umbral sug.':>11s}  costo")
    print(enc)
    print("-" * len(enc))
    for f in filas:
        print(f"{f['estrategia']:10s} {f['modelo']:7s} {f['dims']:5d} "
              f"{f['hit@3']:6.2f} {f['mrr']:6.2f} {str(f['ingesta_s']):>9s} "
              f"{f['sim_min_con']:13.3f} {f['sim_max_sin']:13.3f} "
              f"{str(f['umbral_sugerido']):>11s}  {f['costo']}")

    with open("resultados.csv", "w", newline="", encoding="UTF-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print("\nResultados guardados en resultados.csv")
    print("Recuerda: una diferencia de una sola pregunta es ruido, no conclusión.")


if __name__ == "__main__":
    main()
