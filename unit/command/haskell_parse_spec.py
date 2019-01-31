from kallikrein import k, Expectation
from kallikrein.matchers.length import have_length
from kallikrein.matchers.either import be_right
from kallikrein.matchers.lines import have_lines

from test.command import command_spec_test_config

from amino import Lists, do, Do, List
from amino.test.spec import SpecBase

from ribosome.nvim.io.state import NS
from ribosome.test.unit import unit_test

from myo.output.parser.haskell import haskell_parser
from myo.output.parser.base import parse_events
from myo.output.data.report import ParseReport, format_report
from myo.components.command.compute.output import report_line_number, parse_report
from myo.config.plugin_state import MyoState
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.components.command.compute.parse_handlers import ParseHandlers
from myo.output.configs import haskell_config

output = '''
/path/to/file.hs:38:13: error:
    • No instance for (TypeClass Data)
        arising from a use of ‘foobar’
    • In a stmt of a 'do' block: foo <- bar baz
      In the expression:
        do { foo <- bar baz;
             (a, b, c) <- foo bar;
             .... }

/path/to/file.hs:38:13: error:
    • No instance for (TypeClass
        Data.Type (Monad Data))
        arising from a use of ‘blurb’

Progress 0/2            /path/to/file.hs:43:3: error:
Progress 0/2                Variable not in scope:
Progress 0/2                  doSomething :: TypeA -> Monad a0
Progress 0/2            
Progress 0/2            Progress 1/2

/path/to/file.hs:5:5: error:
    • Couldn't match expected type ‘StateT
                                      (ReaderT
                                         (GHC.Conc.Sync.TVar Data))
                                      a0’
                  with actual type ‘t0 Data1
                                    -> StateT (ReaderT e0) ()’
    • Probable cause: ‘mapM_’ is applied to too few arguments
      In a stmt of a 'do' block: mapM_ end
      In the expression:
        do a <- start
           mapM_ end
      In an equation for ‘execute’:
          execute
            = do a <- start
                 mapM_ end
  |
5 |   mapM_ end
  |   ^^^^^^^^^


  /path/to/file.hs:19:3: error:
    Variable not in scope: asdf :: Monad a
   |
19 |   asdf
   |   ^^^^

    /path/to/file.hs:31:3: error:
        • Variable not in scope:
            mapE
              :: t1 -> t2
              -> t3
        • maybe you meant: x
       |
    31 |   mapE x
       |   ^^^^

    /path/to/file.hs:35:3: error:
        Variable not in scope: run :: a -> b
       |
    35 |   run $ y
       |   ^^^
'''
clean_lines = Lists.lines(output)


@do(NS[MyoState, ParseReport])
def cons_report(lines: List[str]) -> Do:
    events = yield NS.e(parse_events(haskell_parser, lines))
    config = yield NS.e(ParseHandlers.from_config(haskell_config.parse))
    output = ParsedOutput(config, events, events)
    yield parse_report(output)


@do(NS[MyoState, Expectation])
def error_spec() -> Do:
    report = yield cons_report(clean_lines)
    return k(report.lines).must(have_length(10))


@do(NS[MyoState, Expectation])
def line_number_spec() -> Do:
    report = yield cons_report(clean_lines)
    return k(report_line_number(1)(report)).must(be_right(3))


target_report = '''/path/to/file.hs  38
  !instance: foobar
  TypeClass Data
/path/to/file.hs  38
  !instance: blurb
  TypeClass Data.Type (Monad Data)
/path/to/file.hs  43
  Variable not in scope: doSomething :: TypeA -> Monad a0
/path/to/file.hs  5
  type mismatch
  t0 Data1 -> StateT (ReaderT e0) ()
  StateT (ReaderT (GHC.Conc.Sync.TVar Data)) a0
/path/to/file.hs  19
  Variable not in scope: asdf :: Monad a
/path/to/file.hs  31
  Variable not in scope: mapE :: t1 -> t2 -> t3
/path/to/file.hs  35
  Variable not in scope: run :: a -> b'''


@do(NS[MyoState, Expectation])
def report_spec() -> Do:
    report = yield cons_report(clean_lines)
    formatted = format_report(report)
    return k(formatted).must(have_lines(target_report))


class HaskellParseSpec(SpecBase):
    '''
    parse a haskell error $error
    find an output line for an event $event
    format a report $report
    '''

    def error(self) -> Expectation:
        return unit_test(command_spec_test_config, error_spec)

    def event(self) -> Expectation:
        return unit_test(command_spec_test_config, line_number_spec)

    def report(self) -> Expectation:
        return unit_test(command_spec_test_config, report_spec)


__all__ = ('HaskellParseSpec',)
