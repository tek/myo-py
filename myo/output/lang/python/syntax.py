from amino import List, Nil

from ribosome.nvim.io.state import NS
from ribosome.nvim.syntax.syntax import Syntax
from ribosome.nvim.syntax.expr import SyntaxMatch, HiLink, SyntaxLiteral

from myo.components.command.compute.tpe import CommandRibosome

python_include = SyntaxLiteral('syntax include @python syntax/python.vim')
location = SyntaxMatch.cons('MyoLocation', '^.*.*$', 'skipwhite', 'skipnl',
                            contains='MyoPath,MyoLineNumber,MyoFunction', nextgroup='MyoCode')
path = SyntaxMatch.cons('MyoPath', '^.*\ze\( .*$\)\@=', 'contained', containedin='MyoLocation')
line_number = SyntaxMatch.cons('MyoLineNumber', '\( \)\@<=\zs\d\+\ze', 'contained', containedin='MyoLocation')
function = SyntaxMatch.cons('MyoFunction', '\( \d\+ \)\@<=\zs.*$', 'contained', containedin='MyoLocation')
error = SyntaxMatch.cons('MyoError', '^\w\+: .*$', contains='MyoException')
code_line = SyntaxMatch.cons('MyoCode', '^    .*$', 'contained', contains='@python')
exception = SyntaxMatch.cons('MyoException', '^\w\+:', 'contained', containedin='MyoError')

hl_error = HiLink('MyoException', 'Error')
hl_path = HiLink('MyoPath', 'Directory')
hl_line_number = HiLink('MyoLineNumber', 'Directory')
hl_function = HiLink('MyoFunction', 'Type')

syntax = Syntax(
    List(location, path, line_number, function, error, code_line, exception, python_include),
    Nil,
    List(hl_error, hl_path, hl_line_number, hl_function),
)


def python_syntax() -> NS[CommandRibosome, Syntax]:
    return NS.pure(syntax)


__all__ = ('python_syntax',)
