The Java source code for Annarithetmic (Plugin.java) is
Copyright (c) 2008 Lucas Moeskops, all rights reserved.

In order to use this module you need jpype [1] installed and you need
the environment variable JAVA_HOME to point to the correct location of
your java development kit root. You can test this by importing the jpype
module manually:

 >>> from jpype import *
 >>> startJVM(j.getDefaultJVMPath())

If this does not raise any errors you are most likely good to go.

You will also need to compile the java source first and create a .jar:

 $ javac Plugin.java
 $ mkdir annarithmetic
 $ mv Plugin.class annarithmetic
 $ jar cf annarithmetic.jar annarithmetic
 $ rm -rf annarithmetic

[1] http://jpype.sourceforge.net/
