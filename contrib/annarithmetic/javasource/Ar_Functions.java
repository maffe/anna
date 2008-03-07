/*
 * Functions
 * Author: Lucas moeskops
 * Created: 15-01-2008
 * Last change: 15-01-2008
 */

package annarithmetic;

public class Ar_Functions {
	
	/* Square root */
	public static double sqrt(double d) {
		return Math.sqrt(d);
	}
	
	/* N root */
	public static double nroot(double d, double pow) {
		return Math.pow(d, 1 / pow);
	}
	
	/* Power, same as ^ */
	public static double pow(double d, double pow) {
		return Math.pow(d, pow);
	}
	
	/* Log */
	public static double log(double d) {
		return Math.log(d);
	}
	
	/* Log */
	public static double log(double d, double base) {
		return Math.log10(d) / Math.log(base);
	}
	
	/* Round */
	public static double round(double d) {
		return Math.round(d);
	}
	public static double round(double d, double precision) {
		double tmp = Math.pow(10, precision);
		return Math.round(d * tmp) / tmp;
	}	
}