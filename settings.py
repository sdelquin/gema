from pathlib import Path

import telegramtk
from prettyconf import config

PROJECT_DIR = Path(__file__).parent
PROJECT_NAME = PROJECT_DIR.name

TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
telegramtk.init(TELEGRAM_BOT_TOKEN)
TELEGRAM_CHAT_ID = config('TELEGRAM_CHAT_ID')


INBOX = config('INBOX', default='')
POP3_SERVER = config('POP3_SERVER')
POP3_USERNAME = config('POP3_USERNAME')
POP3_PASSWORD = config('POP3_PASSWORD')

LOGFILE = config('LOGFILE', default=PROJECT_DIR / (PROJECT_NAME + '.log'), cast=Path)
LOGFILE_SIZE = config('LOGFILE_SIZE', cast=float, default=1e6)
LOGFILE_BACKUP_COUNT = config('LOGFILE_BACKUP_COUNT', cast=int, default=3)

TIMEZONE = config('TIMEZONE', default='Atlantic/Canary')

INCLUDE_INBOX = config('INCLUDE_INBOX', default=False, cast=config.boolean)
UNPARSED_PLACEHOLDER = config('UNPARSED_PLACEHOLDER', default='?')

EMAIL_REGEX = r'\b[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}\b'
