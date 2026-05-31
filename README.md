# CAGED CE — Dashboard de Emprego Formal no Ceará

Dashboard interativo com dados do Novo CAGED (MTE) para acompanhar estoque, admissões, desligamentos e saldo líquido dos municípios cearenses.

## Estrutura

- `dashboard/` — frontend (HTML/CSS/JS) + servidor Python + preparação dos dados
- `dados_caged_abri.csv` — fonte principal (formato longo)
- `dados_caged_diferencas.csv` — comparação mar vs abri (ajuste cadastral)
- `converter_caged.py` / `comparar_caged.py` — utilitários de conversão e diff

## Uso local

```bat
dashboard\iniciar_dashboard.bat
```

Ou manualmente:

```bash
python dashboard/prepare_data.py
python dashboard/server.py
```

Acesse `http://127.0.0.1:8765`.

## Deploy no Railway

1. Conecte o repositório [pauloqxm/caged-ce](https://github.com/pauloqxm/caged-ce) ao Railway.
2. O Railway detecta o `Dockerfile` automaticamente.
3. A variável `PORT` é injetada pelo Railway; o servidor escuta em `0.0.0.0`.

Build local (opcional):

```bash
docker build -t caged-ce .
docker run -p 8000:8000 caged-ce
```

## Fonte dos dados

Ministério do Trabalho e Emprego — Novo CAGED, agregado por município (Ceará).
