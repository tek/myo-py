from myo.output.config import LangConfig
from myo.output.lang.python.report import python_report
from myo.output.format.path import project_relative_path
from myo.output.lang.python.syntax import python_syntax
from myo.output.lang.scala.report import scala_report
from myo.output.lang.scala.syntax import scala_syntax
from myo.output.lang.python.first_error import python_first_error

from amino import List
from amino.util.tpe import qualified_name


python_config = LangConfig.cons(
    'python',
    output_reporter=qualified_name(python_report),
    output_syntax=qualified_name(python_syntax),
    output_first_error=qualified_name(python_first_error),
)

scala_config = LangConfig.cons(
    'scala',
    output_reporter=qualified_name(scala_report),
    output_syntax=qualified_name(scala_syntax),
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
