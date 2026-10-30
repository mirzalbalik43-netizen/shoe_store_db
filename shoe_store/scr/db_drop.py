
import argparse
from pathlib import Path
from db_init import DB_PATH

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',type=Path,default=DB_PATH)
    parser.add_argument('--yes',action='store_true',help='Подтверждение опасной операции')
    args=parser.parse_args()
    if not args.yes:
        parser.error('База удаляется необратимо. Передайте --yes для подтверждения.')
    for suffix in ['', '-wal','-shm']:
        target=Path(str(args.db)+suffix)
        if target.exists():
            target.unlink()
            print('Удалён файл',target)
