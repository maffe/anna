/*
 * Annarithmetic
 * Author: Lucas moeskops
 * Created: 15-01-2008
 * Last change: 21-01-2008 by Hraban Luyat
 */

package annarithmetic;

public class Plugin {    
    static String[] arith_ops = {"=", "l", "g", "le", "ge", "+", "-", "*", "/", "**", "="};
    
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
            "**\tExponentiate\n" +
            "=\tReturns 1 if arguments are equal, else 0\n" +
            "g\tReturns 1 if left arguments greater than right argument, else 0\n" +
            "l\tReturns 1 if left arguments less than right argument, else 0\n" +
            "ge\tReturns 1 if left arguments greater than or equal to right argument, else 0\n" +
            "le\tReturns 1 if left arguments less than or equal to right argument, else 0";
    }
    
    public String parseString(String s) {
        char c;
        int i, j, k;
        String tmp;

        while (true) {
            /* The most important elements are braces. */
            i = j = k = s.indexOf("(");
            if (i >= 0) {
                /* Find closing brace. */
                do {
                    j = s.indexOf(")", j + 1);
                    i = s.indexOf("(", i + 1);
                } while (j >= 0 && i >= 0 && i < j);
                i = k; /* Reset i. */
                if (j < 0) {
                    /* Assume whole rest of string belongs to opening brace. */
                    j = s.length();
                    s += ")";
                }
                
                /* Check if the braces belong to a function. */
                while (k - 1 >= 0) {
                    c = s.charAt(k - 1);
                    if (!Character.isLetterOrDigit(c))
                        break;
                    k--;
                }
                if (k != i) {
                    /* The braces belong to a function. The function name just found might
                     * start with a digit, which is not possible. This piece should therefore
                     * not be counted as function name. */
                    while (k < i) {
                        c = s.charAt(k);
                        if (!Character.isDigit(c))
                            break;
                        k++;
                    }
                    if (k == i) {
                        /* After all not a function. Now further parse the inner string.*/
                        s = s.substring(0, i) + 
                            parseString(s.substring(i + 1, j)) + 
                            s.substring(j + 1);
                    } else {
                        /* Retrieve and evaluate the function. */
                        tmp = s.substring(k, i); /* function name */
                        s = s.substring(0, k) + 
                            evaluateFunction(tmp, s.substring(i + 1, j)) + 
                            s.substring(j + 1);
                    }
                } else {
                    /* The braces were not part of a function. Now further parse the inner string. */
                    s = s.substring(0, i) + 
                        parseString(s.substring(i + 1, j)) + 
                        s.substring(j + 1);
                }
            } else {
                /* No more braces. */
                return evaluateArithmetic(s);
            }
        }
    }

    private String evaluateArithmetic(String argument) {
        int i, j;
        String s, t;
        
        for (i = 0; i < arith_ops.length; i++) {
            /* Test if operator occurs in argument. */
            j = argument.indexOf(arith_ops[i]);
            if (j >= 0) {
                /* Make sure the operator is surrounded by digits. */
                if ((j > 0 && !Character.isDigit(argument.charAt(j - 1))) ||
                    (j < argument.length() - 1 - arith_ops[i].length() 
                    && !Character.isDigit(argument.charAt(j + arith_ops[i].length()))))
                    continue;
                
                /* Evaluate the arguments. */
                s = evaluateArithmetic(argument.substring(0, j));
                t = evaluateArithmetic(argument.substring(j + arith_ops[i].length()));
                
                /* Exception for minus, because of possible negative values. */
                if (arith_ops[i].equals("-") && s.length() == 0)
                    continue;
                
                /* Evaluate the operation. */
                return evaluateOperation(i, s, t);
            }
        }
        return argument;
    }
    
    private String evaluateFunction(String function, String argument) {
        double answer;
        double[] args;
        int i = 0;
        String[] s_args = argument.split(",");
        
        /* Get the arguments. */
        args = new double[s_args.length];
        try {
            for (i = 0; i < args.length; i++)
                args[i] = Double.parseDouble(parseString(s_args[i]));
        } catch (Exception e) {
            System.out.println("Ongeldige invoer: " + s_args[i] + "; ");
            return "?";
        }
        
        /* Execute the right function. */
        if (function.equals("sqrt")) {
            if (args.length != 1)
                return "Squareroot requires 1 argument.";
            answer = Ar_Functions.sqrt(args[0]);
        } else if (function.equals("round")) {
            if (args.length < 1 || args.length > 2)
                return "Round requires 1 or 2 argument(s).";
            if (args.length == 1) {
                answer = Ar_Functions.round(args[0]);
            } else {
                answer = Ar_Functions.round(args[0], args[1]);
            } 
        } else {
            return "Unknown function '" + function + "'.";
        }
        return String.valueOf(answer);
    }
    
    private String evaluateOperation(int type, String arg_a, String arg_b) {
        double a, b;
        try {
            a = Double.parseDouble(arg_a);
        } catch (Exception e) {
            System.out.println("Ongeldige invoer: '" + arg_a + "'.");
            return "?";
        }
        try {
            b = Double.parseDouble(arg_b);
        } catch (Exception e) {
            System.out.println("Ongeldige invoer: '" + arg_b + "'.");
            return "?";
        }
        switch (type) {
            case 0: /* = */
                return a == b ? "1" : "0";
            case 1: /* = */
                return a < b ? "1" : "0";
            case 2: /* = */
                return a > b ? "1" : "0";
            case 3: /* = */
                return a <= b ? "1" : "0";
            case 4: /* = */
                return a >= b ? "1" : "0";
            case 5: /* + */
                return String.valueOf(a + b);
            case 6: /* - */
                return String.valueOf(a - b);
            case 7: /* * */
                return String.valueOf(a * b);
            case 8: /*/ */
                return String.valueOf(a / b);
            case 9: /* ^ */
                return String.valueOf(Math.pow(a, b));
            default:
                return "?";
        }
    }
}

class Ar_Functions {
    
    /* Square root */
    public static double sqrt(double d) {
        return Math.sqrt(d);
    }
    
    /* Round */
    public static double round(double d) {
        return Math.round(d);
    }
    public static double round(double d, double precision) {
        double tmp = Math.pow(10, precision);
        return Math.round(d) / tmp;
    }
    
}
