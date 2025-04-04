# Eclipse Java Class HTML Parser

## Overview:
This is a small, personal project designed to create a `.java` file (Java source code text file) from a `.html` documentation file created by Eclipse IDE. This is particularly useful for students in UW–Madison's CS 300 course, where students are provided documentation for Java code they are expected to create but not given a starting `.java` file, leading to wasted time copying and pasting Javadocs and signatures. This tool does not write any functional code by interpreting the Javadocs; it simply creates Java code with default return statements where necessary.

## How to Use:
1. This project is built in Python. Make sure you have Python installed and usable in your terminal. This guide will use "`py`" as the keyword for Python, but it may be "`python`", "`python3`", etc. in your environment.

2. Download the files in this project.

3. Download the required dependencies using pip.
`pip install -r requirements.txt`\
or maybe\
`py -m pip install -r requirements.txt`

4. This project is a CLI tool with only one positional argument: `file`. Simply pass the directory to the `.html` documentation file you wish to convert to Java code. The `.java` file will be written to the same directory as `main.py` with the file name of `<ClassName>.java`, where ClassName is the name of the class the documentation file was created for. For example, running `py main.py MyObject.html` will create a `MyObject.java` in the same directory as `main.py`.

5. Move the created file to its intended location and implement the functionality of the code.

## Note:
This tool has not been extensively tested because it was made for personal use, but I did leave some documentation in case anyone wants to work with the code. 