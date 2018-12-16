grammar = '''
start: (specific | generic)+
specific.5: dotted
generic.1: any+
dotted: dot (foundreq | notypeclass | genericdot)

foundreq.5: "Couldn't match expected type" qname "with actual type" qname
notypeclass.5: "No instance for" parenstype "arising from" words qname
genericdot.1: any+
dot: "•"
qname: sql qnamedata sqr
qnamedata: /[^’]+/
parenstype: "(" name name ")"
name: WORD
words: WORD+
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
