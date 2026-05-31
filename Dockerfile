FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
  && rm -rf /var/lib/apt/lists/*

COPY dashboard/ ./dashboard/
COPY dados_caged_abri.csv dados_caged_diferencas.csv ./

RUN python3 dashboard/prepare_data.py

ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "export HOST=${HOST:-0.0.0.0}; export PORT=${PORT:-8000}; exec python3 dashboard/server.py"]
