from amino import List, Map, Just
from amino.boolean import true

from ribosome.config.component import Component
from ribosome.rpc.api import rpc
from ribosome.util.doc.data import DocBlock

from myo.config.component import MyoComponent
from myo.ui.data.ui_data import UiData
from myo.components.ui.compute.open_pane import open_pane
from myo.components.ui.compute.close_pane import close_pane
from myo.components.ui.compute.minimize_pane import minimize_pane
from myo.components.ui.compute.create_pane import create_pane
from myo.components.ui.compute.init import init
from myo.components.ui.compute.info import ui_info
from myo.components.ui.compute.toggle_pane import toggle_pane
from myo.components.ui.compute.toggle_layout import toggle_layout
from myo.components.ui.compute.kill_pane import kill_pane
from myo.components.ui.compute.focus import focus

create_pane_help = DocBlock.string('''Configure a new pane that can be spawned with `MyoOpenPane`.''')
create_pane_json_help = Map(
    layout='containing layout name',
    ident='name to be used for commands like MyoOpenPane',
    min_size='minimum size integer',
    max_size='maximum size integer',
    fixed_size='fixed size, combination of min and max',
    minimized_size='size after calling MyoMinimizePane',
    weight='amount of growth this pane gets when there is space left above the minimums',
    position='absolute position in the layout',
    minimized='whether to create the pane in minimized state',
)


ui = Component.cons(
    'ui',
    state_type=UiData,
    rpc=List(
        rpc.write(create_pane).conf(json=true, help=create_pane_help, json_help=Just(create_pane_json_help)),
        rpc.write(open_pane).conf(json=true),
        rpc.write(close_pane),
        rpc.write(toggle_pane),
        rpc.write(minimize_pane),
        rpc.write(kill_pane),
        rpc.write(toggle_layout),
        rpc.read(ui_info),
        rpc.read(focus),
    ),
    config=MyoComponent.cons(info=ui_info, init=init),
)

__all__ = ('ui',)
