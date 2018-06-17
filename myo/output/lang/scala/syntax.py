from amino import List, Nil

from ribosome.nvim.io.state import NS
from ribosome.nvim.syntax.syntax import Syntax
from ribosome.nvim.syntax.expr import SyntaxMatch, HiLink, SyntaxLiteral

from myo.components.command.compute.tpe import CommandRibosome
from myo.output.lang.scala.report import col_marker

scala_include = SyntaxLiteral('syntax include @scala syntax/scala.vim')
location = SyntaxMatch.cons('MyoLocation', '^.*.*$', 'skipwhite', 'skipnl',
                            contains='MyoPath,MyoLineNumber', nextgroup='MyoError')
path = SyntaxMatch.cons('MyoPath', '^.*\ze\( .*$\)\@=', 'contained', containedin='MyoLocation')
line_number = SyntaxMatch.cons('MyoLineNumber', '\( \)\@<=\zs\d\+\ze', 'contained', containedin='MyoLocation')
error = SyntaxMatch.cons('MyoError', '^.*$', 'contained', 'skipwhite', 'skipnl', nextgroup='MyoCode')
code_line = SyntaxMatch.cons('MyoCode', '^  .*$', 'contained', contains='@scala,MyoColMarker')
col_marker_conceal = SyntaxMatch.cons('MyoColMarker', col_marker, 'conceal', 'contained', containedin='MyoCode',
                                      nextgroup='MyoCol')
col = SyntaxMatch.cons('MyoCol', '.', 'contained')

hl_error = HiLink('MyoError', 'Error')
hl_path = HiLink('MyoPath', 'Directory')
hl_line_number = HiLink('MyoLineNumber', 'Directory')
hl_col = HiLink('MyoCol', 'Search')

syntax = Syntax(
    List(scala_include, location, path, line_number, error, code_line, col_marker_conceal, col),
    Nil,
    List(hl_error, hl_path, hl_line_number, hl_col),
)


def scala_syntax() -> NS[CommandRibosome, Syntax]:
    return NS.pure(syntax)


__all__ = ('scala_syntax',)
