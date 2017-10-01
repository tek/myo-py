from ribosome.settings import PluginSettings, state_dir_help_default

state_dir_help = f'''{state_dir_help_default}
Stored data consists of:
* command history
* last test command line
* last shell used for testing
* layout state
'''


class ProteomeSettings(PluginSettings):

    def __init__(self) -> None:
        super().__init__('proteome', state_dir_help)

__all__ = ('ProteomeSettings',)
