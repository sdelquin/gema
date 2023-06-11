from core import GobCanEmailAlarm
from utils import init_logger

logger = init_logger()


gema = GobCanEmailAlarm()
gema.dispatch()
