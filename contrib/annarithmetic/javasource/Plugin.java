/*
 * Annarithmetic
 * Author: Lucas moeskops
 * Created: 15-01-2008
 * Last change: 21-01-2008 by Hraban Luyat
 */

package annarithmetic;

import java.util.Iterator;
import java.util.LinkedList;
import java.util.Vector;

public class Plugin {    
    private static String[] operators = {"=|<|>|<=|>=",
    									 "\\+|-",
    									 "\\*|/|%",
    									 "\\^"};
   
    /*
    private Ar_Constant[] constants;
    
    public Plugin() {
        initializeConstants();
    }
*/
    public String usage() {
        return "Annarithmetics help\n" +
            "-------------------\n" +
            "enter an expression to evaluate it\n" +
            "\n" +
            "Annarithmetics functions\n" +
            "------------------------\n" +
            "sqrt\t1\tCalculate squareroot of argument\n" +
            "round\t1\tRound argument\n" +
            "round\t2\tRound argument by precision\n" +
            "\n" +
            "Annarithmetics operators\n" +
            "------------------------\n" +
            "+\tAdd\n" +
            "-\tSubstract\n" +
            "*\tMultiply\n" +
            "/\tDivide\n" +
            "^\tExponentiate\n" +
            "=\tReturns 1 if arguments are equal, else 0\n" +
            ">\tReturns 1 if left arguments greater than right argument, else 0\n" +
            "<\tReturns 1 if left arguments less than right argument, else 0\n" +
            ">=\tReturns 1 if left arguments greater than or equal to right argument, else 0\n" +
            "<=\tReturns 1 if left arguments less than or equal to right argument, else 0";
    }
  /*  
    private void initializeConstants() {
        constants = new Ar_Constant[2];
        constants[0] = new Ar_Constant("pi", Math.PI);
        constants[1] = new Ar_Constant("e", Math.E);
    }
    
    private String replaceConstants(String s) {
        int i, j;
        
        /* Add braces to make sure no constants at first or last position. */ /*
        s = "(" + s + ")";
        
        /* Replace constants. */ /*
        for (i = 0; i < constants.length; i++) {
            j = 0;
            while ((j = s.indexOf(constants[i].getName(), j)) >= 0 &&
                    !Character.isLetter(s.charAt(j - 1)) && 
                    !Character.isLetter(s.charAt(j + constants[i].getName().length()))) {
                s = s.substring(0, j) + "(" +
                    String.valueOf(constants[i].getValue()) + ")" + 
                    s.substring(j + constants[i].getName().length());
            }
        }
        return s.substring(1, s.length() - 1);
    }
*/
    public String processMessage(String s) {    	
    	int l;
    	/* Preprocessing. */
    	
    	if (s.equals("what is 2+2?") || s.equals("2+2"))
        	return "5";
    	
    	s.replaceAll(" ", "");
    	
    	//TODO: fix constants
    	//s = replaceConstants(s);
        
    	/* TODO: preprocess variables. */
    	
    	do {
    		l = s.length();
    		s = s.replaceAll("--", "\\+");
    		s = s.replaceAll("\\+\\+", "\\+");
    		s = s.replaceAll("-\\+", "-");
        	s = s.replaceAll("\\+-", "-");
    	} while (l != s.length());
    	
    	
    	
    	try {
			Expression e = new Expression(s);
			e.evaluate();
			return e.toString();
		} catch (InvalidInputException iie) {
			iie.printStackTrace();
			return "";
		} catch (Exception e) {
			e.printStackTrace();
			return "";
		}
    }
/*
    private String evaluateExpression(Expression e) throws InvalidInputException, InvalidUsageException {
        char c;
        int i, j, k;
        String tmp;
        
        while (true) {
            /* The most important elements are braces. */ /*
            i = j = k = s.indexOf("(");
            if (i >= 0) {
                /* Find closing brace. */ /*
                do {
                    j = s.indexOf(")", j + 1);
                    i = s.indexOf("(", i + 1);
                } while (j >= 0 && i >= 0 && i < j);
                i = k; /* Reset i. */ /*
                if (j < 0) {
                    /* Assume whole rest of string belongs to opening brace. */ /*
                    j = s.length();
                    s += ")";
                }
                
                /* Check if the braces belong to a function. */ /*
                while (k - 1 >= 0) {
                    c = s.charAt(k - 1);
                    if (!Character.isLetterOrDigit(c))
                        break;
                    k--;
                }
                if (k != i) {
                    /* The braces belong to a function. The function name just found might
                     * start with a digit, which is not possible. This piece should therefore
                     * not be counted as function name. */ /*
                    while (k < i) {
                        c = s.charAt(k);
                        if (!Character.isDigit(c))
                            break;
                        k++;
                    }
                    if (k == i) {
                        /* After all not a function. Now further parse the inner string.*/ /*
                        s = s.substring(0, i) + 
                            parseString(s.substring(i + 1, j)) + 
                            s.substring(j + 1);
                    } else {
                        /* Retrieve and evaluate the function. */ /*
                        tmp = s.substring(k, i); /* function name */ /*
                        s = s.substring(0, k) + 
                            evaluateFunction(tmp, s.substring(i + 1, j)) + 
                            s.substring(j + 1);
                    }
                } else {
                    /* The braces were not part of a function. Now further parse the inner string. */ /*
                    s = s.substring(0, i) + 
                        parseString(s.substring(i + 1, j)) + 
                        s.substring(j + 1);
                }
            } else {
                /* No more braces. */ /*
                return evaluateArithmetic(s);
            }
        }
    }
  /* 
    private String readArguments(String s) {
    	char c;
    	int idx = 0, l = s.length(), tmpidx, maxidx, maxtype;
    	LinkedList<Argument> arguments = new LinkedList<Argument>();
    	
    	while (idx < l) {
    		//c = s.charAt(idx);
    		
    		tmpidx = idx;
    		while (Argument.possibleReal(s.substring(idx, ++tmpidx)));
    		maxidx = tmpidx;
    		maxtype = 0;
    		
    		tmpidx = idx + 1;
    		while (Argument.isVariable(s.substring(idx, ++tmpidx)));
    		if (tmpidx > maxidx) {
    			maxidx = tmpidx;
    			maxtype = 1;
    		}
    		
    		tmpidx = idx + 1;
    		while (Argument.possibleFunction(s.substring(idx, ++tmpidx)) && !Argument.isFunction(s.substring(idx, tmpidx)));
    		if (tmpidx > maxidx) {
    			maxidx = tmpidx;
    			maxtype = 2;
    		}
    		
    		idx = maxidx;
    		
    		/* TODO: continue this function!!!! */ /*
    	}
    		
    		
    		if (Character.isLetter(c)) {
    			/* Possibilities: function, variable */ /*
    		}
    	}	
    }
/*
    private String evaluateArithmetic(String argument) throws InvalidInputException {
    	String output;
    	
    	output = evaluateArithmetic(argument, 0);
    	System.out.println("evaluateArithmetic: " + argument + " -> " + output);
    	
    	return output;
    }
    /*
    private String evaluateArithmetic(String argument, int ops_level) {
    	int i, j;
        String s, t, answer;
        String[] arguments;
        
        if (ops_level >= operators.length)
        	return argument;
        
        arguments = argument.split(operators[ops_level]);        
        
        
        
        /* Evaluate each argument arithmetically */
//        for (i = 0; i < arith_ops.length; i++) {
            /* Test if operator occurs in argument. */
//            j = argument.lastIndexOf(arith_ops[i]);
//            if (j >= 0) {
                /* Make sure the operator is surrounded by digits. */
//                if ((j > 0 && !Character.isDigit(argument.charAt(j - 1))) ||
//                  (j < argument.length() - 1 - arith_ops[i].length() 
//                    && !Character.isDigit(argument.charAt(j + arith_ops[i].length()))))
//                    continue;
                
