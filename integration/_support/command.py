from amino import __, Path, List
from amino.test import temp_dir

from ribosome.record import encode_json, decode_json

from myo.command import Command

from integration._support.base import DefaultSpec


class CmdSpecConf:

    @property
    def _plugins(self):
        return super()._plugins.cat('command')

    @property
    def _last(self):
        return (lambda: self.vim.vars.pd('last_command') // __.get('name').to_either('no name'))

    @property
    def state_dir(self) -> Path:
        return temp_dir('history', 'load', 'state')

    @property
    def history_file(self) -> Path:
        return self.state_dir / 'history.json'

    def write_history(self, data: List[Command]) -> None:
        history = encode_json(data).get_or_raise
        self.history_file.write_text(history)

    def history(self) -> List[Command]:
        return decode_json(self.history_file.read_text()).get_or_raise

    def _set_vars(self):
        super()._set_vars()
        self.vim.vars.set_p('state_dir', str(self.state_dir))


class CmdPluginSpecConf(CmdSpecConf):

    def _create_command(self, name, line, **opt):
        self.json_cmd_sync('MyoShellCommand {}'.format(name), line=line, **opt)
        self._wait(.1)

    def _run_command(self, name, **opt):
        self.json_cmd_sync('MyoRun {}'.format(name), **opt)
        self._wait(.1)


class CmdSpec(CmdPluginSpecConf, DefaultSpec):
    pass

__all__ = ('CmdSpec', 'CmdSpecConf', 'CmdPluginSpecConf')
