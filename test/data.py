from typing import Any

from amino.lenses.lens import lens

from ribosome.nvim.io.state import NS
from ribosome.data.plugin_state import PS


def update_data(component: type, **data: Any) -> NS[PS, None]:
    return NS.modify(lens.component_data.Get(component, component.cons()).modify(lambda a: a.copy(**data)))


__all__ = ('update_data',)
