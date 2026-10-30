
from backup_restore import backup_safe, check_integrity, clear_old_logs, get_db_stats
from db_init import get_connection


def run_maintenance():
    with get_connection() as c:
        integrity = check_integrity(c)
        if integrity != ['ok']:
            raise RuntimeError(f'Обнаружено повреждение БД: {integrity}')
    archive = backup_safe()
    with get_connection() as c:
        stats = get_db_stats(c)
        removed = clear_old_logs(c, days=30)
    result = {'integrity': integrity, 'backup': str(archive), 'stats': stats,
              'old_logs_removed': removed}
    print('Обслуживание завершено успешно')
    print(result)
    return result


if __name__ == '__main__':
    run_maintenance()
