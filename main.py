import logzero
import typer

from lib.core import GobCanEmailAlarm
from lib.utils import init_logger

logger = init_logger()
app = typer.Typer(add_completion=False)


@app.command()
def run(
    notify: bool = typer.Option(True, help='Notify users with new emails.'),
    delete: bool = typer.Option(True, help='Delete pop3 emails after dispatching'),
    loglevel: str = typer.Option(
        'DEBUG', '--loglevel', '-l', help='Log level (debug, info, error)'
    ),
):
    '''GobCan Email Alert'''

    logger.setLevel(getattr(logzero, loglevel.upper()))
    gema = GobCanEmailAlarm(notify=notify, delete=delete)
    gema.dispatch()


if __name__ == "__main__":
    app()
