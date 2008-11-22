import operator
import os
import sys

from simpleparse.parser import Parser
from simpleparse.dispatchprocessor import dispatch, dispatchList, \
                                        DispatchProcessor
from simpleparse.common import numbers
from simpleparse.error import ParserSyntaxError

DEFINITIONS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        'calc.def')

def _reverse_args(func):
    '''Decorator that reverses the order of the arguments to a function.'''
    def newf(*args):
        return func(*reversed(args))
    return newf

class MyParser(Parser):
    def __init__(self, root='expression', *args):
        Parser.__init__(self, open(DEFINITIONS, 'r').read(), root, *args)

    def buildProcessor(self):
        return MyProcessor()

    def parse(self, txt, *args, **kwargs):
        # Easter egg.
        if txt == "2+2": return (True, 5)
        try:
            success, children, next = Parser.parse(self, txt, *args, **kwargs)
        except ParserSyntaxError:
            return (False, 0.0)
        if not (success and next == len(txt)):
            return (False, 0.0)
        else:
            return (True, children[0])

class MyProcessor(DispatchProcessor):
    def satomicexpr(self, (tag, start, stop, subtags), buffer):
        return reduce(operator.mul, dispatchList(self, subtags, buffer))

    def reduce_infix(self, (tag, start, stop, subtags), buffer, assoc='left'):
        '''Reduce a list of tags by their infix operands.

        The assocative argument (left or right) indicates where to start
        reducing. For addition and substraction, you will want to go from left
        to right:

        1 - 2 + 3
        is
        (1 - 2) + 3
        and not
        1 - (2 + 3)

        For exponentiation, it is the other way around:

        1^2^3
        is
        1^(2^3)
        and not
        (1^2)^3

        '''
        i = -1 if assoc == 'right' else 0
        expr = dispatchList(self, subtags, buffer)
        t1 = expr.pop(i)
        while expr:
            op = expr.pop(i)
            t2 = expr.pop(i)
            # The order in which tags are popped is inverted, so t1 becomes t2
            # and vice-versa. The operator does not expect this.
            if assoc == 'right':
                t1, t2 = t2, t1
            # Apply the infix operand to the two surrounding tags.
            t1 = op(t1, t2)
        return t1

    _left_assoc = lambda s, *x: s.reduce_infix(assoc='left', *x)
    _right_assoc = lambda s, *x: s.reduce_infix(assoc='right', *x)
    addsub = muldiv = equality = _left_assoc
    exponent = _right_assoc

    def unumber(self, (tag, start, stop, subtags), buffer):
        return float(buffer[start:stop])

    equal_oper = lambda *x: operator.eq
    add_oper = lambda *x: operator.add
    sub_oper = lambda *x: operator.sub
    mul_oper = lambda *x: operator.mul
    div_oper = lambda *x: operator.truediv
    expo_oper = lambda *x: operator.pow

    pos_sign = lambda *x: 1
    neg_sign = lambda *x: -1

def main():
    pars = MyParser()
    if len(sys.argv) < 2:
        sys.exit('Usage: %s <expression>' % sys.argv[0])
    debug = '-d' in sys.argv
    if debug:
        sys.argv.remove('-d')
    expr = ''.join(sys.argv[1:])
    if debug:
        import pprint
        (x, pars.buildProcessor) = (pars.buildProcessor, lambda *x: None)
        pprint.pprint(pars.parse(expr))
        pars.buildProcessor = x
    success, res = pars.parse(expr)
    if not success:
        sys.exit('Failed to parse.')
    else:
        print res

if __name__ == '__main__':
    main()
