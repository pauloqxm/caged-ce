#!/usr/bin/env python3
"""
Converte novo_caged.csv (formato largo) para o formato longo de dados_caged.csv.

Entrada:  novo_caged.csv  — municípios nas linhas, meses nas colunas
Saída:     novo_caged_formatado.csv — uma linha por município/mês
"""

import csv
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ARQUIVO_ENTRADA = SCRIPT_DIR / "novo_caged.csv"
ARQUIVO_SAIDA = SCRIPT_DIR / "novo_caged_formatado.csv"

MESES = {
    "Janeiro": "01",
    "Fevereiro": "02",
    "Março": "03",
    "Marco": "03",
    "Abril": "04",
    "Maio": "05",
    "Junho": "06",
    "Julho": "07",
    "Agosto": "08",
    "Setembro": "09",
    "Outubro": "10",
    "Novembro": "11",
    "Dezembro": "12",
}

CAMPOS_METRICAS = ["Estoque", "Admissões", "Desligamentos", "Saldos", "Variação Relativa (%)"]

CABECALHO_SAIDA = [
    "\nCódigo do Município",
    "\nMunicípio",
    "Mês/ano",
    "Estoque",
    "Admissões",
    "Desligamentos",
    "Saldos",
    "Variação Relativa (%)",
]


def normalizar_nome_coluna(nome: str) -> str:
    return nome.strip().replace("\n", "").replace("\ufeff", "")


def mes_ano_para_mm_yyyy(mes_ano: str) -> str:
    """Converte 'Janeiro/2020' para '01/2020'."""
    mes_nome, ano = mes_ano.split("/", 1)
    numero = MESES.get(mes_nome.strip())
    if not numero:
        raise ValueError(f"Mês não reconhecido: {mes_ano!r}")
    return f"{numero}/{ano.strip()}"


def limpar_municipio(nome: str) -> str:
    """Remove prefixo 'Ce-' do nome do município."""
    nome = nome.strip()
    if nome.startswith("Ce-"):
        return nome[3:]
    return nome


def limpar_valor(valor: str) -> str:
    """Normaliza valores ausentes."""
    if valor is None:
        return ""
    valor = str(valor).strip()
    if valor in ("-", ""):
        return ""
    return valor


def formatar_variacao(valor: str) -> str:
    """Converte variação de formato brasileiro (vírgula) para ponto decimal."""
    valor = limpar_valor(valor)
    if not valor:
        return ""
    return valor.replace(".", "").replace(",", ".")


def parse_blocos_meses(linha_meses: list[str], linha_colunas: list[str]) -> list[dict]:
    """Identifica blocos de colunas por mês a partir das duas primeiras linhas."""
    blocos = []
    indices_mes = [i for i, v in enumerate(linha_meses) if v and "/" in v]

    for idx, inicio in enumerate(indices_mes):
        fim = indices_mes[idx + 1] if idx + 1 < len(indices_mes) else len(linha_colunas)
        colunas = [normalizar_nome_coluna(c) for c in linha_colunas[inicio:fim]]
        blocos.append(
            {
                "mes_ano": linha_meses[inicio].strip(),
                "inicio": inicio,
                "colunas": colunas,
            }
        )

    return blocos


def converter(
    arquivo_entrada: Path = ARQUIVO_ENTRADA,
    arquivo_saida: Path = ARQUIVO_SAIDA,
) -> int:
    if not arquivo_entrada.exists():
        print(f"Erro: arquivo não encontrado: {arquivo_entrada}", file=sys.stderr)
        return 1

    with open(arquivo_entrada, "r", encoding="utf-8-sig", newline="") as f_in:
        leitor = csv.reader(f_in)
        linha_meses = next(leitor)
        linha_colunas = next(leitor)
        linhas_dados = list(leitor)

    blocos = parse_blocos_meses(linha_meses, linha_colunas)
    registros = []

    for linha in linhas_dados:
        if not linha or not linha[0].strip():
            continue

        codigo = linha[0].strip()
        municipio = limpar_municipio(linha[1])

        for bloco in blocos:
            inicio = bloco["inicio"]
            cols = bloco["colunas"]
            valores = linha[inicio : inicio + len(cols)]

            while len(valores) < len(cols):
                valores.append("")

            metricas = dict(zip(cols, valores))

            registro = [
                codigo,
                municipio,
                mes_ano_para_mm_yyyy(bloco["mes_ano"]),
                limpar_valor(metricas.get("Estoque", "")),
                limpar_valor(metricas.get("Admissões", "")),
                limpar_valor(metricas.get("Desligamentos", "")),
                limpar_valor(metricas.get("Saldos", "")),
                formatar_variacao(metricas.get("Variação Relativa (%)", "")),
            ]
            registros.append(registro)

    with open(arquivo_saida, "w", encoding="utf-8-sig", newline="") as f_out:
        escritor = csv.writer(f_out, lineterminator="\n")
        escritor.writerow(CABECALHO_SAIDA)
        escritor.writerows(registros)

    print(f"Conversão concluída.")
    print(f"  Entrada:  {arquivo_entrada}")
    print(f"  Saída:    {arquivo_saida}")
    print(f"  Municípios: {len(linhas_dados)}")
    print(f"  Meses:      {len(blocos)}")
    print(f"  Registros:  {len(registros)}")
    return 0


def main() -> int:
    entrada = Path(sys.argv[1]) if len(sys.argv) > 1 else ARQUIVO_ENTRADA
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else ARQUIVO_SAIDA
    return converter(entrada, saida)


if __name__ == "__main__":
    raise SystemExit(main())
