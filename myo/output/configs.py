from myo.output.config import LangConfig
from myo.output.lang.python.report import python_report
from myo.output.format.path import project_relative_path

from amino import List
from amino.util.tpe import qualified_name


python_config = LangConfig.cons(
    'python',
    output_reporter=qualified_name(python_report),
)

scala_config = LangConfig.cons(
    'scala',
)

default_lang_configs = List(
    python_config,
    scala_config,
)

global_config_defaults = LangConfig.cons(
    'global',
    output_path_formatter=qualified_name(project_relative_path),
)

__all__ = ('default_lang_configs', 'global_config_defaults',)
