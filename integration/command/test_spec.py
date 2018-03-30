from kallikrein import Expectation
from kallikrein.matchers.lines import have_lines
from kallikrein.matchers import contain

from integration._support.spec import ExternalSpec, DefaultSpec
from integration._support.command.setup import command_spec_data

from chiasma.util.id import Ident

from amino import do, Do, _, __, List
from amino.test import fixture_path

from ribosome.nvim.io.compute import NvimIO
from ribosome.test.klk import kn
from ribosome.dispatch.execute import eval_trans, dispatch_state
from ribosome.nvim.io import NSuccess
from ribosome.nvim.api import define_function, buffers, buffer_content
from ribosome.nvim.io.api import N

from myo.components.command.trans.test import vim_test, vim_test_command, test_ident
from myo.components.command.trans.run import RunCommandOptions


file = fixture_path('command', 'test', 'code.py')


@do(NvimIO[None])
def mock_test_functions() -> Do:
    yield define_function('MyoTestDetermineRunner', List('file'), f'return "python"')
    yield define_function('MyoTestExecutable', List('runner'), f'return "python"')
    yield define_function('MyoTestBuildPosition', List('runner', 'pos'), f'return ["-c", "raise Exception(1)"]')
    yield define_function('MyoTestBuildArgs', List('runner', 'args'), f'return a:args')


class TestSpec(ExternalSpec):
    '''
    create the test command if it doesn't exist $create_cmd
    run a test comand $run
    '''

    def create_cmd(self) -> Expectation:
        @do(NvimIO[Ident])
        def run() -> Do:
            helper, aff, data = yield command_spec_data()
            (s1, ig) = yield vim_test_command.fun().run(helper.component_res(data))
            yield N.from_either(
                s1.data.comp //
                __.commands.head.to_either('no commands') /
                _.ident
            )
        return kn(self.vim, run) == NSuccess(test_ident)

    def run(self) -> Expectation:
        @do(NvimIO[None])
        def run() -> Do:
            helper, aff, data = yield command_spec_data()
            ds = dispatch_state(helper.state, aff)
            yield mock_test_functions()
            (s1, ignore) = yield eval_trans.match(vim_test(RunCommandOptions.cons()).m).run(ds)
            cmd = yield N.from_either(s1.state.data_by_name('command'))
            log = yield N.from_either(cmd.log_by_ident(test_ident))
            return log.read_text()
        return kn(self.vim, run) == NSuccess('arg')


# TODO test empty `ParseOutput`
class TestISpec(DefaultSpec):
    '''run a test command $run
    '''

    def _pre_start(self) -> None:
        self.vim.vars.set_p('components', List('command'))
        super()._pre_start()

    def run(self) -> Expectation:
        self.cmd_sync('MyoStage1')
        mock_test_functions().unsafe(self.vim)
        self.json_cmd_sync('MyoVimTest')
        self.cmd_sync('MyoParse')
        self._wait(.5)
        target = List('  File "<string>", line 1, in <module>', 'RuntimeError: No active exception to reraise')
        @do(NvimIO[List[str]])
        def content() -> Do:
            bufs = yield buffers()
            buf = yield N.from_maybe(bufs.lift(1), 'scratch buffer wasn\'t opened')
            yield buffer_content(buf)
        return kn(self.vim, content).must(contain(have_lines(target)))


__all__ = ('TestSpec',)
