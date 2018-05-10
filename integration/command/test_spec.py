from kallikrein import Expectation, k
from kallikrein.matchers.lines import have_lines

from amino import do, Do, List
from amino.test import fixture_path
from amino.test.spec import SpecBase

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.api import N
from ribosome.nvim.api.ui import buffers, buffer_content
from ribosome.test.rpc import json_cmd
from ribosome.test.integration.embed import plugin_test
from ribosome.nvim.api.data import Buffer
from ribosome.test.klk.expectation import await_k
from ribosome.nvim.api.util import nvimio_await_success

from test.command import command_spec_test_config
from test.test import mock_test_functions


file = fixture_path('command', 'test', 'code.py')
target = List('  File "<string>", line 1, in <module>', 'RuntimeError: No active exception to reraise')


@do(NvimIO[Buffer])
def scratch_buffer() -> Do:
    bufs = yield buffers()
    yield N.from_maybe(bufs.lift(1), 'scratch buffer wasn\'t opened')


@do(NvimIO[Buffer])
def scratch_content() -> Do:
    buf = yield nvimio_await_success(scratch_buffer, 1.)
    content = yield buffer_content(buf)
    return k(content).must(have_lines(target))


@do(NvimIO[Expectation])
def run_spec() -> Do:
    yield mock_test_functions()
    yield json_cmd('MyoVimTest')
    yield json_cmd('MyoParse')
    yield await_k(scratch_content)


# TODO test empty `ParseOutput`
class TestSpec(SpecBase):
    '''run a test command $run
    '''

    def run(self) -> Expectation:
        return plugin_test(command_spec_test_config, run_spec)


__all__ = ('TestSpec',)
