# liberty-to-genlib
Convert Synopsys Liberty fomat to SIS Genlib 

First iteration designed only to processes combinational gates. Tie cells are
not yet processed correctly. 

## Requirements
Python 3 
liberty-parser (tested with 0.0.7) 

## Usage
`python liberty-to-genlib.py [inputfile.lib] > [outputfile.lib]` 
