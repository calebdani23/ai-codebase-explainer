# MASTER PROMPT — AI Codebase Explainer & Issue Triage

Actúa como un agente senior de ingeniería de software, arquitectura full-stack, AI tooling, DevOps ligero, seguridad básica de análisis de código y diseño de producto.

Vas a construir un proyecto de portfolio profesional llamado:

AI Codebase Explainer & Issue Triage

El objetivo es crear una plataforma visual que permita analizar repositorios de software, explicar su arquitectura, detectar stack tecnológico, generar mapas del codebase, identificar riesgos técnicos y producir issues sugeridos con prioridad, severidad, archivos relacionados y recomendaciones accionables.

Este proyecto debe verse como una herramienta real para equipos de software que necesitan entender rápidamente un repositorio, auditar deuda técnica y convertir hallazgos en tickets accionables.

Este NO debe ser un simple “chat con archivos”. Debe presentarse como:

AI-powered engineering assistant for repository understanding, architecture review and issue triage.

---

## 1. Contexto general del proyecto

Estoy desarrollando este proyecto en un servidor remoto, dentro de un repositorio dedicado que se sincronizará con GitHub.

El proyecto debe poder exponerse así:

1. Frontend estático en GitHub Pages.
2. Backend/API en hosting remoto gratuito, preferentemente Render Free Web Service o Koyeb Free Web Service.
3. Base de datos gratuita externa, preferentemente Neon Postgres Free o Supabase Free.
4. El frontend nunca debe contener secretos.
5. El backend debe manejar llaves, conexión a base de datos, análisis de repositorios, llamadas AI y lógica privada mediante variables de entorno.
6. El proyecto debe poder correr localmente en mi servidor remoto usando Docker Compose o comandos simples.
7. El proyecto debe quedar muy bien documentado en README, con arquitectura, screenshots, comandos, variables de entorno, roadmap y demo script.
8. El MVP debe funcionar aunque no exista una API key real de OpenAI, usando análisis demo/determinístico y repositorios demo.

---

## 2. Relación con mi proyecto anterior

Ya existe un proyecto previo llamado:

AI Agent Observability Dashboard

URL pública:
https://calebdani23.github.io/ai-agent-observability-dashboard/

Repositorio:
https://github.com/calebdani23/ai-agent-observability-dashboard

Ese proyecto funciona como dashboard de observabilidad para AI agents, LLM calls, prompts, tool calls, tokens, costos, latencia, errores, sesiones y trazas completas.

Este nuevo proyecto debe conectarse opcionalmente con ese dashboard de observabilidad.

La historia de portfolio que quiero contar es:

“Primero construí una plataforma para observar agentes de AI. Luego construí un agente que analiza repositorios y lo instrumenté usando mi propia plataforma de observabilidad.”

Por lo tanto, este proyecto debe incluir integración opcional con el observability dashboard mediante variables de entorno.

---

## 3. Integración obligatoria con observabilidad

Implementa un módulo interno llamado:

packages/observability-client/

o, si la estructura del repo se simplifica:

apps/api/services/observability_client.py

Este cliente debe poder enviar trazas al backend del AI Agent Observability Dashboard usando el contrato de `POST /api/traces`.

Variables de entorno esperadas:

```env
OBSERVABILITY_ENABLED=true
OBSERVABILITY_API_URL=https://YOUR_OBSERVABILITY_BACKEND_URL
OBSERVABILITY_INGEST_API_KEY=replace-with-ingest-key
OBSERVABILITY_APP_NAME=ai-codebase-explainer

Si OBSERVABILITY_ENABLED=false o falta OBSERVABILITY_API_URL, el proyecto debe seguir funcionando sin fallar.

Cada análisis de repositorio debe crear una trace con operación:

analyze_repository
detect_stack
generate_architecture_summary
generate_issue_triage
ask_codebase

Cada trace debe incluir steps como:

user_message — solicitud original del usuario.
tool_call — fetch o clone del repositorio.
tool_call — scan de archivos.
retrieval — selección de chunks relevantes.
llm_call — resumen de arquitectura.
llm_call — generación de issues sugeridos.
final_response — resultado final entregado a la UI.
error — si alguna etapa falla.

Ejemplo conceptual de trace enviada:

{
  "app_name": "ai-codebase-explainer",
  "session_id": "analysis_123",
  "operation": "analyze_repository",
  "model": "gpt-4o-mini",
  "provider": "openai",
  "status": "success",
  "input_tokens": 2500,
  "output_tokens": 900,
  "metadata": {
    "repository_url": "https://github.com/example/repo",
    "files_analyzed": 120,
    "detected_stack": ["React", "FastAPI", "PostgreSQL"]
  },
  "steps": [
    {
      "step_type": "tool_call",
      "name": "scan_repository",
      "input": "Repository URL",
      "output": "120 files analyzed"
    },
    {
      "step_type": "llm_call",
      "name": "generate_issue_triage",
      "input": "Repository chunks and architecture summary",
      "output": "Generated 8 suggested issues"
    }
  ]
}

No debe bloquear el análisis si falla el envío de observabilidad. En caso de error, registrar warning en logs y continuar.

4. Repositorio esperado

Crea o adapta la estructura del repo de esta forma:

ai-codebase-explainer/
  apps/
    web/
    api/
  packages/
    shared/
    observability-client/
  examples/
    demo-repos/
  docs/
    architecture.md
    analysis-pipeline.md
    deployment.md
    demo-script.md
    issue-schema.md
    observability-integration.md
    roadmap.md
    screenshots/
  .github/
    workflows/
      deploy-pages.yml
  docker-compose.yml
  README.md
  .gitignore
  .env.example
  MASTER_PROMPT.md

Si esta estructura resulta demasiado pesada para un MVP inicial, puedes simplificarla, pero mantén separación clara entre:

frontend,
backend,
lógica de análisis,
cliente de observabilidad,
documentación,
ejemplos/demo.
5. Stack técnico recomendado

Frontend:

Vite
React
TypeScript
Tailwind CSS
shadcn/ui o componentes propios bien diseñados
React Router
TanStack Query
Recharts para métricas simples
Monaco Editor opcional para vista de archivos/chunks

Backend:

FastAPI
Python
Pydantic
SQLAlchemy o SQLModel
PostgreSQL
Uvicorn
CORS configurado para GitHub Pages y localhost

AI:

OpenAI API opcional
Structured JSON outputs cuando sea posible
Modo demo sin AI key
Embeddings opcionales para búsqueda semántica
Si pgvector no se implementa en el primer MVP, dejar arquitectura preparada para agregarlo después

Base de datos:

PostgreSQL compatible con Neon o Supabase
Evitar depender de filesystem local para persistencia en producción
El filesystem local puede usarse temporalmente para clonar repos durante un job, pero no como almacenamiento permanente

DevOps:

Docker Compose para desarrollo local
GitHub Actions para desplegar frontend en GitHub Pages
Instrucciones para deploy backend en Render o Koyeb
Variables de entorno separadas para frontend y backend

Importante:

No usar servicios pagados como requisito.
No hardcodear secretos.
No exponer tokens en frontend.
No depender de SQLite para producción en Render Free.
El proyecto debe funcionar con datos demo aunque no haya OpenAI API key configurada.
6. Objetivo funcional del MVP

Construir una aplicación que permita:

Ingresar una URL de repositorio público de GitHub.
Analizar un repositorio demo si no se quiere usar GitHub real.
Leer estructura de archivos.
Ignorar carpetas pesadas o irrelevantes.
Detectar stack tecnológico.
Generar resumen del proyecto.
Generar explicación de arquitectura.
Mostrar árbol de archivos.
Mostrar archivos o módulos importantes.
Generar issues sugeridos.
Asignar severidad, categoría, confianza y esfuerzo estimado a cada issue.
Permitir copiar/exportar issue en formato Markdown.
Permitir exportar análisis completo como Markdown o JSON.
Tener una pantalla de chat “Ask your codebase”.
Conectar opcionalmente cada análisis con el AI Agent Observability Dashboard.
Documentar todo como proyecto profesional de portfolio.
7. Alcance visual del frontend

Diseña una interfaz moderna, limpia y profesional.

Debe verse como una herramienta SaaS de ingeniería para equipos técnicos.

Debe tener estas pantallas:

7.1 Landing / Project Intro

Ruta sugerida:

/

Contenido:

Hero: “AI Codebase Explainer & Issue Triage”
Subtítulo: “Understand repositories, map architecture and generate actionable engineering issues with AI.”
Botones:
“Analyze Repository”
“Try Demo Repository”
“View GitHub”
Cards de valor:
Architecture summary
Stack detection
AI issue triage
Ask your codebase
Observability integrated

Debe incluir una sección que explique la conexión con el proyecto anterior:

“This project is instrumented with my AI Agent Observability Dashboard, so repository analysis runs can be monitored as traces with LLM calls, tool usage, latency, cost and errors.”

7.2 Repository Intake

Ruta sugerida:

/analyze

Formulario:

GitHub Repository URL
Branch opcional
Analysis mode:
Quick Scan
Deep Scan
Issue Triage Only
Demo Repository
Checkbox:
Send telemetry to observability dashboard
Botón:
Start Analysis

Validaciones:

Solo permitir URLs públicas de GitHub en MVP.
No pedir tokens de GitHub desde frontend.
Si hay GitHub token opcional, debe ir solo en backend.
Mostrar nota de seguridad: no analizar repos privados con secretos en este MVP.
7.3 Analysis Overview

Ruta sugerida:

/analysis/:id

Debe mostrar cards:

Repository name
Branch
Status
Files analyzed
Languages detected
Detected stack
Risk score
Suggested issues
Analysis duration
Observability trace status

Secciones:

Executive Summary
Architecture Summary
Detected Stack
Important Folders
Main Entry Points
Suggested Issues
Observability Trace Link o Trace ID si existe
7.4 Architecture Explorer

Puede ser sección dentro de /analysis/:id o ruta:

/analysis/:id/architecture

Debe mostrar:

Árbol de archivos y carpetas
Carpetas principales explicadas
Archivos críticos
Entry points
Dependencias detectadas
Notas de arquitectura

Ejemplo visual:

src/
  app/
  components/
  services/
  lib/
  api/

Al seleccionar una carpeta o archivo, mostrar:

función probable,
por qué es importante,
dependencias relacionadas,
riesgos detectados,
recomendaciones.
7.5 Issue Triage

Ruta sugerida:

/analysis/:id/issues

Tabla de issues:

Columnas:

Priority
Severity
Category
Title
Confidence
Effort
Related files
Status

Categorías:

bug
security
performance
refactor
testing
docs
architecture
maintainability

Cada issue debe tener detalle:

título,
descripción,
evidencia,
archivos relacionados,
razón del problema,
sugerencia de solución,
dificultad estimada,
markdown listo para copiar como GitHub Issue.

No crear issues reales en GitHub en el MVP. Solo generar texto listo para copiar.

7.6 Ask Your Codebase

Ruta sugerida:

/analysis/:id/chat

Chat contextual donde el usuario puede preguntar:

“Where is authentication handled?”
“What files would I modify to add payments?”
“What are the main risks in this repo?”
“Explain the backend architecture.”
“Which files are most important?”
“What tests should be added first?”

La respuesta debe incluir referencias a archivos relacionados cuando existan.

En MVP, puede funcionar con búsqueda simple por keywords/chunks y respuesta AI si hay API key. Si no hay API key, usar respuestas demo/determinísticas para el demo repo.

7.7 Observability Integration View

Ruta sugerida:

/analysis/:id/observability

Debe mostrar:

Si la integración está habilitada.
Trace ID generada.
Operaciones enviadas.
Estado del envío:
success
disabled
failed
Link manual al dashboard de observabilidad si existe.
Resumen de steps enviados.

Esto ayuda a contar la historia de portfolio.

8. Seguridad y límites de análisis de repositorios

Implementa reglas defensivas:

Ignorar carpetas:
.git
node_modules
dist
build
.next
.turbo
venv
.venv
__pycache__
.pytest_cache
.mypy_cache
coverage
.cache
vendor
Ignorar archivos grandes:
límite recomendado: 300 KB por archivo para MVP
configurable con MAX_FILE_SIZE_KB
Ignorar binarios:
imágenes,
videos,
fuentes,
zips,
ejecutables,
lockfiles demasiado grandes si aplica.
Extensiones permitidas para análisis:
.ts
.tsx
.js
.jsx
.py
.go
.java
.cs
.php
.rb
.rs
.md
.json
.yaml
.yml
.toml
.sql
.prisma
.env.example
Dockerfile
No guardar secretos detectados en prompts ni en traces.
Agregar redacción básica para patrones sensibles:
API keys
tokens
passwords
private keys
.env
Para archivos .env, solo permitir .env.example; ignorar .env real.
Prevenir Zip Slip si se implementa upload ZIP.
No ejecutar código del repositorio analizado.
No instalar dependencias del repositorio analizado.
El análisis debe ser estático.
9. Pipeline interno de análisis

El backend debe implementar un pipeline claro:

1. Recibir GitHub URL o seleccionar demo repo
2. Crear analysis job
3. Clonar o descargar repo en carpeta temporal
4. Validar tamaño y límites
5. Escanear árbol de archivos
6. Filtrar archivos analizables
7. Detectar lenguajes y stack
8. Extraer archivos críticos
9. Crear chunks de código/documentación
10. Redactar posibles secretos
11. Generar resumen determinístico base
12. Si hay AI key, generar resumen AI
13. Generar arquitectura
14. Generar issues sugeridos
15. Guardar resultados en Postgres
16. Enviar trace al Observability Dashboard si está habilitado
17. Devolver analysis_id para la UI

Cada etapa debe tener logs claros y manejo de errores.

10. Modelos de datos recomendados
RepositoryAnalysis
type RepositoryAnalysis = {
  id: string;
  repositoryUrl?: string;
  repositoryName: string;
  branch?: string;
  sourceType: "github" | "demo" | "zip";
  status: "pending" | "analyzing" | "completed" | "failed";
  analysisMode: "quick" | "deep" | "issue_triage_only";
  detectedStack: string[];
  languages: Record<string, number>;
  filesAnalyzed: number;
  totalFilesSeen: number;
  riskScore: "low" | "medium" | "high" | "critical";
  summary?: string;
  architectureSummary?: string;
  observabilityTraceId?: string;
  observabilityStatus?: "disabled" | "sent" | "failed";
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
};
CodeFile
type CodeFile = {
  id: string;
  analysisId: string;
  path: string;
  language: string;
  sizeBytes: number;
  isEntryPoint: boolean;
  isImportant: boolean;
  summary?: string;
};
CodeChunk
type CodeChunk = {
  id: string;
  analysisId: string;
  fileId: string;
  filePath: string;
  language: string;
  content: string;
  redactedContent: string;
  startLine: number;
  endLine: number;
  tokenEstimate?: number;
  embeddingId?: string;
};
SuggestedIssue
type SuggestedIssue = {
  id: string;
  analysisId: string;
  title: string;
  category:
    | "bug"
    | "security"
    | "performance"
    | "refactor"
    | "testing"
    | "docs"
    | "architecture"
    | "maintainability";
  severity: "low" | "medium" | "high" | "critical";
  priority: "p1" | "p2" | "p3" | "p4";
  confidence: number;
  effort: "small" | "medium" | "large";
  description: string;
  evidence: string;
  relatedFiles: string[];
  suggestedFix: string;
  githubIssueMarkdown: string;
  createdAt: string;
};
ChatMessage
type ChatMessage = {
  id: string;
  analysisId: string;
  role: "user" | "assistant" | "system";
  content: string;
  relatedFiles?: string[];
  createdAt: string;
};
11. Endpoints API requeridos
Health

GET /health

Respuesta:

{
  "status": "ok",
  "service": "ai-codebase-explainer-api"
}
Analyses

POST /api/analyses

Crea un nuevo análisis.

Body:

{
  "repository_url": "https://github.com/example/repo",
  "branch": "main",
  "analysis_mode": "quick",
  "send_observability": true
}

También permitir:

{
  "source_type": "demo",
  "demo_repo": "react-fastapi-saas",
  "analysis_mode": "quick",
  "send_observability": true
}

GET /api/analyses

Lista análisis previos.

Filtros:

status
repository_name
limit
offset

GET /api/analyses/{analysis_id}

Devuelve overview completo.

GET /api/analyses/{analysis_id}/files

Devuelve árbol y archivos importantes.

GET /api/analyses/{analysis_id}/issues

Devuelve issues sugeridos.

GET /api/analyses/{analysis_id}/export.md

Devuelve análisis en Markdown.

GET /api/analyses/{analysis_id}/export.json

Devuelve análisis en JSON.

Chat

POST /api/analyses/{analysis_id}/chat

Body:

{
  "message": "Where is authentication handled?"
}

Respuesta:

{
  "answer": "Authentication appears to be handled in...",
  "related_files": ["src/auth/session.ts", "src/api/login.ts"],
  "observability_status": "sent"
}
Demo

POST /api/demo/reset

Limpia y crea análisis demo.

POST /api/demo/analyze

Ejecuta análisis demo sin GitHub real.

GET /api/demo/repos

Lista repos demo disponibles.

Observability

GET /api/analyses/{analysis_id}/observability

Devuelve:

{
  "enabled": true,
  "status": "sent",
  "trace_id": "trace_123",
  "app_name": "ai-codebase-explainer",
  "operations": [
    "scan_repository",
    "detect_stack",
    "generate_issue_triage"
  ],
  "dashboard_url": "https://calebdani23.github.io/ai-agent-observability-dashboard/"
}
12. AI y modo demo

El proyecto debe tener dos modos:

Modo real AI

Activo si existe:

OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini

En este modo:

generar resumen con AI,
generar arquitectura con AI,
generar issues con AI,
responder chat con AI,
enviar telemetría con tokens/costo estimado si es posible.
Modo demo/determinístico

Si no hay OPENAI_API_KEY, el proyecto debe seguir funcionando con:

repos demo,
análisis heurístico,
issues demo realistas,
respuestas predefinidas o basadas en keywords,
UI completa.

Importante:

La UI debe mostrar un badge claro:
“Demo mode”
“AI mode”
No ocultar si se están usando datos demo.
13. Structured outputs para issues

Cuando uses AI para generar issues, intenta que la respuesta sea JSON estructurado.

Formato esperado:

{
  "issues": [
    {
      "title": "Missing input validation in API route",
      "category": "security",
      "severity": "high",
      "priority": "p1",
      "confidence": 0.86,
      "effort": "medium",
      "description": "The API route accepts user input without schema validation.",
      "evidence": "Request body is passed directly into service layer.",
      "relatedFiles": ["apps/api/routes/users.py"],
      "suggestedFix": "Add Pydantic validation and reject malformed input.",
      "githubIssueMarkdown": "## Problem\n..."
    }
  ]
}

Validar y sanear la salida antes de guardarla.

Si la AI devuelve JSON inválido, usar fallback.

14. Detección de stack

Implementa detección heurística por archivos:

Frontend:

package.json
vite.config.ts
next.config.js
src/main.tsx
app/page.tsx
tailwind.config.*

Backend:

requirements.txt
pyproject.toml
main.py
app.py
manage.py
package.json
server.ts

DB/ORM:

prisma/schema.prisma
alembic
drizzle.config.ts
typeorm
sqlalchemy
.sql

Infra:

Dockerfile
docker-compose.yml
.github/workflows
render.yaml
fly.toml
vercel.json

Testing:

pytest.ini
vitest.config.ts
jest.config.js
playwright.config.ts
15. Issue generation heuristics

Aunque no haya AI key, generar issues útiles con reglas básicas:

No README o README pobre → docs issue.
No .env.example → setup/docs issue.
No tests detectados → testing issue.
API sin validación aparente → security/bug issue.
Archivos muy grandes → maintainability issue.
Duplicación simple de nombres o patrones → refactor issue.
Falta de Dockerfile/deploy docs → devops/docs issue.
Dependencias sin lockfile → reliability issue.
No GitHub Actions → CI issue.
Uso de .env real detectado → critical security issue, pero no guardar contenido.
16. GitHub Pages

Configura el frontend para publicarse en GitHub Pages.

Requisitos:

Usar Vite.
Configurar base correctamente para repo pages.
Si el repo se llama ai-codebase-explainer, usar:
/ai-codebase-explainer/
Usar hash routing o configuración compatible para evitar 404 en rutas directas.
Crear workflow:
.github/workflows/deploy-pages.yml
El workflow debe:
instalar dependencias,
construir apps/web,
publicar el build en GitHub Pages.
Documentar en docs/deployment.md cómo activar GitHub Pages en Settings > Pages > GitHub Actions.
17. Backend deploy gratuito

Preparar backend para Render Free Web Service y opcionalmente Koyeb.

Documentación para Render:

Root directory: apps/api
Runtime: Python
Build command:
pip install -r requirements.txt
Start command:
uvicorn main:app --host 0.0.0.0 --port $PORT
Environment variables:
DATABASE_URL
CORS_ORIGINS
OPENAI_API_KEY opcional
OPENAI_MODEL
GITHUB_TOKEN opcional
OBSERVABILITY_ENABLED
OBSERVABILITY_API_URL
OBSERVABILITY_INGEST_API_KEY
DEMO_MODE

El backend debe usar el puerto entregado por variable de entorno PORT.

No guardar datos importantes en filesystem local.

18. Variables de entorno

Crear .env.example.

Backend:

DATABASE_URL=postgresql://user:password@host:5432/dbname
CORS_ORIGINS=http://localhost:5173,https://YOUR_GITHUB_USERNAME.github.io
ENVIRONMENT=development
DEMO_MODE=true

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

GITHUB_TOKEN=

MAX_REPO_SIZE_MB=25
MAX_FILE_SIZE_KB=300
MAX_FILES_ANALYZED=300

OBSERVABILITY_ENABLED=false
OBSERVABILITY_API_URL=https://YOUR_OBSERVABILITY_BACKEND_URL
OBSERVABILITY_INGEST_API_KEY=
OBSERVABILITY_APP_NAME=ai-codebase-explainer

PORT=8000

Frontend:

VITE_API_URL=http://localhost:8000
VITE_DEMO_MODE=true
VITE_REPO_URL=https://github.com/YOUR_USERNAME/ai-codebase-explainer
VITE_OBSERVABILITY_DASHBOARD_URL=https://calebdani23.github.io/ai-agent-observability-dashboard/

Nunca crear .env con secretos reales.

19. Calidad visual

El diseño debe lucir como producto SaaS moderno para ingeniería:

layout limpio,
sidebar o top nav,
cards con métricas,
árbol de archivos legible,
tabla de issues clara,
badges para severity,
badges para status,
timeline de análisis,
estados vacíos bien diseñados,
modo demo indicado,
diseño responsive básico,
buen spacing,
buen contraste,
estilo technical dashboard.

Debe verse como herramienta profesional de AI engineering, no como práctica escolar.

20. Documentación obligatoria

Crear o actualizar:

README.md

Debe incluir:

Nombre del proyecto.
Descripción corta.
Problema que resuelve.
Features.
Relación con AI Agent Observability Dashboard.
Tech stack.
Arquitectura.
Screenshots o placeholders.
Cómo correr localmente.
Variables de entorno.
Cómo analizar demo repo.
Cómo analizar repo público de GitHub.
Cómo desplegar frontend en GitHub Pages.
Cómo desplegar backend en Render/Koyeb.
Cómo conectar con observability dashboard.
Roadmap.
Engineering decisions.
docs/architecture.md

Debe explicar:

frontend,
backend,
database,
analysis pipeline,
observability integration,
deployment flow.
docs/analysis-pipeline.md

Debe explicar:

clone/fetch,
scan,
filter,
stack detection,
chunking,
redaction,
AI summary,
issue triage,
export,
telemetry.
docs/issue-schema.md

Debe definir:

SuggestedIssue,
severity,
priority,
confidence,
effort,
categories,
markdown export.
docs/observability-integration.md

Debe explicar:

cómo este proyecto se conecta al dashboard anterior,
variables necesarias,
qué operaciones se envían,
cómo se estructura una trace,
cómo desactivar la integración,
cómo manejar errores.
docs/deployment.md

Debe explicar:

GitHub Pages,
Render,
Koyeb,
Neon/Supabase,
CORS,
variables de entorno,
troubleshooting.
docs/demo-script.md

Debe explicar cómo presentar el proyecto:

Abrir landing.
Analizar demo repo.
Mostrar overview.
Mostrar architecture explorer.
Mostrar issue triage.
Copiar un issue como Markdown.
Hacer una pregunta en Ask your codebase.
Abrir observability view.
Explicar que el análisis está instrumentado con tu propio dashboard de observabilidad.
21. Fases de implementación

Trabaja por fases. No implementes todo de forma desordenada.

Fase 1 — Setup base

Objetivo:

Crear estructura del repo.
Configurar frontend Vite React TypeScript.
Configurar backend FastAPI.
Configurar Docker Compose.
Crear health check.
Configurar CORS.
Crear README inicial.
Crear .env.example.

Criterio de aceptación:

Frontend corre localmente.
Backend responde /health.
README tiene comandos básicos.
No hay secretos.
Estructura lista para GitHub Pages y backend remoto.
Fase 2 — Backend data models y demo analysis

Objetivo:

Crear modelos de datos.
Conectar a Postgres.
Crear endpoints base de analyses.
Crear demo repo analysis sin GitHub real.
Guardar resultados en DB.
Crear endpoint /api/demo/analyze.

Criterio de aceptación:

Se puede crear un análisis demo.
Se puede listar análisis.
Se puede abrir análisis por ID.
Se pueden ver summary, stack, files e issues demo.
Fase 3 — Repository scanner

Objetivo:

Implementar análisis de repos públicos de GitHub.
Clonar o descargar repo.
Escanear archivos.
Aplicar filtros.
Detectar stack.
Crear chunks.
Redactar secretos básicos.
Guardar files/chunks.

Criterio de aceptación:

Se puede analizar un repo público pequeño.
Se respetan límites.
No se ejecuta código del repo.
Se ignoran carpetas pesadas.
Se detecta stack de forma razonable.
Fase 4 — Issue triage

Objetivo:

Generar issues heurísticos sin AI key.
Generar issues con AI si OPENAI_API_KEY existe.
Validar JSON estructurado.
Crear markdown listo para GitHub Issue.
Crear export JSON/Markdown.

Criterio de aceptación:

Cada análisis produce issues.
Cada issue tiene severidad, categoría, prioridad, confianza, esfuerzo y archivos relacionados.
Se puede copiar/exportar issue.
Fase 5 — Frontend product UI

Objetivo:

Crear landing.
Crear repository intake.
Crear analysis overview.
Crear architecture explorer.
Crear issue triage.
Crear ask your codebase.
Crear observability integration view.
Conectar con API.
Agregar fallback demo.

Criterio de aceptación:

UI navegable.
Demo repo funciona desde frontend.
Tabla de issues visible.
Árbol de archivos visible.
Overview se ve profesional.
Modo demo/AI indicado.
Fase 6 — Ask your codebase

Objetivo:

Implementar chat por analysis ID.
Buscar chunks relevantes.
Responder con AI si hay key.
Responder con fallback demo si no hay key.
Incluir related files.
Enviar trace de chat a observability si está habilitado.

Criterio de aceptación:

Usuario puede preguntar sobre un análisis.
Respuesta menciona archivos relacionados.
No falla sin AI key.
Fase 7 — Observability integration

Objetivo:

Implementar cliente de observabilidad.
Enviar traces para análisis.
Enviar traces para issue triage.
Enviar traces para chat.
Mostrar estado en UI.
Documentar integración.

Criterio de aceptación:

Si OBSERVABILITY_ENABLED=true, se intenta enviar trace.
Si falla, la app sigue funcionando.
UI muestra status.
Docs explican cómo conectar con el dashboard anterior.
Fase 8 — Deployment

Objetivo:

Configurar GitHub Pages.
Configurar workflow.
Preparar backend para Render/Koyeb.
Preparar variables para Neon/Supabase.
Documentar CORS.
Probar build frontend.
Probar start command backend.

Criterio de aceptación:

npm run build funciona.
GitHub Actions queda preparado.
Backend usa $PORT.
Docs de deploy están claras.
Fase 9 — Polish portfolio

Objetivo:

Mejorar UI.
Agregar screenshots o placeholders.
Agregar demo script.
Agregar roadmap.
Agregar architecture diagram en Markdown.
Pulir README para reclutador/cliente.
Asegurar que la historia con el dashboard de observabilidad esté clara.

Criterio de aceptación:

El repo se entiende en menos de 2 minutos.
La landing vende el proyecto.
El dashboard parece producto real.
La documentación demuestra criterio de ingeniería.
El proyecto se conecta conceptualmente y técnicamente con AI Agent Observability Dashboard.
22. Reglas importantes
No hardcodear secretos.
No usar pagos como requisito.
No romper compatibilidad con GitHub Pages.
No depender de filesystem local para persistencia.
No ejecutar código de repos analizados.
No instalar dependencias de repos analizados.
No guardar secretos detectados.
No exponer OPENAI_API_KEY, GITHUB_TOKEN ni OBSERVABILITY_INGEST_API_KEY en frontend.
No crear issues reales en GitHub en el MVP.
No implementar auth compleja en MVP salvo que sea estrictamente necesario.
No presentar costos como facturación exacta.
No ocultar cuando se usa modo demo.
No hacer commits automáticamente salvo que se indique explícitamente.
No borrar archivos existentes sin revisar.
Mantener el proyecto enfocado y presentable.
23. Criterios finales de éxito

El proyecto estará completo cuando:

Exista frontend visual profesional.
Exista backend funcional.
Exista análisis demo.
Exista análisis de repos públicos pequeños.
Exista detección de stack.
Exista architecture summary.
Exista issue triage.
Exista export Markdown/JSON.
Exista Ask your codebase.
Exista integración opcional con AI Agent Observability Dashboard.
Exista documentación completa.
Exista workflow de GitHub Pages.
Existan instrucciones para backend gratuito.
El proyecto pueda presentarse como una herramienta real de AI engineering.
24. Primer paso que debes ejecutar

Antes de escribir código, inspecciona el estado actual del directorio y confirma:

ruta actual,
si ya existe package.json,
si ya existe git repo,
rama actual,
remote actual de GitHub si existe,
estructura actual de archivos,
si existe MASTER_PROMPT.md.

Después:

Resume brevemente el plan de ejecución para la Fase 1.
Ejecuta la Fase 1.
No hagas commits automáticamente.
Al terminar, reporta:
qué archivos creaste,
cómo correr frontend,
cómo correr backend,
cómo probar /health,
qué falta para la siguiente fase.

Empieza ahora con la inspección inicial del repositorio y luego ejecuta la Fase 1.