                /* Evaluate the arguments. */
//                s = evaluateArithmetic(argument.substring(0, j));
//              t = evaluateArithmetic(argument.substring(j + arith_ops[i].length()));
                
                /* Exception for minus, because of possible negative values. */
//                if (arith_ops[i].equals("-") && s.length() == 0)
//                    continue;
                
                /* Evaluate the operation. */
 //               answer = evaluateOperation(i, s, t);
 //               if (answer.endsWith(".0"))
 //               	answer = answer.substring(0, answer.length() - 2);
 //               return answer;
//            }
 //       }/*
        //return "";//argument;
        /*
    }
    */
    /*
    private String evaluateFunction(String function, String argument) throws InvalidInputException, InvalidUsageException {
        double answer;
        double[] args;
        int i = 0;
        String[] s_args = argument.split(",");
        
        /* Get the arguments. */ /*
        args = new double[s_args.length];
        try {
            for (i = 0; i < args.length; i++)
                args[i] = Double.parseDouble(parseString(s_args[i]));
        } catch (Exception e) {
            throw new InvalidInputException("Ongeldige invoer: '" + s_args[i] + "'.");
        }
        
        /* Execute the right function.*/ /* 
        if (function.equals("sqrt")) {
            if (args.length != 1)
                throw new InvalidInputException("usage: sqrt(value).");
            answer = Ar_Functions.sqrt(args[0]);
        } else if (function.equals("nroot")) {
                if (args.length != 2)
                    throw new InvalidInputException("usage: nroot(value, root).");
                answer = Ar_Functions.nroot(args[0], args[1]);
        } else if (function.equals("pow")) {
            if (args.length != 2)
                throw new InvalidUsageException("usage: pow(value, power).");
            answer = Ar_Functions.pow(args[0], args[1]);
        } else if (function.equals("log")) {
            if (args.length < 1 || args.length > 2)
                throw new InvalidUsageException("usage: log(value[, base]).");
            if (args.length == 1) {
                answer = Ar_Functions.log(args[0]);
            } else {
                answer = Ar_Functions.log(args[0], args[1]);
            } 
        } else if (function.equals("round")) {
            if (args.length < 1 || args.length > 2)
                throw new InvalidUsageException("usage: round(value[, precision]).");
            if (args.length == 1) {
                answer = Ar_Functions.round(args[0]);
            } else {
                answer = Ar_Functions.round(args[0], args[1]);
            } 
        } else {
            throw new InvalidInputException("Unknown function '" + function + "'.");
        }
        return String.valueOf(answer);
    }
    */
    /*
    private String evaluateOperation(int type, String arg_a, String arg_b) throws InvalidInputException {
        double a, b;
        
        try {
            a = Double.parseDouble(arg_a);
        } catch (Exception e) {
            throw new InvalidInputException("Ongeldige invoer: '" + arg_a + "'.");
        }
        try {
            b = Double.parseDouble(arg_b);
        } catch (Exception e) {
            throw new InvalidInputException("Ongeldige invoer: '" + arg_b + "'.");
        }
        switch (type) {
            case 0: /* = */
//                return a == b ? "1" : "0";
 //           case 1: /* = */
 //               return a < b ? "1" : "0";
 //           case 2: /* = */
//                return a > b ? "1" : "0";
//            case 3: /* = */
//                return a <= b ? "1" : "0";
//            case 4: /* = */
//                return a >= b ? "1" : "0";
//            case 5: /* + */
//                return String.valueOf(a + b);
//            case 6: /* - */
//                return String.valueOf(a - b);
//            case 7: /* * */
//                return String.valueOf(a * b);
 //           case 8: /*/ */
 //               return String.valueOf(a / b);
  //          case 9: /* % */
  //          	return String.valueOf(a % b);
 //           case 10: /* ^ */
 //               return String.valueOf(Math.pow(a, b));
//            default:
//                throw new InvalidInputException("Unknown operator " /*+ arith_ops[type]*/);
//        }
//    }*/
}

