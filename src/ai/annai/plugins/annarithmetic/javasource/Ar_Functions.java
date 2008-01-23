/*
 * Functions
 * Author: Lucas moeskops
 * Created: 15-01-2008
 * Last change: 22-01-2008
 */

package annarithmetic;

public class Ar_Functions {
	
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
		return Math.round(d * tmp) / tmp;
	}
	
}
