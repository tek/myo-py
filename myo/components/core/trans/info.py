from amino import do, Do, List, _

from ribosome.nvim.scratch import show_in_scratch_buffer_default
from ribosome.trans.api import trans
from ribosome.nvim.io.state import NS
from ribosome.trans.action import Trans

from myo.config.handler import find_handlers
from myo.data.info import InfoWidget


@do(NS[None, None])
def display_info(widgets: List[InfoWidget]) -> Do:
    yield NS.lift(show_in_scratch_buffer_default(widgets // _.lines))


@trans.free.do()
@do(Trans)
def collect_info() -> Do:
    handlers = yield find_handlers(_.info)
    yield handlers.traverse(_, Trans)


@trans.free.do()
@do(Trans)
def info() -> Do:
    widgets = yield collect_info()
    yield display_info(widgets).trans


__all__ = ('info',)
