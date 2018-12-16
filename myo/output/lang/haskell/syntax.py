from amino import List

from ribosome.nvim.io.state import NS
from ribosome.nvim.syntax.syntax import Syntax
from ribosome.nvim.syntax.expr import SyntaxMatch, HiLink, SyntaxLiteral, SyntaxRegion, Highlight

from myo.components.command.compute.tpe import CommandRibosome
from myo.output.lang.scala.report import col_marker

error_end = f'\ze.*\(\|{col_marker}\)'
foundreqHead = 'type mismatch'
noInstanceMarker = '\s*!instance:'
notInScopeMarker = 'Variable not in scope:'
haskell_include = SyntaxLiteral('syntax include @haskell syntax/haskell.vim')
location = SyntaxMatch.cons('MyoLocation', '^.*.*$', 'skipwhite', 'skipnl',
                            contains='MyoPath,MyoLineNumber', nextgroup='MyoHsError')
path = SyntaxMatch.cons('MyoPath', '^.*\ze\( .*$\)\@=', 'contained', containedin='MyoLocation')
line_number = SyntaxMatch.cons('MyoLineNumber', '\( \)\@<=\zs\d\+\ze', 'contained', containedin='MyoLocation')
# function = SyntaxMatch.cons('MyoFunction', '\( \d\+ \)\@<=\zs.*$', 'contained', containedin='MyoLocation')
error = SyntaxRegion.cons(
    'MyoHsError',
    '^',
    error_end,
    'contained',
    'skipwhite',
    'skipnl',
    contains='MyoHsFoundReq,MyoHsNoInstance,MyoHsNotInScope',
)
foundreq = SyntaxRegion.cons(
    'MyoHsFoundReq',
    foundreqHead,
    error_end,
    'contained',
    'skipwhite',
    'skipnl',
    contains='MyoHsFound',
)
found = SyntaxMatch.cons('MyoHsFound', '^.*$', 'contained', 'skipnl', nextgroup='MyoHsReq')
req = SyntaxMatch.cons('MyoHsReq', '^.*$', 'contained')
code = SyntaxMatch.cons('MyoHsCode', '.*', 'contained', contains='@haskell')
noInstance = SyntaxRegion.cons(
    'MyoHsNoInstance',
    noInstanceMarker,
    error_end,
    'contained',
    contains='MyoHsNoInstanceHead',
)
noInstanceHead = SyntaxMatch.cons(
    'MyoHsNoInstanceHead',
    f'\s*{noInstanceMarker} .*$',
    'contained',
    'skipnl',
    contains='MyoHsNoInstanceBang',
    nextgroup='MyoHsNoInstanceDesc',
)
noInstanceBang = SyntaxMatch.cons('MyoHsNoInstanceBang', '!', 'contained', nextgroup='MyoHsNoInstanceKw')
noInstanceKw = SyntaxMatch.cons(
    'MyoHsNoInstanceKw',
    'instance\ze:',
    'contained',
    'skipwhite',
    nextgroup='MyoHsNoInstanceTrigger',
)
noInstanceTrigger = SyntaxMatch.cons('MyoHsNoInstanceTrigger', '.*', 'contained')
noInstanceDesc = SyntaxMatch.cons('MyoHsNoInstanceDesc', '.*', 'contained', 'skipnl', nextgroup='MyoLocation')
notInScope = SyntaxRegion.cons(
    'MyoHsNotInScope',
    notInScopeMarker,
    error_end,
    'contained',
    contains='MyoHsNotInScopeHead',
)
notInScopeHead = SyntaxMatch.cons(
    'MyoHsNotInScopeHead',
    f'\s*{notInScopeMarker}',
    'skipnl',
    'contained',
    nextgroup='MyoHsCode',
)

hl_path = HiLink('MyoPath', 'Directory')
hl_line_number = HiLink('MyoLineNumber', 'Directory')
hl_foundreq = HiLink('MyoHsFoundReq', 'Title')
hl_found = HiLink('MyoHsFound', 'Error')
hl_bang = HiLink('MyoHsNoInstanceBang', 'Error')
hl_kw = HiLink('MyoHsNoInstanceKw', 'Directory')
hl_notinscope = HiLink('MyoHsNotInScopeHead', 'Error')

hi_req = Highlight.cons('MyoHsReq', ctermfg=2, guifg='#719e07')
hi_trigger = Highlight.cons('MyoHsNoInstanceTrigger', ctermfg=3)

syntax = Syntax(
    List(haskell_include, location, path, line_number, error, foundreq, found, req, code, noInstance, noInstanceHead,
         noInstanceBang, noInstanceKw, noInstanceTrigger, noInstanceDesc, notInScope, notInScopeHead),
    List(hi_req, hi_trigger),
    List(hl_path, hl_line_number, hl_foundreq, hl_found, hl_bang, hl_kw, hl_notinscope),
)


def haskell_syntax() -> NS[CommandRibosome, Syntax]:
    return NS.pure(syntax)


__all__ = ('haskell_syntax',)
