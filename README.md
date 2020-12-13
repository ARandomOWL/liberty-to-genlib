# liberty-to-genlib
Convert Synopsys Liberty fomat to SIS Genlib 

First iteration designed only to processes combinational gates. Tie cells are
not yet processed correctly. 

Designed for interoperability with Workcraft, therefore (for the moment at least): 
- Non-unate gates are not processed. 
- Pin loads and delays are not processed (Workcraft backends don't use them, arbitrary defaults are written). 

## Requirements
Python 3 
liberty-parser (tested with 0.0.7) 

## Usage
`python liberty-to-genlib.py [inputfile.lib] > [outputfile.lib]` 
