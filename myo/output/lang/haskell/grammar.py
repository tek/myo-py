grammar = '''
start: (specific | generic)+
specific.5: dotted | undotted
generic.1: any+
dotted.5: dot (foundreq1 | foundreq2 | notypeclass | notinscope | genericdot)
undotted.1: notinscope

foundreq1.5: "Couldn't match" "expected" "type" qname "with" "actual type"? qname
foundreq2.5: "Couldn't match" "type" qname "with" "actual type"? qname
notypeclass.5: "No instance for" parenstype "arising from" words qname
notinscope.5: "Variable not in scope:" name "::" type+
genericdot.1: any+
dot: "•"
qname: sql qnamedata sqr
qnamedata: /[^’]+/
parenstype: "(" (parenstypename+) ")"
parenstypename: parenstype | parenstypenamequal | name
parenstypenamequal: name "." parenstypename
name: WORD
words: WORD+
type: /.+/
sql: "‘"
sqr: "’"
any: (/[^•]+/ | NEWLINE)
%import common.NEWLINE
%import common.WS
%import common.WORD
%ignore WS
%ignore NEWLINE
'''

__all__ = ('grammar',)
