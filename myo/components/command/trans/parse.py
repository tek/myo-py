from typing import TypeVar

from ribosome.trans.api import trans
from ribosome.trans.action import TransM
from ribosome.nvim.io import NS
from ribosome.config.config import Resources

from amino import do, Do, List, Dat

from myo.settings import MyoSettings
from myo.config.component import MyoComponent
from myo.env import Env
from myo.output import Parsing
from myo.output.data import ParseResult

D = TypeVar('D')


class ParseConfig(Dat['ParseConfig']):

    def __init__(self, langs: List[str]) -> None:
        self.langs = langs


@do(NS[Resources[Env, MyoSettings, MyoComponent], None])
def parse_config() -> Do:
    yield NS.pure(ParseConfig(List('python')))


@do(NS[D, ParseResult])
def parse_output(output: List[str], config: ParseConfig) -> Do:
    parsing = yield NS.delay(lambda v: Parsing(v, config.langs))
    result = yield NS.from_io(parsing.parse(output, None))


@trans.free.do()
@do(TransM)
def parse(output: List[str]) -> Do:
    config = yield parse_config().trans
    yield parse_output(output, config).trans


@trans.free.do()
@do(TransM)
def parse_pane() -> Do:
    yield TransM.unit


__all__ = ('parse',)
