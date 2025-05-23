import telegramtk
from logzero import logger

import settings
from lib.email.server import Pop3Server


class GobCanEmailAlarm:
    def __init__(self, notify: bool = True, delete: bool = True):
        self.server = Pop3Server()
        self.notify = notify
        self.delete = delete

        if not self.notify:
            logger.warning('Disabled email notification')
        if not self.delete:
            logger.warning('Disabled email deletion after dispatching')

    def dispatch(self, telegram_chat_id=settings.TELEGRAM_CHAT_ID):
        logger.info('👤 Dispatching emails')
        for email in self.server.fetch():
            if email is None:
                logger.warning('Skipping this email')
                continue
            try:
                logger.info(email)
                if self.notify:
                    telegramtk.send_message(telegram_chat_id, email.as_markdown())
            except Exception as err:
                logger.error(err)
            else:
                if self.delete:
                    self.server.delete(email)
