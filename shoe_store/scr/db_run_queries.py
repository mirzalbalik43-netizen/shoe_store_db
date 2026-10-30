
import argparse
from pathlib import Path
from db_init import DB_PATH, PROJECT_DIR, get_connection

SQL_PATH=PROJECT_DIR/'queries'/'04_check_queries.sql'


def run_queries(db_path=DB_PATH, write_report=True):
    content=SQL_PATH.read_text(encoding='utf-8')
    statements=[]
    descriptions=[]
    accumulator=[]
    for line in content.splitlines():
        if line.lstrip().startswith('--'):
            if line.startswith('-- ') and line[3:4].isdigit():
                descriptions.append(line.lstrip('- ').strip())
            continue
        accumulator.append(line)
        if ';' in line:
            query='\n'.join(accumulator).strip().rstrip(';').strip()
            if query:
                statements.append(query)
            accumulator=[]
    result=[]
    with get_connection(db_path) as conn:
        for i,sql in enumerate(statements):
            cursor=conn.execute(sql)
            names=[d[0] for d in cursor.description]
            records=cursor.fetchall()
            result.append((descriptions[i] if i<len(descriptions) else f'Запрос {i+1}',sql,names,records))
    if write_report:
        md=['# УП.11 №4 — Фактические результаты SQL-запросов','',
            f'Запросы выполнены на базе `{Path(db_path).name}`, SQL-файл `queries/04_check_queries.sql`.','']
        for name,sql,columns,records in result:
            md.extend([f'## {name}','',f'Возвращено строк: **{len(records)}**.','',
                       '| '+' | '.join(columns)+' |','| '+' | '.join('---' for _ in columns)+' |'])
            for r in records[:8]:
                md.append('| '+' | '.join(str(value).replace('|','\\|').replace('\n',' ') if value is not None else 'NULL' for value in r)+' |')
            if not records: md.append('| '+' | '.join('—' for _ in columns)+' |')
            if len(records)>8: md.append(f'\n*Показаны первые 8 из {len(records)} строк.*')
            md.append('')
        (PROJECT_DIR/'docs'/'04_query_results.md').write_text('\n'.join(md),encoding='utf-8')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',type=Path,default=DB_PATH)
    args=parser.parse_args()
    for name,sql,cols,rows in run_queries(args.db):
        print(f'{name}: {len(rows)} строк')
