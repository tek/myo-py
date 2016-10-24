from ribosome import NvimFacade

from amino import _, L, List, Right, Left, __


def vimtest_position(vim: NvimFacade):
    fn_mod = vim.vars('g:test#filename_modifier') | ':.'
    line, col = vim.window.cursor
    return vim.call('expand', '%{}'.format(fn_mod)) / (
        lambda f: dict(file=f, line=line, col=col)
    )


def assemble_vim_test_line(vim: NvimFacade):
    def build(exe, args):
        fmt = lambda a: '{} {}'.format(exe, a)
        return List.wrap(args) / fmt
    def args(runner, pos):
        ''' build_position and build_args return lists
        '''
        exe = vim.call('test#{}#executable'.format(runner))
        bpos = vim.call('test#base#build_position', runner, 'nearest', pos)
        args = bpos // L(vim.call)('test#base#build_args', runner, _)
        return ((args / List.wrap) & exe).map2(__.cons(_)) / _.join_tokens
    def runner(pos):
        chk_res = lambda a: (
            Right(a) if isinstance(a, str) else Left('no runner found'))
        return (
            vim.call('test#determine_runner', pos['file']) //
            chk_res //
            L(args)(_, pos)
        )
    return vimtest_position(vim) // runner

__all__ = ('assemble_vim_test_line',)
