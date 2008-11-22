import operator
import os
import sys

from simpleparse.parser import Parser
from simpleparse.dispatchprocessor import dispatch, dispatchList, \
                                        DispatchProcessor
from simpleparse.common import numbers

DEFINITIONS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        'calc.def')

class MyParser(Parser):
    def __init__(self, root='expression', *args):
        Parser.__init__(self, open(DEFINITIONS, 'r').read(), root, *args)

    def buildProcessor(self):
        return MyProcessor()

    def parse(self, txt, *args, **kwargs):
        success, children, next = Parser.parse(self, txt, *args, **kwargs)
        if not (success and next == len(txt)):
            return (False, 0.0)
        else:
            return (True, children[0])

class MyProcessor(DispatchProcessor):
    def atomicexpr(self, (tag, start, stop, subtags), buffer):
        l = dispatchList(self, subtags, buffer)
        if len(l) == 1:
            return l[0]
        else:
            return l[0] * l[1]

    def addsub(self, (tag, start, stop, subtags), buffer):
        expr = dispatchList(self, subtags, buffer)
        t1 = expr.pop(0)
        while expr:
            op = expr.pop(0)
            t2 = expr.pop(0)
            t1 = op(t1, t2)
        return t1

    muldiv = addsub

    _opers = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            'x': operator.mul,
            '/': operator.truediv,
            }
    def _choose_oper(self, (tag, start, stop, subtags), buffer):
        return self._opers[buffer[start].lower()]
    addsub_oper = _choose_oper
    muldiv_oper = _choose_oper

    def sign(self, (tag, start, stop, subtags), buffer):
        return 1 - 2 * (buffer[start] == '-')

    # Package simpleparse.common.numbers.
    int = numbers.IntInterpreter()
    int_unsigned = int
    hex = numbers.HexInterpreter()
    float = numbers.FloatInterpreter()
    float_floatexp = numbers.FloatFloatExpInterpreter()
    binary_number = numbers.BinaryInterpreter()
    imaginary_number = numbers.ImaginaryInterpreter()
    def number(self, (tag, start, stop, subtags), buffer):
        return dispatch(self, subtags[0], buffer)
    number_full = number

def main():
    pars = MyParser()
    if len(sys.argv) < 2:
        sys.exit('Usage: %s <expression>' % sys.argv[0])
    expr = ''.join(sys.argv[1:])
    success, res = pars.parse(expr)
    if not success:
        sys.exit('Failed to parse.')
    else:
        print res

if __name__ == '__main__':
    main()
