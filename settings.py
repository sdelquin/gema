from pathlib import Path

from prettyconf import config

PROJECT_DIR = Path(__file__).parent
PROJECT_NAME = PROJECT_DIR.name

CONFIG_PATH = config('CONFIG_PATH', default='config.yaml')
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='<YOUR_TELEGRAM_BOT_TOKEN_HERE>')

LOGFILE = config('LOGFILE', default=PROJECT_DIR / (PROJECT_NAME + '.log'), cast=Path)
LOGFILE_SIZE = config('LOGFILE_SIZE', cast=float, default=1e6)
LOGFILE_BACKUP_COUNT = config('LOGFILE_BACKUP_COUNT', cast=int, default=3)
