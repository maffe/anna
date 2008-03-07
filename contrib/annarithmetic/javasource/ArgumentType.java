package annarithmetic;

public class ArgumentType {
	public static final int UNKNOWN = 0;
	public static final int REAL = 1;
	public static final int COMPLEX = 6; /* Not yet implemented */
	public static final int OPERATOR = 2;
	public static final int VARIABLE = 3;
	public static final int FUNCTION = 4;
	public static final int EXPRESSION = 5;
	public static final int STRING = 6;
	
	public static ArgumentType determineType(String arg) {
		if (isReal(arg)) {
			return new ArgumentType(REAL);
		} else if (isOperator(arg)) {
			return new ArgumentType(OPERATOR);
		} else if (isVariable(arg)) {
			return new ArgumentType(VARIABLE);
		} else if (isFunction(arg)) {
			return new ArgumentType(FUNCTION);
		} else {
			return new ArgumentType(EXPRESSION);
		}
	}
	
	/* TODO: Might be implemented more elegant. */
	private static boolean isFunction(String arg) {
		boolean moreThanJustLetters = false;
		int i, j, level = 1;
		System.out.print("<");
		for (i = 0; i < arg.length(); i++) {
			if (!Character.isLetter(arg.charAt(i))) {
				moreThanJustLetters = true;
				/* So the function name ended; now a opening brace should occur. */
				if (arg.charAt(i) != '(') {
					/* If not, this is not a valid function. */
					return false;
				} else {
					/* Now check if the last character is the correct closing brace. */
					i++;
					while (i >= 0 && i < arg.length() - 1) {
						j = arg.indexOf(')', i + 1);
						i = arg.indexOf('(', i + 1);
						if (i >= 0 && i < j)
							level++;
						else if (j >= 0)
							level--;
						System.out.print(level);
						/* If level is zero or below while the last character isn't reached yet, 
						 * the input contains more than just the function.
						 */
						if (level <= 0 && j < arg.length() - 1)
							return false;
						
						i = Math.min(i, j) > 0? Math.min(i, j) + 1 : Math.max(i, j);
					}
					System.out.print(":" + i + ":");
					if (level != 0 || i < arg.length() - 1)
						return false;
				}
			}
		}
		
		return arg.length() > 0 && moreThanJustLetters;
	}
	
	private static boolean isReal(String arg) {
		/* TODO: ugly implementation ? */
		try {
			Float.parseFloat(arg);
			return true;
		} catch (NumberFormatException nfe) {
			return false;
		}
	}
	
	private static boolean isOperator(String arg) {
		return Globals.operators.indexOf("?" + arg + "?") >= 0 || Globals.operators.indexOf("?\\" + arg + "?") >= 0;
	}
	
	private static boolean isVariable(String arg) {
		int i;
		
		for (i = 0; i < arg.length(); i++) {
			if (!Character.isLetter(arg.charAt(i)))
				return false;
		}
		
		return arg.length() > 0;
	}
	
	private int type;
	
	public ArgumentType(int type) {
		this.type = type;
	}
	
	public boolean isExpression() {
		return type == EXPRESSION;
	}
	
	public boolean isFunction() {
		return type == FUNCTION;
	}
	
	public boolean isOperator() {
		return type == OPERATOR;
	}
	
	public boolean isReal() {
		return type == REAL;
	}
	
	public boolean isVariable() {
		return type == VARIABLE;
	}
	
	public String toString() {
		switch (type) {
			case EXPRESSION:
				return "Expression";
			case FUNCTION:
				return "Function";
			case OPERATOR:
				return "Operator";
			case REAL:
				return "Real";
			case VARIABLE:
				return "Variable";
			default:
				return "Unknown type";	
		}
	}
}