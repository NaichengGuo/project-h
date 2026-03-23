import argparse
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pymysql
from pyhive import hive

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

#python /mnt/workspace/draft/hive_2ops_db/sync_poker_hive_to_mysql.py --dt 2026-03-17

MYSQL_HOST="test.cjudqgucury7.ap-southeast-1.rds.amazonaws.com"
MYSQL_PORT="3306"
MYSQL_USER="poker_analysis_user1"
MYSQL_PASSWORD="password01"
MYSQL_DB="poker_data_analysis"

HIVE_HOST="10.0.21.126"
HIVE_PORT="10000"
HIVE_USER="root"
HIVE_DB="default"

@dataclass(frozen=True)
class ColumnSpec:
    name: str
    hive_type: str
    is_partition: bool


@dataclass(frozen=True)
class TableSpec:
    hive_table: str
    mysql_table: str
    columns: Tuple[ColumnSpec, ...]
    partition_columns: Tuple[str, ...]


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SAFE_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SAFE_PART_VALUE_RE = re.compile(r"^[A-Za-z0-9_\-:.]+$")


def _yesterday_dt_str() -> str:
    if ZoneInfo is not None:
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
    else:
        now = datetime.now()
    return (now - timedelta(days=1)).strftime("%Y-%m-%d")


def _strip_backticks(s: str) -> str:
    s = s.strip()
    if s.startswith("`") and s.endswith("`") and len(s) >= 2:
        return s[1:-1]
    return s


