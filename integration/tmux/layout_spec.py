from kallikrein import k, Expectation

from integration._support.tmux import TmuxSpec


class LayoutSpec(TmuxSpec):
    '''
    test $test
    '''

    def test(self) -> Expectation:
        return k(1) == 1


__all__ = ('LayoutSpec',)
