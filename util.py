import logging
from functools import wraps
from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Extra, Field
from rich.logging import RichHandler
from rich.console import Console

_console = Console()

BASE_LEVEL = logging.ERROR


def trycatch(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyboardInterrupt:
            return

    return wrap


def setup_logger() -> logging.Logger:
    logging.basicConfig(level=BASE_LEVEL)
    logger = logging.getLogger("app")
    logger.handlers = [RichHandler(rich_tracebacks=True)]
    logger.level = logging.DEBUG
    logger.propagate = False
    return logger


def line():
    width = _console.size.width
    logger.debug("─" * (width // 2))

class YesNoResponse(BaseModel):
    answer: Literal['yes', 'Yes', 'no', 'No']
    model_config = ConfigDict(extra='allow')  

class Stage(BaseModel):
    stage: float = Field(default=-1)

_stage = Stage()
def stage() -> Stage:
    return _stage

logger = setup_logger()
