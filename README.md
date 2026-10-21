# Practica 9 (Gemini)

## Preguntas de ejemplo
Mismas 20 preguntas que en la 'Practica 8'. Las preguntas están
disponibles en [yumiz04/Practica8](https://github.com/yumiz04/Practica8)

## Guía de instalación
Abrir una terminal (CMD o Git Bash) y navegar hasta la ruta deseada
```bash
cd Practicas
```

Clonar el repo
```bash
git clone https://github.com/yumiz04/Practica9.git
```

Entrar a la carpeta del proyecto
```bash
cd Practica9
```

Crear el entorno virtual de Python
```bash
python -m venv venv
```

Abrir VS Code
```bash
code .
```

Activar el entorno virtual (si no está activo)
```bash
.\venv\Scripts\activate
```

Instalar dependencias del proyecto
```bash
pip install supabase langchain-google-genai python-dotenv sentence-transformers
```

## Guía de uso
Ejecutar
```bash
python ingesta.py
```
Muestra la estrategia de chunking y el número de chunks.
Cronometra los tiempos en segundos.

```bash
python bench.py
```
Muestra una tabla comparativa de estrategias, modelos,
Hit@3, MRR, tiempo de ingesta y costo.

Se crean archivos locales con los tiempos de ingesta y
resultados para su análisis. Estos son proporcionados
por 'ingesta.py' -> 'tiempos_ingesta.json' y 'bench.py'
crea un CSV con los resultados generales -> 'resultados'