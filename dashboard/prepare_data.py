#!/usr/bin/env python3
"""
Prepara dados JSON para o dashboard a partir dos CSVs do CAGED.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parent
BASE_DIR = DASHBOARD_DIR.parent
DATA_DIR = DASHBOARD_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

MESES = {
    "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Marco": "03",
    "Abril": "04", "Maio": "05", "Junho": "06", "Julho": "07",
    "Agosto": "08", "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12",
}

NOMES_MES = {
    "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr", "05": "Mai", "06": "Jun",
    "07": "Jul", "08": "Ago", "09": "Set", "10": "Out", "11": "Nov", "12": "Dez",
}


def norm_col(n):
    return n.strip().replace("\n", "").replace("\ufeff", "")


def norm_mes(m):
    m = m.strip()
    if "/" not in m:
        return m
    p, a = m.split("/", 1)
    if p.isdigit():
        return f"{int(p):02d}/{a.strip()}"
    num = MESES.get(p.strip())
    return f"{num}/{a.strip()}" if num else m


def to_num(v):
    v = str(v).strip().replace('"', "")
    if v in ("", "-"):
        return None
    try:
        n = float(v.replace(",", "."))
        return int(n) if n == int(n) else n
    except ValueError:
        return None


def mes_sort_key(mes_ano):
    mm, aa = mes_ano.split("/")
    return (int(aa), int(mm))


def label_mes(mes_ano):
    mm, aa = mes_ano.split("/")
    return f"{NOMES_MES.get(mm, mm)}/{aa}"


def carregar_csv(nome):
    path = BASE_DIR / nome
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    header = [norm_col(c) for c in rows[0]]
    idx = {c: i for i, c in enumerate(header)}
    registros = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        registros.append({
            "codigo": row[idx["Código do Município"]].strip(),
            "municipio": row[idx["Município"]].strip(),
            "mes_ano": norm_mes(row[idx["Mês/ano"]].strip()),
            "estoque": to_num(row[idx["Estoque"]]),
            "admissoes": to_num(row[idx["Admissões"]]),
            "desligamentos": to_num(row[idx["Desligamentos"]]),
            "saldos": to_num(row[idx["Saldos"]]),
        })
    return registros


def soma_saldos_periodo(serie_mensal, mes_ini, mes_fim):
    """Soma dos saldos mensais (adm − des) entre mes_ini e mes_fim, inclusive."""
    return sum(
        s["saldo"] for s in serie_mensal
        if mes_sort_key(mes_ini) <= mes_sort_key(s["mes_ano"]) <= mes_sort_key(mes_fim)
    )


def processar_abri(registros):
    por_mes = defaultdict(lambda: {"estoque": 0, "adm": 0, "des": 0, "saldo": 0, "n": 0})
    por_ano = defaultdict(lambda: {"adm": 0, "des": 0, "saldo": 0, "meses": 0})
    por_muni = defaultdict(lambda: {"nome": "", "por_mes": {}})

    for r in registros:
        mes = r["mes_ano"]
        ano = int(mes.split("/")[1])
        cod = r["codigo"]
        est = r["estoque"] or 0
        adm = r["admissoes"] or 0
        des = r["desligamentos"] or 0
        sal = r["saldos"] or 0

        por_mes[mes]["estoque"] += est
        por_mes[mes]["adm"] += adm
        por_mes[mes]["des"] += des
        por_mes[mes]["saldo"] += sal
        por_mes[mes]["n"] += 1

        por_ano[ano]["adm"] += adm
        por_ano[ano]["des"] += des
        por_ano[ano]["saldo"] += sal
        por_ano[ano]["meses"] += 1

        por_muni[cod]["nome"] = r["municipio"]
        por_muni[cod]["por_mes"][mes] = est

    meses_ord = sorted(por_mes.keys(), key=mes_sort_key)
    serie_mensal = []
    for mes in meses_ord:
        d = por_mes[mes]
        serie_mensal.append({
            "mes_ano": mes,
            "label": label_mes(mes),
            "estoque": d["estoque"],
            "admissoes": d["adm"],
            "desligamentos": d["des"],
            "saldo": d["saldo"],
            "municipios": d["n"],
        })

    anos_ord = sorted(por_ano.keys())
    serie_anual = []
    for ano in anos_ord:
        d = por_ano[ano]
        serie_anual.append({
            "ano": ano,
            "admissoes": d["adm"],
            "desligamentos": d["des"],
            "saldo": d["saldo"],
        })

    # Crescimento por município jan/2023 -> jan/2026
    crescimento_muni = []
    for cod, info in por_muni.items():
        e23 = info["por_mes"].get("01/2023")
        e26 = info["por_mes"].get("01/2026")
        if e23 is not None and e26 is not None:
            diff = e26 - e23
            pct = (diff / e23 * 100) if e23 else 0
            crescimento_muni.append({
                "codigo": cod,
                "municipio": info["nome"],
                "estoque_2023": e23,
                "estoque_2026": e26,
                "crescimento": diff,
                "percentual": round(pct, 2),
            })
    crescimento_muni.sort(key=lambda x: x["crescimento"], reverse=True)

    # KPIs — comparativo jan/2023 → abr/2026
    ultimo = serie_mensal[-1] if serie_mensal else {}
    ini23 = next((s for s in serie_mensal if s["mes_ano"] == "01/2023"), None)
    fim26 = next((s for s in serie_mensal if s["mes_ano"] == "04/2026"), None) or ultimo
    ini20 = next((s for s in serie_mensal if s["mes_ano"] == "01/2020"), None)

    cresc_2326 = soma_saldos_periodo(serie_mensal, "01/2023", fim26["mes_ano"])
    diff_est_2326 = (fim26["estoque"] - ini23["estoque"]) if ini23 and fim26 else 0
    pct_2326 = round(cresc_2326 / ini23["estoque"] * 100, 1) if ini23 and ini23["estoque"] else 0

    mes_fim = fim26["mes_ano"]
    cresc_2026 = soma_saldos_periodo(serie_mensal, "01/2020", mes_fim) if ini20 else 0
    diff_est_2026 = (fim26["estoque"] - ini20["estoque"]) if ini20 and fim26 else 0
    pct_2026 = round(cresc_2026 / ini20["estoque"] * 100, 1) if ini20 and ini20["estoque"] else 0

    kpis = {
        "estoque_atual": ultimo.get("estoque", 0),
        "mes_atual": ultimo.get("label", ""),
        "municipios": ultimo.get("municipios", 0),
        "mes_inicio": ini23["mes_ano"] if ini23 else "",
        "mes_fim": mes_fim,
        "mes_inicio_label": ini23["label"] if ini23 else "",
        "mes_fim_label": fim26["label"] if fim26 else "",
        "estoque_inicio": ini23["estoque"] if ini23 else 0,
        "estoque_fim": fim26["estoque"] if fim26 else 0,
        "crescimento_2023_2026": cresc_2326,
        "percentual_2023_2026": pct_2326,
        "diff_estoque_2023_2026": diff_est_2326,
        "crescimento_2020_2026": cresc_2026,
        "percentual_2020_2026": pct_2026,
        "diff_estoque_2020_2026": diff_est_2026,
        "saldo_2025": next((a["saldo"] for a in serie_anual if a["ano"] == 2025), 0),
        "saldo_2026_parcial": sum(
            s["saldo"] for s in serie_mensal
            if s["mes_ano"].endswith("/2026") and int(s["mes_ano"].split("/")[0]) <= 4
        ),
    }

    # Estoque de janeiro por ano (comparabilidade)
    jan_por_ano = []
    for s in serie_mensal:
        if s["mes_ano"].startswith("01/"):
            jan_por_ano.append({"ano": int(s["mes_ano"].split("/")[1]), "estoque": s["estoque"]})

    return {
        "serie_mensal": serie_mensal,
        "serie_anual": serie_anual,
        "jan_por_ano": jan_por_ano,
        "top_crescimento": crescimento_muni[:15],
        "top_queda": sorted(crescimento_muni, key=lambda x: x["crescimento"])[:10],
        "kpis": kpis,
    }


def processar_diferencas():
    path = BASE_DIR / "dados_caged_diferencas.csv"
    if not path.exists():
        return None

    por_ano = defaultdict(lambda: {"soma_diff": 0, "n": 0})
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            diff = to_num(row.get("Estoque_diff", ""))
            if diff is None:
                continue
            ano = int(row["Mês/ano"].split("/")[1])
            por_ano[ano]["soma_diff"] += diff
            por_ano[ano]["n"] += 1

    return {
        "por_ano": [{"ano": a, "soma_diff": d["soma_diff"], "media_diff": round(d["soma_diff"] / d["n"]) if d["n"] else 0}
                    for a, d in sorted(por_ano.items())],
    }


def main():
    print("Preparando dados do dashboard...")
    abri = carregar_csv("dados_caged_abri.csv")
    payload = {
        "gerado_em": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "fonte": "dados_caged_abri.csv",
        "emprego": processar_abri(abri),
        "ajuste_cadastral": processar_diferencas(),
    }

    out = DATA_DIR / "emprego_ce.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"  -> {out} ({out.stat().st_size // 1024} KB)")
    print("Dados prontos.")


if __name__ == "__main__":
    main()
