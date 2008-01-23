The Java source code for Annarithetmic (Plugin.java) is
Copyright (c) 2008 Lucas Moeskops, all rights reserved.

In order to use this module you need jpype [1] installed and you need
the environment variable JAVA_HOME to point to the correct location of
your java development kit root. You can test this by importing the jpype
module manually:

 >>> from jpype import *
 >>> startJVM(j.getDefaultJVMPath())

If this does not raise any errors you are most likely good to go.

You can use the compile.sh script provided in the javasource directory
to compile the source into a usable .jar file.

To test the plugin, run

 $ python test.py

[1] http://jpype.sourceforge.net/
