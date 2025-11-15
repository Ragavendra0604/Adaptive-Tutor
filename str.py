from pathlib import Path

project_root = Path("Adaptive_Tutor")

files_to_create = [
    "backend/app/main.py",
    "backend/app/api/v1/query.py",
    "backend/app/api/v1/ingest.py",
    "backend/app/api/v1/admin.py",
    "backend/app/core/config.py",
    "backend/app/core/logger.py",
    "backend/app/db/mongo.py",
    "backend/app/db/schemas.py",
    "backend/app/embeddings/embedder.py",
    "backend/app/ingest/chunker.py",
    "backend/app/ingest/ingester.py",
    "backend/app/retriever/faiss_index.py",
    "backend/app/retriever/retriever.py",
    "backend/app/rag/prompt_templates.py",
    "backend/app/rag/rag_engine.py",
    "backend/app/scraper/fetcher.py",
    "backend/app/scraper/parsers.py",
    "backend/app/assessment/generator.py",
    "backend/app/assessment/evaluator.py",
    "backend/app/tasks/scheduler.py",
    "backend/requirements.txt",
    "backend/Dockerfile",
    "infra/docker-compose.yml",
    "infra/mongo-init/init-script.js",
    "docs/architecture.md",
    "scripts/seed_knowledge.py",
    "scripts/rebuild_index.py"
]

print("Creating project structure for 'adaptive-tutor'...")

for file_path in files_to_create:
    file = project_root / file_path

    file.parent.mkdir(parents=True, exist_ok=True)

    file.touch()

print("Project structure created successfully!")