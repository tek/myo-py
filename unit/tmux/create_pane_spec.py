from kallikrein import k, Expectation

from amino.test.spec import SpecBase


class CreatePaneSpec(SpecBase):
    '''
    create a pane $create
    '''

    def create(self) -> Expectation:
        return k(1) == 1


__all__ = ('CreatePaneSpec',)
