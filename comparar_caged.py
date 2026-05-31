#!/usr/bin/env python3
"""
Compara Estoque, Admissões, Desligamentos e Saldos entre dados_caged_mar.csv
e dados_caged_abri.csv, usando como chave Código do Município, Município e Mês/ano.

O Mês/ano é normalizado internamente (ex.: 'Janeiro/2026' = '01/2026') para
permitir o cruzamento entre arquivos com formatos de data diferentes.

Gera arquivo CSV apenas com linhas em que as chaves coincidem e alguma métrica difere.
A coluna *_diff indica (valor_abri - valor_mar); negativo = abri menor que mar.
"""

import csv
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ARQUIVO_MAR = SCRIPT_DIR / "dados_caged_mar.csv"
ARQUIVO_ABRI = SCRIPT_DIR / "dados_caged_abri.csv"
ARQUIVO_SAIDA = SCRIPT_DIR / "dados_caged_diferencas.csv"

METRICAS = ["Estoque", "Admissões", "Desligamentos", "Saldos"]

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

CABECALHO_SAIDA = [
    "Código do Município",
    "Município",
    "Mês/ano",
    "Estoque_mar",
    "Estoque_abri",
    "Estoque_diff",
    "Admissões_mar",
    "Admissões_abri",
    "Admissões_diff",
    "Desligamentos_mar",
    "Desligamentos_abri",
    "Desligamentos_diff",
    "Saldos_mar",
    "Saldos_abri",
    "Saldos_diff",
]


def normalizar_coluna(nome: str) -> str:
    return nome.strip().replace("\n", "").replace("\ufeff", "")


def normalizar_mes_ano(mes_ano: str) -> str:
    """Unifica formatos como 'Janeiro/2026' e '01/2026'."""
    mes_ano = mes_ano.strip()
    if "/" not in mes_ano:
        return mes_ano
    parte, ano = mes_ano.split("/", 1)
    ano = ano.strip()
    if parte.isdigit():
        return f"{int(parte):02d}/{ano}"
    numero = MESES.get(parte.strip())
    if numero:
        return f"{numero}/{ano}"
    return mes_ano


def parse_numero(valor: str):
    valor = str(valor).strip().replace('"', "")
    if valor in ("", "-"):
        return None
    valor = valor.replace(",", ".")
    try:
        num = float(valor)
        return int(num) if num == int(num) else num
    except ValueError:
        return valor


def formatar_numero(valor):
    if valor is None:
        return ""
    if isinstance(valor, float) and valor == int(valor):
        return str(int(valor))
    return str(valor)


def calcular_diff(valor_abri, valor_mar):
    if valor_abri is None and valor_mar is None:
        return None
    if valor_abri is None or valor_mar is None:
        return None
    if isinstance(valor_abri, (int, float)) and isinstance(valor_mar, (int, float)):
        diff = valor_abri - valor_mar
        return int(diff) if diff == int(diff) else diff
    return None


def carregar_arquivo(caminho: Path) -> dict[tuple[str, str, str], dict[str, object]]:
    with open(caminho, "r", encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.reader(f))

    cabecalho = [normalizar_coluna(c) for c in linhas[0]]
    indices = {col: i for i, col in enumerate(cabecalho)}

    dados = {}
    for linha in linhas[1:]:
        if not linha or not linha[0].strip():
            continue

        codigo = linha[indices["Código do Município"]].strip()
        municipio = linha[indices["Município"]].strip()
        mes_ano_original = linha[indices["Mês/ano"]].strip()
        mes_ano = normalizar_mes_ano(mes_ano_original)
        chave = (codigo, municipio, mes_ano)

        dados[chave] = {
            "mes_ano_original": mes_ano_original,
            **{metrica: parse_numero(linha[indices[metrica]]) for metrica in METRICAS},
        }

    return dados


def comparar(
    arquivo_mar: Path = ARQUIVO_MAR,
    arquivo_abri: Path = ARQUIVO_ABRI,
    arquivo_saida: Path = ARQUIVO_SAIDA,
) -> int:
    if not arquivo_mar.exists():
        print(f"Erro: arquivo não encontrado: {arquivo_mar}", file=sys.stderr)
        return 1
    if not arquivo_abri.exists():
        print(f"Erro: arquivo não encontrado: {arquivo_abri}", file=sys.stderr)
        return 1

    dados_mar = carregar_arquivo(arquivo_mar)
    dados_abri = carregar_arquivo(arquivo_abri)

    chaves_comuns = sorted(set(dados_mar) & set(dados_abri))
    chaves_so_mar = sorted(set(dados_mar) - set(dados_abri))
    chaves_so_abri = sorted(set(dados_abri) - set(dados_mar))

    registros_diff = []
    contagem_metricas_menor = {m: 0 for m in METRICAS}
    contagem_metricas_maior = {m: 0 for m in METRICAS}

    for chave in chaves_comuns:
        registro_mar = dados_mar[chave]
        registro_abri = dados_abri[chave]
        valores_mar = {m: registro_mar[m] for m in METRICAS}
        valores_abri = {m: registro_abri[m] for m in METRICAS}

        if valores_mar == valores_abri:
            continue

        codigo, municipio, mes_ano = chave
        linha = [codigo, municipio, mes_ano]

        for metrica in METRICAS:
            vm = valores_mar[metrica]
            va = valores_abri[metrica]
            diff = calcular_diff(va, vm)

            linha.extend([formatar_numero(vm), formatar_numero(va), formatar_numero(diff)])

            if isinstance(diff, (int, float)):
                if diff < 0:
                    contagem_metricas_menor[metrica] += 1
                elif diff > 0:
                    contagem_metricas_maior[metrica] += 1

        registros_diff.append(linha)

    with open(arquivo_saida, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, lineterminator="\n")
        escritor.writerow(CABECALHO_SAIDA)
        escritor.writerows(registros_diff)

    print("Comparação concluída.")
    print(f"  Mar:  {len(dados_mar)} registros")
    print(f"  Abri: {len(dados_abri)} registros")
    print(f"  Chaves iguais (código + município + mês/ano): {len(chaves_comuns)}")
    print(f"  Chaves só em mar:  {len(chaves_so_mar)}")
    print(f"  Chaves só em abri: {len(chaves_so_abri)}")
    print(f"  Linhas com diferença: {len(registros_diff)}")
    print(f"  Saída: {arquivo_saida}")
    print()
    print("Diferenças (abri - mar) por métrica:")
    for metrica in METRICAS:
        print(
            f"  {metrica}: abri menor em {contagem_metricas_menor[metrica]} linhas, "
            f"abri maior em {contagem_metricas_maior[metrica]} linhas"
        )

    return 0


def main() -> int:
    mar = Path(sys.argv[1]) if len(sys.argv) > 1 else ARQUIVO_MAR
    abri = Path(sys.argv[2]) if len(sys.argv) > 2 else ARQUIVO_ABRI
    saida = Path(sys.argv[3]) if len(sys.argv) > 3 else ARQUIVO_SAIDA
    return comparar(mar, abri, saida)


if __name__ == "__main__":
    raise SystemExit(main())