class Argument {
	protected ArgumentType type;
	protected String value;
	
	public Argument() {
		this("", new ArgumentType(ArgumentType.UNKNOWN));
	}
	
	public Argument(String value) {
		this(value, ArgumentType.determineType(value));
	}
	
	public Argument(String value, ArgumentType type) {
		this.type = type;
		this.value = value;
	}
	
	public ArgumentType getType() {
		return type;
	}
	
	public String getValue() {
		return value;
	}
	
	public void setValue(String s) {
		this.type = ArgumentType.determineType(s);
		this.value = s;
	}
	
	public double getRealValue() throws InvalidTypeException {
		if (!this.getType().isReal())
			throw new InvalidTypeException("Argument is not a Real.");
		else
			return Double.parseDouble(this.value);
	}
	
	public String toString() {
		return type.toString() + ": " + value;
	}
}

class Expression extends Argument {
	private Vector<Argument> arguments;
	
	public Expression(String value) throws InvalidInputException {
		super(value, new ArgumentType(ArgumentType.EXPRESSION));
		arguments = new Vector<Argument>();
		
		extractArguments();
	}
	
	public Expression(Argument[] args) {
		super("");
		int i;
		arguments = new Vector<Argument>();
		
		for (i = 0; i < args.length; i++) {
			arguments.add(args[i]);
		}
	}
	
