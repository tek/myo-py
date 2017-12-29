from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import List, Map

from ribosome.test.integration.run import DispatchHelper
from ribosome.config import Config


config = Config.cons(
    'compo',
    components=Map(command='command'),
    core_components=List(),
    default_components=List('command'),
)


class ComponentSpec(SpecBase):
    '''
    test $test
    '''

    def test(self) -> Expectation:
        helper = DispatchHelper.cons(config, 'command')
        r = helper.loop('command:load_history', args=(5,)).unsafe(helper.vim)
        return k(1) == 1


__all__ = ('ComponentSpec',)
