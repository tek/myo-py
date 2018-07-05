from amino import List, Nil

from ribosome.nvim.io.state import NS
from ribosome.nvim.syntax.syntax import Syntax
from ribosome.nvim.syntax.expr import SyntaxMatch, HiLink, SyntaxLiteral, SyntaxRegion

from myo.components.command.compute.tpe import CommandRibosome
from myo.output.lang.scala.report import col_marker, found_marker, separator_marker, foundreq_separator, req_marker

def conceal(name: str, pattern: str, *a: str, **kw: str) -> SyntaxMatch:
    return SyntaxMatch.cons(
        name,
        pattern,
        'conceal',
        'contained',
        *a,
        **kw,
    )

error_end = f'\ze.*\(\|{col_marker}\)'
scala_include = SyntaxLiteral('syntax include @scala syntax/scala.vim')
location = SyntaxMatch.cons(
    'MyoLocation',
    '^.*.*$',
    'skipwhite',
    'skipnl',
    contains='MyoPath,MyoLineNumber',
    nextgroup='MyoError',
)
path = SyntaxMatch.cons('MyoPath', '^.*\ze\( .*$\)\@=', 'contained', containedin='MyoLocation')
line_number = SyntaxMatch.cons('MyoLineNumber', '\( \)\@<=\zs\d\+\ze', 'contained', containedin='MyoLocation')
error = SyntaxRegion.cons(
    'MyoError',
    '^.',
    error_end,
    'contained',
    'skipwhite',
    'skipnl',
    nextgroup='MyoCode',
    contains='MyoSplain,MyoSplainFoundReq',
)
code_line = SyntaxMatch.cons('MyoCode', '.*', 'contained', contains='@scala,MyoColMarker')
col_marker_conceal = conceal('MyoColMarker', col_marker, nextgroup='MyoCol')
col = SyntaxMatch.cons('MyoCol', '.', 'contained')
splain = SyntaxRegion.cons(
    'MyoSplain',
    '\s*!I',
    error_end,
    'contained',
    'skipwhite',
    'skipnl',
    nextgroup='MyoCode',
    contains='MyoSplainParam,MyoSplainCandidate',
)
splain_param = SyntaxMatch.cons(
    'MyoSplainParam',
    '^\s*!I.*',
    'contained',
    containedin='MyoSplain',
    contains='MyoSplainParamMarker',
)
splain_param_marker = SyntaxMatch.cons(
    'MyoSplainParamMarker',
    '!I',
    'contained',
    nextgroup='MyoSplainParamName',
    contains='MyoSplainParamMarkerBang',
)
splain_param_marker_bang = SyntaxMatch.cons(
    'MyoSplainParamMarkerBang',
    '!',
    'contained',
    nextgroup='MyoSplainParamMarkerI',
)
splain_param_marker_i = SyntaxMatch.cons(
    'MyoSplainParamMarkerI',
    'I',
    'contained',
    'skipwhite',
    nextgroup='MyoSplainParamName',
)
splain_param_name = SyntaxMatch.cons(
    'MyoSplainParamName',
    '[^:]\+\ze:',
    'contained',
    nextgroup='MyoSplainParamType',
)
splain_param_type = SyntaxRegion.cons(
    'MyoSplainParamType',
    '.',
    f'\ze.*\(invalid because\|{col_marker}\)',
    'contained',
)
splain_candidate = SyntaxMatch.cons(
    'MyoSplainCandidate',
    '\S\+\ze invalid because',
    'contained',
    containedin='MyoSplain',
)
splain_foundreq = SyntaxMatch.cons(
    'MyoSplainFoundReq',
    f'^.*{found_marker}.\{{-}}{separator_marker}{foundreq_separator}.\{{-}}{req_marker}.*$',
    'contained',
    contains='MyoSplainFound,MyoSplainReq',
)
splain_found = SyntaxMatch.cons(
    'MyoSplainFound',
    f'{found_marker}.\{{-}}{separator_marker}',
    'contained',
    contains='MyoSplainFoundReqMarker',
    nextgroup='MyoSplainReq',
)
splain_req = SyntaxMatch.cons(
    'MyoSplainReq',
    f'{foundreq_separator}\zs.\{{-}}\ze{req_marker}',
    'contained',
    nextgroup='MyoSplainFoundReqMarker',
)
splain_req_marker_conceal = conceal('MyoSplainFoundReqMarker', f'{found_marker}\|{separator_marker}\|{req_marker}')

hl_error = HiLink('MyoError', 'Error')
hl_path = HiLink('MyoPath', 'Directory')
hl_line_number = HiLink('MyoLineNumber', 'Directory')
hl_col = HiLink('MyoCol', 'Search')
hl_splain_param_marker_bang = HiLink('MyoSplainParamMarkerBang', 'Error')
hl_splain_param_marker_i = HiLink('MyoSplainParamMarkerI', 'Directory')
hl_splain_param_name = HiLink('MyoSplainParamName', 'Type')
hl_splain_param_type = HiLink('MyoSplainParamType', 'Statement')
hl_splain_candidate = HiLink('MyoSplainCandidate', 'Error')
hl_splain_found_req = HiLink('MyoSplainFoundReq', 'Normal')
hl_splain_found = HiLink('MyoSplainFound', 'Error')
hl_splain_req = HiLink('MyoSplainReq', 'Statement')

syntax = Syntax(
    List(scala_include, location, path, line_number, error, code_line, col_marker_conceal, col, splain, splain_param,
         splain_param_marker, splain_param_marker_bang, splain_param_marker_i, splain_param_name, splain_param_type,
         splain_candidate, splain_foundreq, splain_found, splain_req, splain_req_marker_conceal),
    Nil,
    List(hl_error, hl_path, hl_line_number, hl_col, hl_splain_param_marker_bang, hl_splain_param_marker_i,
         hl_splain_param_name, hl_splain_param_type, hl_splain_candidate, hl_splain_found, hl_splain_req),
)


def scala_syntax() -> NS[CommandRibosome, Syntax]:
    return NS.pure(syntax)


__all__ = ('scala_syntax',)