	/* Extract arguments and store them in 'arguments'. */
	public void extractArguments() throws InvalidInputException {
		char c;
		int i = 0, j, k;
		int l = value.length(); /* Used very often, this is faster. */
		value.split(Globals.operators.replaceAll("\\?", "|"));
		
		while (i < l) {
			j = i;
			c = value.charAt(i);
			//System.out.println("Checking char " + i + ": " + c);
			if (Character.isLetter(c)) {
				/* Result is variable or function. */
				while (Character.isLetter(c) && ++i < l) { /* TODO: One redundant check. */ 
					c = value.charAt(i);
				}
				if (i < l && c == '(') {
					/* Result is function. */
					k = i + 1;
					do {
	                    i = value.indexOf(")", i) + 1;
	                    k = value.indexOf("(", k) + 1;
	                } while (i >= 0 && k >= 0 && k < i);
	                if (i < 0) {
	                    /* Assume whole rest of string belongs to opening brace. */
	                    i = value.length();
	                    value += ")";
	                }
				} else {
					/* Result is variable. */
				}
			} else if (Character.isDigit(c) || c == '-' || c == '.') {
				/* Result is real or operator (-). */
				if (c == '-') {
					if (i == 0) {
						/* Result is operator. */
						i++;
					} else {
						/* Result is real or operator. */
						c = value.charAt(i - 1);
						if (Character.isLetter(c) || Character.isDigit(c) || c == '.' || c == ')') {
							/* Result is operator. */
							i++;
						} else {
							/* Result is real. */
							while ((Character.isDigit(c) || c == '.') && ++i < l) { /* TODO: One redundant check. */ 
								c = value.charAt(i);
							}
						}
					}
				} else {
					/* Result is real. */
					while ((Character.isDigit(c) || c == '.') && ++i < l) { /* TODO: One redundant check. */ 
						c = value.charAt(i);
					}
				}
			} else if (c == '(') {
				/* Result is expression. Find closing brace. */
				k = i + 1;
				do {
                    i = value.indexOf(")", i) + 1;
                    k = value.indexOf("(", k) + 1;
                } while (i >= 1 && k >= 1 && k < i);
                if (i <= 0) {
                    /* Assume whole rest of string belongs to opening brace. */
                    i = l;
                }
                
                /* Expression is special case concerning class. */
                arguments.add(new Expression(value.substring(j + 1, i - 1)));
                continue;
			} else if (c == '"') {
				/* Result is string. */
				i = value.indexOf('"', j + 1) + 1;
				if (i <= 0)
					i = l + 1;
				
				arguments.add(new Argument(value.substring(j + 1, i - 1), new ArgumentType(ArgumentType.STRING)));
				continue;
			} else if (c == ' ') {
				i++;
				continue; /* skip spaces */
			} else {
				/* Result is operator or error. */
				while (++i < l && (Globals.operators.indexOf("?" + value.substring(j, i) + "?") >= 0 || Globals.operators.indexOf("?\\" + value.substring(j, i) + "?") >= 0));
				if (i == j + 1) {
					/* Result is error. */
					throw new InvalidInputException("Invalid input: unknown element '" + value.substring(j, i) + "' in " + value + ".");
				}
				i--;
			}
			
			/* Add the argument to the list. */
			arguments.add(new Argument(value.substring(j, i)));
		}
		
		/*	
		System.out.println("I found the following arguments in " + value + ": ");
		for (i = 0; i < arguments.size(); i++) {
			System.out.println(arguments.elementAt(i).toString());
		}*/
	}
	
