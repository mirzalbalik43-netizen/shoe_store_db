
import argparse
from pathlib import Path
import sqlite3
from db_init import DB_PATH, PROJECT_DIR, get_connection


def export_schema(db_path=DB_PATH, out_path=None):
    output=Path(out_path) if out_path else PROJECT_DIR/'db'/'schema_generated.sql'
    with get_connection(db_path) as conn:
        rows=conn.execute('''SELECT type,name,sql FROM sqlite_master
                             WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'
                             ORDER BY CASE type WHEN 'table' THEN 1 WHEN 'index' THEN 2
                                                WHEN 'view' THEN 3 WHEN 'trigger' THEN 4 ELSE 5 END,
                                      name''').fetchall()
    lines=['-- Автоматический экспорт schema из sqlite_master','PRAGMA foreign_keys = ON;','']
    lines.extend(f'-- {r["type"]}: {r["name"]}\n{r["sql"]};\n' for r in rows)
    output.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return output

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',type=Path,default=DB_PATH)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    print(export_schema(args.db,args.output))
