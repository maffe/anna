#!/usr/bin/env bash

# Compile the java source into a usable .jar file.

javac *.java
mkdir annarithmetic
mv *.class annarithmetic
jar cf annarithmetic.jar annarithmetic
rm -rf annarithmetic