def _quote_mysql_ident(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def _quote_hive_table(full_name: str) -> str:
    parts = [p.strip() for p in full_name.split(".") if p.strip()]
    return ".".join([f"`{p.replace('`', '``')}`" for p in parts])


def _quote_hive_ident(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def _parse_partition_spec(spec: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    raw = spec.strip()
    if not raw:
        return result
    for part in [p.strip() for p in raw.split(",") if p.strip()]:
        if "=" not in part:
            raise ValueError(f"Invalid partition spec segment: {part}")
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError(f"Invalid partition spec segment: {part}")
        if not _SAFE_IDENT_RE.match(key):
            raise ValueError(f"Unsafe partition column: {key}")
        if not _SAFE_PART_VALUE_RE.match(value):
            raise ValueError(f"Unsafe partition value for {key}: {value}")
        result[key] = value
    return result


def parse_data_dictionary(md_path: str) -> List[TableSpec]:
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    tables: List[Dict[str, object]] = []
    current: Optional[Dict[str, object]] = None
    mode: Optional[str] = None

    for line in lines:
        m = re.match(r"^\s*-\s*表名：`([^`]+)`\s*$", line)
        if m:
            hive_table = m.group(1).strip()
            mysql_table = hive_table.split(".")[-1]
            current = {
                "hive_table": hive_table,
                "mysql_table": mysql_table,
                "columns": [],
                "partitions": [],
            }
            tables.append(current)
            mode = None
            continue

        if current is None:
            continue

        if line.strip().startswith("### 字段"):
            mode = "columns"
            continue
        if line.strip().startswith("### 分区字段"):
            mode = "partitions"
            continue
        if line.strip().startswith("## "):
            mode = None
            continue

        if mode not in ("columns", "partitions"):
            continue

        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            continue

        parts = [p.strip() for p in s.split("|")]
        if len(parts) < 4:
            continue
        raw_name = _strip_backticks(parts[1])
        raw_type = _strip_backticks(parts[2])
        if raw_name in ("字段名", "---", ""):
            continue
        if raw_name.startswith("---"):
            continue
        if raw_type in ("类型", "---", ""):
            continue

        if mode == "columns":
            current["columns"].append((raw_name, raw_type))
        else:
            current["partitions"].append((raw_name, raw_type))

    specs: List[TableSpec] = []
    for t in tables:
        hive_table = str(t["hive_table"])
        mysql_table = str(t["mysql_table"])
        cols: List[ColumnSpec] = []
        seen = set()

        for name, hive_type in t["columns"]:
            if name in seen:
                continue
            cols.append(ColumnSpec(name=name, hive_type=hive_type, is_partition=False))
            seen.add(name)

        partition_names: List[str] = []
        for name, hive_type in t["partitions"]:
            partition_names.append(name)
            if name in seen:
                continue
            cols.append(ColumnSpec(name=name, hive_type=hive_type, is_partition=True))
            seen.add(name)

        specs.append(
            TableSpec(
                hive_table=hive_table,
                mysql_table=mysql_table,
                columns=tuple(cols),
                partition_columns=tuple(partition_names),
            )
        )
    return specs


def hive_type_to_mysql_type(col: ColumnSpec) -> str:
    t = col.hive_type.strip().lower()
    if t.startswith("decimal(") and t.endswith(")"):
        inner = t[len("decimal(") : -1]
        if re.match(r"^\d+\s*,\s*\d+$", inner):
            p, s = [x.strip() for x in inner.split(",", 1)]
            return f"DECIMAL({p},{s})"
        return "DECIMAL(38,18)"
    if t in ("bigint",):
        return "BIGINT"
    if t in ("int",):
        return "INT"
    if t in ("tinyint",):
        return "TINYINT"
    if t in ("smallint",):
        return "SMALLINT"
    if t in ("double",):
        return "DOUBLE"
    if t in ("float",):
        return "FLOAT"
    if t in ("date",):
        return "DATE"
    if t in ("timestamp",):
        return "DATETIME"
    if t in ("boolean",):
        return "TINYINT"
    if t in ("string", "varchar", "char"):
        if col.is_partition or col.name == "dt":
            return "VARCHAR(32)"
        return "TEXT"
    return "TEXT"


def build_create_table_sql(mysql_table: str, columns: Sequence[ColumnSpec], partition_cols: Sequence[str]) -> str:
    col_lines: List[str] = []
    for col in columns:
        mysql_type = hive_type_to_mysql_type(col)
        col_lines.append(f"{_quote_mysql_ident(col.name)} {mysql_type} NULL")

    key_sql = ""
    safe_partition_cols = [c for c in partition_cols if c in {x.name for x in columns}]
    if safe_partition_cols:
        cols_sql = ",".join([_quote_mysql_ident(c) for c in safe_partition_cols])
        key_sql = f",KEY {_quote_mysql_ident('idx_partition')} ({cols_sql})"

    cols_sql = ",\n  ".join(col_lines)
    return (
        f"CREATE TABLE IF NOT EXISTS {_quote_mysql_ident(mysql_table)} (\n"
        f"  {cols_sql}{key_sql}\n"
        f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    )


def _validate_dt(dt_str: str) -> None:
    if not _DATE_RE.match(dt_str):
        raise ValueError(f"Invalid dt: {dt_str}")


def _connect_mysql(host: str, port: int, user: str, password: str, database: str) -> pymysql.connections.Connection:
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=None,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.Cursor,
    )
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {_quote_mysql_ident(database)} DEFAULT CHARACTER SET utf8mb4")
        cursor.execute(f"USE {_quote_mysql_ident(database)}")
    conn.commit()
    return conn


def _connect_hive(host: str, port: int, username: str, database: str):
    return hive.connect(host=host, port=port, username=username, database=database)


def _select_tables(all_tables: Sequence[TableSpec], selected: Optional[Sequence[str]]) -> List[TableSpec]:
    if not selected:
        return list(all_tables)

    selected_norm = {s.strip() for s in selected if s.strip()}
    selected_full = {s for s in selected_norm if "." in s}
    selected_short = {s for s in selected_norm if "." not in s}

    result: List[TableSpec] = []
    for t in all_tables:
        if t.hive_table in selected_full:
            result.append(t)
            continue
        if t.mysql_table in selected_short:
            result.append(t)
            continue
    return result


def _build_hive_query(table: TableSpec, partition_filters: Dict[str, str]) -> str:
    table_sql = _quote_hive_table(table.hive_table)
    cols_sql = ",".join([_quote_hive_ident(c.name) for c in table.columns])
    where_parts: List[str] = []
    for k, v in partition_filters.items():
        where_parts.append(f"{_quote_hive_ident(k)}='{v}'")
    where_sql = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""
    return f"SELECT {cols_sql} FROM {table_sql}{where_sql}"


def _build_mysql_delete_sql(mysql_table: str, partition_filters: Dict[str, str]) -> Tuple[str, Tuple[object, ...]]:
    if not partition_filters:
        return f"TRUNCATE TABLE {_quote_mysql_ident(mysql_table)}", ()
    where_sql = " AND ".join([f"{_quote_mysql_ident(k)}=%s" for k in partition_filters.keys()])
    return f"DELETE FROM {_quote_mysql_ident(mysql_table)} WHERE {where_sql}", tuple(partition_filters.values())


def _build_mysql_insert_sql(mysql_table: str, column_names: Sequence[str]) -> str:
    cols_sql = ",".join([_quote_mysql_ident(c) for c in column_names])
    placeholders = ",".join(["%s"] * len(column_names))
    return f"INSERT INTO {_quote_mysql_ident(mysql_table)} ({cols_sql}) VALUES ({placeholders})"


def _get_latest_dt_for_table(hive_conn, table: TableSpec) -> Optional[str]:
    if "dt" not in table.partition_columns:
        return None
    cursor = hive_conn.cursor()
    try:
        cursor.execute(f"SHOW PARTITIONS {_quote_hive_table(table.hive_table)}")
        rows = cursor.fetchall()
        candidates: List[str] = []
        for (spec,) in rows:
            s = str(spec)
            parts = [p for p in s.split("/") if p]
            for p in parts:
                if p.startswith("dt="):
                    val = p.split("=", 1)[1]
                    if _DATE_RE.match(val):
                        candidates.append(val)
                    break
        return max(candidates) if candidates else None
    finally:
        try:
            cursor.close()
        except Exception:
            pass


def sync_one_table(
    hive_conn,
    mysql_conn: pymysql.connections.Connection,
    table: TableSpec,
    mysql_table: str,
    partition_filters: Dict[str, str],
    mode: str,
    batch_size: int,
) -> int:
    create_sql = build_create_table_sql(mysql_table, table.columns, table.partition_columns)
    with mysql_conn.cursor() as mysql_cursor:
        mysql_cursor.execute(create_sql)
    mysql_conn.commit()

    if mode == "overwrite":
        delete_sql, delete_args = _build_mysql_delete_sql(mysql_table, partition_filters)
        with mysql_conn.cursor() as mysql_cursor:
            mysql_cursor.execute(delete_sql, delete_args)
        mysql_conn.commit()

    hive_query = _build_hive_query(table, partition_filters)
    hive_cursor = hive_conn.cursor()
    hive_cursor.execute(hive_query)

    insert_sql = _build_mysql_insert_sql(mysql_table, [c.name for c in table.columns])

    total = 0
    while True:
        rows = hive_cursor.fetchmany(batch_size)
        if not rows:
            break
        with mysql_conn.cursor() as mysql_cursor:
            mysql_cursor.executemany(insert_sql, rows)
        mysql_conn.commit()
        total += len(rows)

    try:
        hive_cursor.close()
    except Exception:
        pass
    return total


def _is_s3_location(location: str) -> bool:
    loc = location.strip().lower()
    return loc.startswith("s3://") or loc.startswith("s3a://") or loc.startswith("s3n://")


def _get_table_location(hive_conn, full_table_name: str) -> Optional[str]:
    cursor = hive_conn.cursor()
    try:
        cursor.execute(f"DESCRIBE FORMATTED {_quote_hive_table(full_table_name)}")
        rows = cursor.fetchall()
        for row in rows:
            if not row:
                continue
            key = str(row[0]).strip()
            if key.lower() == "location:":
                if len(row) >= 2 and row[1] is not None:
                    return str(row[1]).strip()
                return None
        return None
    finally:
        try:
            cursor.close()
        except Exception:
            pass


def _show_tables(hive_conn, database: str) -> List[str]:
    cursor = hive_conn.cursor()
    try:
        cursor.execute(f"SHOW TABLES IN {_quote_hive_ident(database)}")
        rows = cursor.fetchall()
        result: List[str] = []
        for row in rows:
            if not row:
                continue
            result.append(str(row[0]).strip())
        return result
    finally:
        try:
            cursor.close()
        except Exception:
            pass


def _show_partitions(hive_conn, full_table_name: str) -> List[str]:
    cursor = hive_conn.cursor()
    try:
        cursor.execute(f"SHOW PARTITIONS {_quote_hive_table(full_table_name)}")
        rows = cursor.fetchall()
        result: List[str] = []
        for row in rows:
            if not row:
                continue
            result.append(str(row[0]).strip())
        return result
    finally:
        try:
            cursor.close()
        except Exception:
            pass


def _fs_du_bytes(path: str, fs_du_cmd: Sequence[str]) -> int:
    proc = subprocess.run(
        [*fs_du_cmd, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"fs du failed for {path}: {proc.stderr.strip()}")
    for line in proc.stdout.splitlines():
        s = line.strip()
        if not s:
            continue
        m = re.match(r"^(\d+)\s+", s)
        if m:
            return int(m.group(1))
    raise RuntimeError(f"Unable to parse fs du output for {path}: {proc.stdout.strip()}")


def _iter_selected_table_names(
    hive_conn,
    database: str,
    dictionary_tables: Sequence[TableSpec],
    selected: Optional[Sequence[str]],
    scan_hive_db: bool,
) -> List[str]:
    if scan_hive_db:
        all_names = _show_tables(hive_conn, database)
        full = [f"{database}.{name}" for name in all_names]
        if not selected:
            return full
        selected_norm = {s.strip() for s in selected if s.strip()}
        selected_full = {s for s in selected_norm if "." in s}
        selected_short = {s for s in selected_norm if "." not in s}
        result: List[str] = []
        for ft in full:
            short = ft.split(".", 1)[1] if "." in ft else ft
            if ft in selected_full or short in selected_short:
                result.append(ft)
        return result

    tables = list(dictionary_tables)
    selected_specs = _select_tables(tables, selected)
    return [t.hive_table for t in selected_specs]


def report_s3_stats(
    hive_conn,
    database: str,
    table_names: Sequence[str],
    fs_du_cmd: Sequence[str],
    max_partitions_per_table: int,
    include_unpartitioned: bool,
    output: str,
) -> int:
    s3_tables: List[Tuple[str, str]] = []
    for full_table_name in table_names:
        loc = _get_table_location(hive_conn, full_table_name)
        if loc is None:
            continue
        if _is_s3_location(loc):
            s3_tables.append((full_table_name, loc))

    sys.stdout.write(f"s3_table_count\t{len(s3_tables)}\n")
    sys.stdout.flush()

    if output == "tsv":
        sys.stdout.write("type\ttable\tpartition_count\ttable_location\tpartition_spec\tpartition_location\tsize_mb\n")
        sys.stdout.flush()

    for full_table_name, table_loc in s3_tables:
        partitions: List[str] = []
        try:
            partitions = _show_partitions(hive_conn, full_table_name)
        except Exception:
            partitions = []

        if max_partitions_per_table > 0 and len(partitions) > max_partitions_per_table:
            partitions = partitions[:max_partitions_per_table]

        if not partitions and include_unpartitioned:
            partitions = [""]

        if output == "tsv":
            sys.stdout.write(f"table\t{full_table_name}\t{len(partitions)}\t{table_loc}\t\t\t\n")
            sys.stdout.flush()
        elif output == "jsonl":
            sys.stdout.write(
                f'{{"type":"table","table":"{full_table_name}","partition_count":{len(partitions)},"location":"{table_loc}"}}\n'
            )
            sys.stdout.flush()

        for spec in partitions:
            part_loc = f"{table_loc.rstrip('/')}/{spec}" if spec else table_loc.rstrip("/")
            size_bytes = _fs_du_bytes(part_loc, fs_du_cmd)
            size_mb = round(size_bytes / (1024 * 1024), 2)
            if output == "tsv":
                sys.stdout.write(f"partition\t{full_table_name}\t\t\t{spec}\t{part_loc}\t{size_mb}\n")
            elif output == "jsonl":
                safe_spec = spec
                sys.stdout.write(
                    f'{{"type":"partition","table":"{full_table_name}","partition_spec":"{safe_spec}","location":"{part_loc}","size_mb":{size_mb}}}\n'
                )
            sys.stdout.flush()
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["sync", "s3-stats"], default="sync")
    parser.add_argument("--dictionary", default="/mnt/workspace/draft/hive_2ops_db/poker_hive_data_dictionary.md")
    parser.add_argument("--tables", default="")
    parser.add_argument("--table-prefix", default="")
    parser.add_argument("--mode", choices=["overwrite", "append"], default="overwrite")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--dt", default="")
    parser.add_argument("--partition-spec", default="")
    parser.add_argument("--use-latest-dt", action="store_true")
    parser.add_argument("--scan-hive-db", action="store_true")
    parser.add_argument("--fs-du-cmd", default=os.environ.get("FS_DU_CMD", "hadoop fs -du -s"))
    parser.add_argument("--max-partitions-per-table", type=int, default=0)
    parser.add_argument("--include-unpartitioned", action="store_true")
    parser.add_argument("--output", choices=["tsv", "jsonl"], default="tsv")

    parser.add_argument("--hive-host", default=os.environ.get("HIVE_HOST", "10.0.21.126"))
    parser.add_argument("--hive-port", type=int, default=int(os.environ.get("HIVE_PORT", "10000")))
    parser.add_argument("--hive-user", default=os.environ.get("HIVE_USER", "root"))
    parser.add_argument("--hive-db", default=os.environ.get("HIVE_DB", "default"))

    parser.add_argument("--mysql-host", default=MYSQL_HOST)
    parser.add_argument("--mysql-port", type=int, default=int(MYSQL_PORT))
    parser.add_argument("--mysql-user", default=MYSQL_USER)
    parser.add_argument("--mysql-password", default=MYSQL_PASSWORD)
    parser.add_argument("--mysql-db", default=MYSQL_DB)

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.action == "sync":
        if not args.mysql_host or not args.mysql_user or not args.mysql_password or not args.mysql_db:
            raise SystemExit("Missing MySQL config: MYSQL_HOST/MYSQL_USER/MYSQL_PASSWORD/MYSQL_DB (or CLI args)")

    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be > 0")

    selected = [s.strip() for s in args.tables.split(",") if s.strip()] if args.tables else None
    tables = parse_data_dictionary(args.dictionary)
    tables = _select_tables(tables, selected)

    dt_str = args.dt.strip()
    if not dt_str:
        dt_str = _yesterday_dt_str()
    raw_partition_spec = args.partition_spec.strip()
    partition_filters = _parse_partition_spec(raw_partition_spec)
    if not partition_filters:
        partition_filters = {"dt": dt_str}
    if "dt" in partition_filters:
        _validate_dt(partition_filters["dt"])

    hive_conn = None
    mysql_conn = None
    try:
        hive_conn = _connect_hive(args.hive_host, args.hive_port, args.hive_user, args.hive_db)
        if args.action == "s3-stats":
            fs_du_cmd = tuple(s for s in shlex.split(args.fs_du_cmd) if s.strip())
            if not fs_du_cmd:
                raise SystemExit("--fs-du-cmd is empty")
            table_names = _iter_selected_table_names(
                hive_conn=hive_conn,
                database=args.hive_db,
                dictionary_tables=tables,
                selected=selected,
                scan_hive_db=args.scan_hive_db,
            )
            return report_s3_stats(
                hive_conn=hive_conn,
                database=args.hive_db,
                table_names=table_names,
                fs_du_cmd=fs_du_cmd,
                max_partitions_per_table=args.max_partitions_per_table,
                include_unpartitioned=args.include_unpartitioned,
                output=args.output,
            )

        mysql_conn = _connect_mysql(args.mysql_host, args.mysql_port, args.mysql_user, args.mysql_password, args.mysql_db)

        for t in tables:
            mysql_table = f"{args.table_prefix}{t.mysql_table}"
            effective_filters = {}
            if t.partition_columns:
                if raw_partition_spec:
                    effective_filters = partition_filters
                elif args.use_latest_dt:
                    latest_dt = _get_latest_dt_for_table(hive_conn, t)
                    effective_filters = {"dt": latest_dt} if latest_dt is not None else partition_filters
                else:
                    effective_filters = partition_filters
            count = sync_one_table(
                hive_conn=hive_conn,
                mysql_conn=mysql_conn,
                table=t,
                mysql_table=mysql_table,
                partition_filters=effective_filters,
                mode=args.mode,
                batch_size=args.batch_size,
            )
            sys.stdout.write(f"{t.hive_table} -> {mysql_table}: {count}\n")
            sys.stdout.flush()

    finally:
        try:
            if hive_conn is not None:
                hive_conn.close()
        except Exception:
            pass
        try:
            if mysql_conn is not None:
                mysql_conn.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
