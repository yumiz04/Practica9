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
> [!WARNING]
> Necesitará la tabla 'politicas_bench' y algunas funciones.
> Ejecute primero el script sql disponible en la sección [Recursos adicionales](#recursos-adicionales)
> en el editor sql de supabase antes de continuar.

> [!WARNING]
> Asegúrese de tener una buena velocidad de conexión a Internet,
> ya que se descargarán algunos modelos la primera vez que
> ejecute las pruebas.

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

## Recursos adicionales
### Script SQL para supabase
Ejecutar en el SQL Editor de Supabase, es seguro ejecutarlo varias veces
```markdown
create extension if not exists vector;

create table if not exists politicas_bench (
  id bigserial primary key,
  archivo text,
  estrategia text,          -- 'articulo' | 'renglones' | 'palabras'
  capitulo text,
  articulo text,
  content text,
  emb_minilm vector(384),   -- all-MiniLM-L6-v2
  emb_bge vector(1024),     -- BAAI/bge-m3
  emb_gemini vector(3072)   -- gemini-embedding-001
);

-- Por si la tabla ya existía de antes sin la columna de Gemini
alter table politicas_bench add column if not exists emb_gemini vector(3072);

-- Nota: no se crea índice vectorial en emb_gemini (HNSW/IVFFlat soportan
-- hasta 2000 dimensiones). Con tan pocos chunks la búsqueda exacta es instantánea.

create or replace function buscar_minilm(
  query_embedding vector(384), estrategia_f text, match_count int)
returns table (id bigint, content text, articulo text, similarity float)
language sql stable as $$
  select id, content, articulo, 1 - (emb_minilm <=> query_embedding) as similarity
  from politicas_bench
  where estrategia = estrategia_f and emb_minilm is not null
  order by emb_minilm <=> query_embedding
  limit match_count;
$$;

create or replace function buscar_bge(
  query_embedding vector(1024), estrategia_f text, match_count int)
returns table (id bigint, content text, articulo text, similarity float)
language sql stable as $$
  select id, content, articulo, 1 - (emb_bge <=> query_embedding) as similarity
  from politicas_bench
  where estrategia = estrategia_f and emb_bge is not null
  order by emb_bge <=> query_embedding
  limit match_count;
$$;

create or replace function buscar_gemini(
  query_embedding vector(3072), estrategia_f text, match_count int)
returns table (id bigint, content text, articulo text, similarity float)
language sql stable as $$
  select id, content, articulo, 1 - (emb_gemini <=> query_embedding) as similarity
  from politicas_bench
  where estrategia = estrategia_f and emb_gemini is not null
  order by emb_gemini <=> query_embedding
  limit match_count;
$$;

notify pgrst, 'reload schema';
```