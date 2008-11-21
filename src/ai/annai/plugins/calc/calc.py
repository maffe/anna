import operator
import os
import sys

from simpleparse.parser import Parser
from simpleparse.dispatchprocessor import dispatch, dispatchList, \
                                        DispatchProcessor

DEFINITIONS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        'calc.def')

class MyParser(Parser):
    def __init__(self, root='expression', *args):
        Parser.__init__(self, open(DEFINITIONS, 'r').read(), root, *args)

    def buildProcessor(self):
        return MyProcessor()

    def parse(self, txt, *args):
        success, children, next = Parser.parse(self, txt, *args)
        if not (success and next == len(txt)):
            return (False, 0.0)
        else:
            return (True, children[0])

class MyProcessor(DispatchProcessor):
    def sexpression(self, (tag, start, stop, subtags), buffer):
        sign = dispatch(self, subtags[0], buffer)
        return dispatch(self, subtags[1], buffer) * sign

    def addsub(self, (tag, start, stop, subtags), buffer):
        expr = dispatchList(self, subtags, buffer)
        t1 = expr.pop(0)
        while expr:
            op = expr.pop(0)
            t2 = expr.pop(0)
            t1 = op(t1, t2)
        return t1

    def muldiv(self, *args):
        return self.addsub(*args)

    def snumber(self, (tag, start, stop, subtags), buffer):
        '''A signed number has two elements: a sign (-1 or +1) and digits.'''
        return operator.mul(*dispatchList(self, subtags, buffer))

    def unumber(self, (tag, start, stop, subtags), buffer):
        return float(buffer[start:stop])

    add_oper = lambda *x: operator.add
    sub_oper = lambda *x: operator.sub
    mul_oper = lambda *x: operator.mul
    div_oper = lambda *x: operator.div
    pos_sign = lambda *x: 1
    neg_sign = lambda *x: -1

def main():
    pars = MyParser()
    if len(sys.argv) < 2:
        sys.exit('Usage: %s <expression>' % sys.argv[0])
    expr = ''.join(sys.argv[1:])
    success, res = pars.parse(expr)
    if not success:
        sys.exit('Failed to parse.')
    else:
        print '%g' % res

if __name__ == '__main__':
    main()