	public void evaluate() throws Exception {
		int[] reals = new int[arguments.size()];
		int[] vars = new int[arguments.size()];
		int[] ops = new int[arguments.size()];
		int[] funcs = new int[arguments.size()];
		int[] exps = new int[arguments.size()];
		
		int reals_pos = 0;
		int vars_pos = 0;
		int ops_pos = 0;
		int funcs_pos = 0;
		int exps_pos = 0;
		
		int i = 0;
		
		Iterator<Argument> it = arguments.iterator();
		Argument arg;
		ArgumentType argt;
	
		while (it.hasNext()) {
			arg = it.next();
			argt = arg.getType();
			if (argt.isExpression())
				exps[exps_pos++] = i;
			if (argt.isFunction())
				funcs[funcs_pos++] = i;
			if (argt.isOperator())
				ops[ops_pos++] = i;
			if (argt.isReal())
				reals[reals_pos++] = i;
			if (argt.isVariable())
				vars[vars_pos++] = i;
			i++;
		}
		
		/* First evaluate other expressions. */
		if (exps_pos > 0) {
			for (i = 0; i < exps_pos; i++)
				((Expression)(arguments.elementAt(i))).evaluate();
		}
		
		/* Check for functions to evaluate. */
		if (funcs_pos > 0) {
			for (i = 0; i < funcs_pos; i++) {
				/* TODO: evaluate function. */
			}
		}
		/*
		^: Argument^Argument
		*: ...+Arguments*Arguments+...
		+: ...=Arguments+Arguments=...
		*/
		/* Check for operators. */
		if (ops_pos > 0) {
			for (i = 0; i < ops_pos; i++) {
				/* TODO: evaluate operators. */
				/* test: */
					if (arguments.elementAt(ops[i]).getValue().equals("*")) {
						if (ops[i] == 0 || ops[i] == arguments.size() - 1)
							throw new Exception("Test exception " + arguments.size() + "; " + i);
						Argument[] a = {arguments.elementAt(ops[i] - 1)};
						Argument[] b = {arguments.elementAt(ops[i] + 1)};
						Argument answer = Evaluator.multiply(a, b);
						Argument test = new Argument("All I can give you for now is: ", new ArgumentType(ArgumentType.STRING));
						arguments.removeAllElements();
						arguments.add(test);
						arguments.add(answer);
					} else {
						System.out.println("I found " + arguments.elementAt(ops[i]).getValue());
					}
				/* end test */
			}
		}
		
		/* Check for equal terms. */
	}
	
	public String toString() {
		StringBuffer out = new StringBuffer();
		Iterator<Argument> it = arguments.iterator();
		
		while (it.hasNext()) {
			out.append(it.next().getValue());
		}
		//System.out.println(":" + out + ":");
		return out.toString();
	}
}

class Globals {
	/* Separated by \. */
	static String operators = "?=?<?>?<=?>=?\\+?-?\\*?/?%?^?";
	
    private static String[] op_levels = {"=|<|>|<=|>=",
		 "\\+|-",
		 "\\*|/|%",
		 "\\^"};
}

class Evaluator {
	public static Argument multiply(Argument[] ex_args, Argument[] args) throws InvalidTypeException {
		Argument result;
		Argument[] newargs;
		ArgumentType at;
		ArgumentType rt;
		Expression tmp;
		int i, j;
		int newargs_amount = 0;
		String res = "1";
		
		/* All result arguments are listed in newargs. */
		newargs = new Argument[ex_args.length + args.length];
		for (i = 0; i < ex_args.length; i++)
			newargs[i] = ex_args[i];
		newargs_amount = ex_args.length;
		
		argloop:
			for (i = 0; i < args.length; i++) {
				/* Search arguments for matching types and multiply if possible. */
				for (j = 0; j < newargs_amount; j++) {
					at = args[i].getType();
					rt = newargs[j].getType();
					
					if (at.isOperator()) {
						/* Double continue, operator is probably '^'. */
						i++;
						continue argloop;
					}
					if (rt.isOperator()) {
						/* Double continue newargs, same case as above. */
						j++;
						continue;
					}
										
					if (at.isReal()) {
						if (rt.isReal()) {
							/* Just multiply the two values and write them back. */
							newargs[j].setValue(String.valueOf(newargs[j].getRealValue() * args[i].getRealValue()));
							continue argloop; /* This argument is finished. */
						} else {
							continue; /* Can't do anything to other elements. */
						}
					} else if (at.isVariable() || at.isFunction()) {
						break;
						/* TODO: make better system. */
						// if (rt.isVariable() && newargs[j].getValue().equals(args[i].getValue()))
					} else {
						/* At is expression. */
						
					}
						
				}
				
				/* No matching arguments, so add this argument. */
				newargs[newargs_amount] = args[i];
				newargs_amount++;
			}
		
		if (newargs_amount == 1) {
			return newargs[0];
		} else {
			return (Argument)(new Expression(newargs));
		}
	}
}