# Attempts to process only combinational gates!
# Sequential gates *should* be skipped, but may be improperly processed instead!
# Pin loads and delays are *not* processed! They are ignored, and arbitrary defaults are written to the output.
from sys import stderr, argv, stdin
from liberty.parser import parse_liberty
from enum import Enum

fname = argv[1]
if fname == '-':
    lib = parse_liberty(stdin.read())
else:
    lib = parse_liberty(open(fname, 'r').read())

class TimingSense(Enum):
    NONE            = 0
    POSITIVE_UNATE  = 1
    NEGATIVE_UNATE  = 2
    UNKNOWN         = 3

def cellIsDontuse (cell):
    return cell['dont_use']

def cellIsComb (cell):
    return not cellIsSeq(cell)

def cellIsSeq (cell):
    for pin in cell.get_groups('pin'):
        if pin['clock'] == 'true' or pin['clock_gate_out_pin'] == 'true':
            return True
    return False

def cellIsTie (cell):
    cell_sense = cellTimingSense(cell)
    if cell_sense == TimingSense.NONE and cellOutputPins(cell) == 1:
        # Probably a tie cell
        return True
    else:
        return False

def cellIsUnate (cell):
    sense = TimingSense.NONE
    cell_sense = cellTimingSense(cell)
    if cell_sense == TimingSense.POSITIVE_UNATE or cell_sense == TimingSense.NEGATIVE_UNATE:
        return True
    elif cellIsTie(cell):
        return True
    else:
        return False

def pinIsOutput (pin):
    if pin['direction'] == 'output':
        return True
    else:
        return False

def cellOutputPins (cell):
    output_pins = 0
    output_pin = None
    for pin in cell.get_groups('pin'):
        if pinIsOutput(pin):
            output_pins += 1
            output_pin = pin
    return output_pins

def cellSingleOutput (cell):
    output_pins = cellOutputPins(cell)
    if output_pins != 1:
        return False
    else:
        for pin in cell.get_groups('pin'):
            if pinIsOutput(pin):
                return pin

# Return timing sense of a pin from a timing group as a TimingSense object
def timingGetTimingSense (timing) -> TimingSense:
    sense = timing['timing_sense']
    switcher = {
        'positive_unate': TimingSense.POSITIVE_UNATE,
        'negative_unate': TimingSense.NEGATIVE_UNATE,
    }
    return switcher.get(sense, TimingSense.NONE)

def outputpinTimingSense (pin) -> TimingSense:
    # If sense of all timing groups of output pin are equal, this determines the timing sense of the pin.
    # If sense of timing groups differ, sense is binate or unknown.
    if not pinIsOutput(pin):
        raise Exception('Cannot find timing sense of a non-output pin {}'.format(pin.args[0]))
    sense = TimingSense.NONE
    for timing in pin.get_groups('timing'):
        timing_sense = timingGetTimingSense(timing)
        if sense == TimingSense.NONE:
            sense = timing_sense
        elif sense != timing_sense:
            return TimingSense.UNKNOWN
    return sense

def cellTimingSense (cell) -> TimingSense:
    # Cannot determine cell sense of a non-single-output cell
    output_pin = cellSingleOutput(cell)
    if output_pin == False:
        return TimingSense.NONE
    # Cell is unate if timing sense of all pins is equal
    # The cell's output pin contains timing sense info w.r.t. to all inputs
    return outputpinTimingSense(output_pin)

# Loop through all cells in library
for cell in lib.get_groups('cell'):
    cell_name = cell.args[0]
    output_count = 0

    # Skip cell marked 'dont use'
    if cellIsDontuse(cell):
        print('Skipping cell marked as "dont use" in input library: {}'.format(cell_name), file=stderr)
        continue

    # Skip cells with multiple outputs
    if cellSingleOutput(cell) == False:
        print('Skipping cell without exactly one output pin: {}'.format(cell_name), file=stderr)
        continue

    # Skip non-unate gates
    if not cellIsUnate(cell):
        print('Skipping cell with non-unate output: {}'.format(cell_name), file=stderr)
        continue

    # Skip sequential gates
    if cellIsSeq(cell):
        print('Skipping sequential cell: {}'.format(cell_name), file=stderr)
        continue

    # Get output pin's function and translate to Genlib format
    output_pin = cellSingleOutput(cell)
    func = str(output_pin['function'])

    # Cell has not been determined to be non-unate after checking timing groups.
    # Is it possible the cell could be unate even if it contains an xor (^) in its function?
    if '^' in func:
        print('Rejecting cell with xor operator in cell function field: {}'.format(cell_name), file=stderr)
        continue
    replacements = {
            '&': '*',
            '|': '+',
            '"': '',
            ' ': '',
    }
    func = ''.join([replacements.get(c, c) for c in func])
    # Replace 0 and 1 functions with CONST0/CONST1
    if func == '0':
        func = 'CONST0'
    elif func == '1':
        func = 'CONST1'

    # Translate timing_sense to Genlib format
    switcher = {
            TimingSense.POSITIVE_UNATE: 'NONINV',
            TimingSense.NEGATIVE_UNATE: 'INV',
    }
    phase = switcher.get(cellTimingSense(cell), TimingSense.UNKNOWN)

    area = cell['area']
    # Print Genlib format
    print('GATE\t{}\t\t{}\t{}={};'.format(cell_name, area, output_pin.args[0], func))
    if not cellIsTie(cell):
        print('PIN *\t{} 1 999 1 0.2 1 0.2'.format(phase))
    print()
