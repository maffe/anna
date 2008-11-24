import math
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

def _all_equal(*args):
    '''Returns True if all arguments are equal.'''
    print args
    args = iter(args)
    x = args.next()
    for e in args:
        if x != e:
            return False
    return True

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

    def equality(self, (tag, start, stop, subtags), buffer):
        return _all_equal(dispatchList(self, subtags, buffer))

    def _reduce_infix(self, (tag, start, stop, subtags), buffer, assoc='left'):
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

    _left_assoc = lambda s, *x: s._reduce_infix(assoc='left', *x)
    _right_assoc = lambda s, *x: s._reduce_infix(assoc='right', *x)
    addsub = muldiv = _left_assoc
    pow = _right_assoc

    def naturalexp(self, (tag, start, stop, subtags), buffer):
        return reduce(operator.mul, dispatchList(self, subtags, buffer))

    def unumber(self, (tag, start, stop, subtags), buffer):
        return float(buffer[start:stop])

    equal_oper = lambda *x: operator.eq
    add_oper = lambda *x: operator.add
    sub_oper = lambda *x: operator.sub
    mul_oper = lambda *x: operator.mul
    div_oper = lambda *x: operator.truediv
    pow_oper = lambda *x: operator.pow

    pos_sign = lambda *x: 1
    neg_sign = lambda *x: -1

    naturalexpchar = lambda *x: math.e

def process(expr, debug=False, parser=MyParser()):
    if debug:
        import pprint
        (x, parser.buildProcessor) = (parser.buildProcessor, lambda *x: None)
        pprint.pprint(parser.parse(expr))
        parser.buildProcessor = x
    success, res = parser.parse(expr)
    print res if success else 'Failed to parse.'

def main():
    if '-h' in sys.argv or '--help' in sys.argv:
        print 'Usage:', sys.argv[0], '<expression>'
        sys.exit(0)
    while 1:
        sys.stderr.write('> ')
        sys.stderr.flush()
        process(raw_input(), '-d' in sys.argv)

if __name__ == '__main__':
    main()
