# Attempts to process only combinational gates!
# Sequential gates *should* be skipped, but may be improperly processed instead!
# Pin loads and delays are *not* processed! They are ignored, and arbitrary defaults are written to the output.
from sys import stderr, argv
from liberty.parser import parse_liberty

f = argv[1]
lib = parse_liberty(open(f).read())

# Loop through all cells in library
for cell in lib.get_groups('cell'):
    cell_name = cell.args[0]
    output_count = 0

    # Loop through all pins of current cell
    func = None
    timing_sense = None
    for pin in cell.get_groups('pin'):
        pin_name = pin.args[0]

        # No need to process input pins explicitly. All useful info contained in output pins.
        if (pin['direction'] != 'output'):
            continue

        # Skip sequential gates
        # by checking if any pins are marked as 'clock' or 'clock_gate_clock_pin'
        if (pin['clock'] == 'true' or pin['clock_gate_out_pin'] == 'true'):
            print('Skipping sequential cell: {}'.format(cell_name), file=stderr)
            func = None
            break

        # Skip cells with multiple outputs (Genlib format doesn't support them)
        output_count += 1
        if (output_count > 1):
            print('Skipping cell with multiple output pins: {}'.format(cell_name), file=stderr)
            func = None
            break

        # Skip non-unate gates
        # by checking timing sense of all inputs (w.r.t. output) are equal
        for timing in pin.get_groups('timing'):
            if (timing_sense == None):
                timing_sense = timing['timing_sense']
            elif (timing_sense != timing['timing_sense']):
                timing_sense = None
                break
        # If timing_sense unset here, cell is non-unate
        if (timing_sense == None):
            print('Skipping cell with non-unate output: {}'.format(cell_name), file=stderr)
            func = None
            break

        # Get output pin's function and translate to Genlib format
        func = pin['function']
        replacements = {
                '&': '*',
                '|': '+',
                '"': '',
                ' ': '',
        }
        func = ''.join([replacements.get(c, c) for c in str(func)])


    # If func is unset here, we're ignoring this cell
    if (func == None):
        continue

    # Translate timing_sense to Genlib format
    phase = str(timing_sense).replace('positive_unate', 'NONINV').replace('negative_unate', 'INV')

    area = cell['area']
    # Print Genlib format
    print('GATE\t{}\t\t{}\t{}={};'.format(cell_name, area, pin_name, func))
    print('PIN *\t{} 1 999 1 0.2 1 0.2'.format(phase))
    print()
