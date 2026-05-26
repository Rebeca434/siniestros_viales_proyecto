# ════════════════════════════════════════════════════════════════════════════
# Dockerfile — Sistema Distribuido de Análisis de Siniestros Viales
# Base: Python 3.11 slim
# ════════════════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# ── Dependencias del sistema ────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        procps \
    && rm -rf /var/lib/apt/lists/*

# ── Directorio de trabajo ───────────────────────────────────────────────────
WORKDIR /app

# ── Dependencias Python ─────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Código fuente ───────────────────────────────────────────────────────────
COPY src/ ./src/

# ── Directorios de datos y salidas ──────────────────────────────────────────
RUN mkdir -p data outputs

# ── Variables de entorno ────────────────────────────────────────────────────
ENV PYTHONPATH=/app/src \
    RAY_DISABLE_IMPORT_WARNING=1 \
    PYTHONUNBUFFERED=1

# ── Puerto por defecto (Streamlit) ──────────────────────────────────────────
EXPOSE 8501

# ── Comando por defecto ─────────────────────────────────────────────────────
CMD ["python", "src/main.py"]
