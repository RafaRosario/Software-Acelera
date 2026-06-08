import argparse
import os
import sys
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import MetaData, Table, create_engine, inspect, select, text


TABLE_ORDER = [
    "motoristas",
    "veiculos",
    "empresas",
    "fornecedores",
    "prestadores_servicos",
    "usuarios",
    "fretes",
]


def mask_url(url: str) -> str:
    """Hide password when printing database URLs."""
    try:
        parts = urlsplit(url)
        if "@" not in parts.netloc:
            return url
        auth, host = parts.netloc.rsplit("@", 1)
        if ":" in auth:
            user, _ = auth.split(":", 1)
            auth = f"{user}:***"
        else:
            auth = "***"
        return urlunsplit((parts.scheme, f"{auth}@{host}", parts.path, parts.query, parts.fragment))
    except Exception:
        return url


def make_engine(url: str):
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def existing_tables(engine, desired: Iterable[str]) -> list[str]:
    names = set(inspect(engine).get_table_names())
    return [name for name in desired if name in names]


def migrate(source_url: str, target_url: str, debug: bool = False) -> None:
    if target_url.startswith("sqlite"):
        raise RuntimeError("Target precisa ser PostgreSQL, nao SQLite.")

    if debug:
        print("[DEBUG] Iniciando migracao...")
        print(f"[DEBUG] Source: {mask_url(source_url)}")
        print(f"[DEBUG] Target: {mask_url(target_url)}")

    src_engine = make_engine(source_url)
    dst_engine = make_engine(target_url)

    if debug:
        with src_engine.connect() as src_conn:
            src_conn.execute(text("SELECT 1"))
        with dst_engine.connect() as dst_conn:
            dst_conn.execute(text("SELECT 1"))
        print("[DEBUG] Conexao com origem e destino OK.")

    src_tables = existing_tables(src_engine, TABLE_ORDER)
    dst_tables = existing_tables(dst_engine, TABLE_ORDER)
    tables = [name for name in TABLE_ORDER if name in src_tables and name in dst_tables]

    if debug:
        print(f"[DEBUG] Tabelas na origem: {src_tables}")
        print(f"[DEBUG] Tabelas no destino: {dst_tables}")
        print(f"[DEBUG] Tabelas que serao migradas: {tables}")

    if not tables:
        raise RuntimeError("Nenhuma tabela em comum encontrada entre origem e destino.")

    src_meta = MetaData()
    dst_meta = MetaData()
    # resolve_fks=False evita falhas quando existem FKs antigas para tabelas
    # legadas que nao existem mais (ex.: veiculos_antigos).
    src_ref = {name: Table(name, src_meta, autoload_with=src_engine, resolve_fks=False) for name in tables}
    dst_ref = {name: Table(name, dst_meta, autoload_with=dst_engine, resolve_fks=False) for name in tables}
    valid_ids: dict[str, set[int]] = {
        "motoristas": set(),
        "veiculos": set(),
        "fretes": set(),
    }

    with src_engine.connect() as src_conn, dst_engine.begin() as dst_conn:
        # Limpa destino mantendo integridade referencial
        truncate_sql = "TRUNCATE TABLE " + ", ".join(tables) + " RESTART IDENTITY CASCADE"
        if debug:
            print(f"[DEBUG] Executando truncate: {truncate_sql}")
        dst_conn.execute(text(truncate_sql))

        for table_name in tables:
            src_table = src_ref[table_name]
            dst_table = dst_ref[table_name]

            common_cols = [col.name for col in dst_table.columns if col.name in src_table.c]
            if debug:
                print(f"[DEBUG] {table_name} - colunas em comum: {common_cols}")
            rows = src_conn.execute(select(*[src_table.c[col] for col in common_cols])).mappings().all()
            if debug:
                print(f"[DEBUG] {table_name} - linhas encontradas na origem: {len(rows)}")

            if rows:
                payload = [{col: row[col] for col in common_cols} for row in rows]

                if table_name in ("motoristas", "veiculos", "fretes") and "id" in common_cols:
                    valid_ids[table_name].update(
                        int(row["id"]) for row in payload if row.get("id") is not None
                    )

                if table_name == "usuarios" and "motorista_id" in common_cols:
                    ajustados = 0
                    for row in payload:
                        motorista_id = row.get("motorista_id")
                        if motorista_id is not None and int(motorista_id) not in valid_ids["motoristas"]:
                            row["motorista_id"] = None
                            ajustados += 1
                    if debug and ajustados:
                        print(f"[DEBUG] usuarios - motorista_id orfao ajustado para NULL: {ajustados}")

                if table_name == "fretes":
                    ajustados_veiculo = 0
                    ajustados_motorista = 0
                    ajustados_principal = 0
                    frete_ids = valid_ids["fretes"]
                    for row in payload:
                        veiculo_id = row.get("veiculo_id")
                        if veiculo_id is not None and int(veiculo_id) not in valid_ids["veiculos"]:
                            row["veiculo_id"] = None
                            ajustados_veiculo += 1

                        motorista_id = row.get("motorista_id")
                        if motorista_id is not None and int(motorista_id) not in valid_ids["motoristas"]:
                            row["motorista_id"] = None
                            ajustados_motorista += 1

                        principal_id = row.get("frete_principal_id")
                        if principal_id is not None and int(principal_id) not in frete_ids:
                            row["frete_principal_id"] = None
                            ajustados_principal += 1

                    if debug and (ajustados_veiculo or ajustados_motorista or ajustados_principal):
                        print(
                            "[DEBUG] fretes - FKs orfas ajustadas para NULL: "
                            f"veiculo_id={ajustados_veiculo}, "
                            f"motorista_id={ajustados_motorista}, "
                            f"frete_principal_id={ajustados_principal}"
                        )

                dst_conn.execute(dst_table.insert(), payload)
                print(f"[OK] {table_name}: {len(payload)} registros")
            else:
                print(f"[OK] {table_name}: 0 registros")

        # Ajusta sequencias de id apos insercao explicita
        for table_name in tables:
            dst_cols = {col.name for col in dst_ref[table_name].columns}
            if "id" not in dst_cols:
                if debug:
                    print(f"[DEBUG] {table_name} - sem coluna id, pulando ajuste de sequencia.")
                continue
            if debug:
                print(f"[DEBUG] {table_name} - ajustando sequencia de id.")
            dst_conn.execute(
                text(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                        (SELECT MAX(id) IS NOT NULL FROM {table_name})
                    )
                    """
                )
            )

    print("\nMigracao concluida com sucesso.")


def main():
    parser = argparse.ArgumentParser(description="Migra dados do SQLite local para PostgreSQL.")
    parser.add_argument(
        "--source",
        default=os.getenv("SOURCE_DATABASE_URL", "sqlite:///./acelera.db"),
        help="URL do banco de origem (default: sqlite:///./acelera.db)",
    )
    parser.add_argument(
        "--target",
        default=os.getenv("DATABASE_URL", ""),
        help="URL do banco de destino (default: DATABASE_URL)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Mostra logs detalhados para diagnostico.",
    )
    args = parser.parse_args()

    if not args.target:
        print("Defina DATABASE_URL ou passe --target com a URL do PostgreSQL.", file=sys.stderr)
        sys.exit(1)

    try:
        migrate(args.source, args.target, debug=args.debug)
    except Exception as exc:
        print(f"Erro na migracao: {exc}", file=sys.stderr)
        if args.debug:
            import traceback
            print("\n[DEBUG] Stack trace completo:", file=sys.stderr)
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
