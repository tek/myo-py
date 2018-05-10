from amino import do, List, Do

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.function import define_function


@do(NvimIO[None])
def mock_test_functions() -> Do:
    yield define_function('MyoTestDetermineRunner', List('file'), f'return "python"')
    yield define_function('MyoTestExecutable', List('runner'), f'return "python"')
    yield define_function('MyoTestBuildPosition', List('runner', 'pos'), f'return ["-c", "raise Exception(1)"]')
    yield define_function('MyoTestBuildArgs', List('runner', 'args'), f'return a:args')


__all__ = ('mock_test_functions',)
