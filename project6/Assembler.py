import os
import sys

TAB = '\t'
SPACE = ' '
A_COMMAND = 'A_COMMAND'
C_COMMAND = 'C_COMMAND'
L_COMMAND = 'L_COMMAND'
A_CODE_PREFIX = '0'
C_CODE_PREFIX = '1'
SEMICOLON = ';'
EQUAL = '='
L_PREFIX = '('
R_PREFIX = ')'
A_PREFIX = '@'
PATH_INDEX = 1
NEW_LINE_TRAIL = '\n'
START_OF_COMMENT = '//'
READ_MODE = 'r'
WRITE_MODE = 'w'
EMPTY_TRAILS = {'\n', '\r\n'}
ASM_END = ".asm"
HACK_END = ".hack"


class Assembler:
    """  a class that represent an assembler object who takes a list of instructions in assembly language and
    translate them to machine language """

    PRE_DEFINED_LABELS = {'R0': '{0:015b}'.format(0),
                          'R1': '{0:015b}'.format(1),
                          'R2': '{0:015b}'.format(2),
                          'R3': '{0:015b}'.format(3),
                          'R4': '{0:015b}'.format(4),
                          'R5': '{0:015b}'.format(5),
                          'R6': '{0:015b}'.format(6),
                          'R7': '{0:015b}'.format(7),
                          'R8': '{0:015b}'.format(8),
                          'R9': '{0:015b}'.format(9),
                          'R10': '{0:015b}'.format(10),
                          'R11': '{0:015b}'.format(11),
                          'R12': '{0:015b}'.format(12),
                          'R13': '{0:015b}'.format(13),
                          'R14': '{0:015b}'.format(14),
                          'R15': '{0:015b}'.format(15),
                          'SP': '{0:015b}'.format(0),
                          'LCL': '{0:015b}'.format(1),
                          'ARG': '{0:015b}'.format(2),
                          'THIS': '{0:015b}'.format(3),
                          'THAT': '{0:015b}'.format(4),
                          'SCREEN': '{0:015b}'.format(16384),
                          'KBD': '{0:015b}'.format(24576)
                          }

    VARIABLES_RAM_LOCATION = 16

    def __init__(self, file):
        """ Initialize the symbol table with all the predefined symbols and their pre-allocated RAM addresses """
        self.parser = Parser(file)
        self.code = Code()

        self.symbols = SymbolTable()
        self.init_predefined_labels()

        self.file = open(file.replace(ASM_END, HACK_END), WRITE_MODE)

    def init_predefined_labels(self):
        """ set the pre-defined lables"""
        for label in Assembler.PRE_DEFINED_LABELS:
            self.symbols.add_entry(label, Assembler.PRE_DEFINED_LABELS[label])

    def assemble(self):
        """ preform the parsing process"""
        self.first_pass()
        self.second_pass()

    def first_pass(self):
        parser = self.parser
        parser.reset()
        rom_address = 0
        while True:
            if parser.command_type() is L_COMMAND:
                self.symbols.add_entry(parser.symbol(), rom_address)
            else:
                rom_address += 1
            if not parser.has_more_commands():
                break

            parser.advance()

    def second_pass(self):
        self.parser.reset()
        var_address = Assembler.VARIABLES_RAM_LOCATION
        while True:

            if self.parser.command_type() is A_COMMAND:
                symbol = self.parser.symbol()
                if not (symbol.isdigit() or (symbol in self.symbols)):
                    # add symbol to table
                    self.symbols.add_entry(symbol, var_address)
                    var_address += 1

                self.file.write(self.translate_A_instruction())

            elif self.parser.command_type() is C_COMMAND:
                self.file.write(self.translate_C_instruction())

            if not self.parser.has_more_commands():
                break
            self.parser.advance()

        self.file.close()

    def translate_A_instruction(self):
        """ Returns a string of a 16 bit binary number of an A instruction """
        binary_code = A_CODE_PREFIX + self.symbols.get_address(self.parser.symbol())
        return binary_code + '\n'

    def translate_C_instruction(self):
        """ Returns a string of a 16 bit binary number of an C instruction """
        assert self.parser.command_type() == C_COMMAND
        comp = self.code.comp(self.parser.comp())
        dest = self.code.dest(self.parser.dest())
        jump = self.code.jump(self.parser.jump())
        binary_code = C_CODE_PREFIX + comp + dest + jump
        return binary_code + NEW_LINE_TRAIL


class SymbolTable:
    """ Keeps a correspondence between symbolic labels and numeric addresses."""

    def __init__(self):
        """ Creates a new empty symbol table."""
        self.table = dict()

    def add_entry(self, symbol, address):
        """  Adds the pair (symbol,address) to the table."""
        if type(address) == int:
            self.table[symbol] = '{0:015b}'.format(address)
        else:
            self.table[symbol] = address

    def __contains__(self, symbol):
        """ Does the symbol table contain the given symbol?"""
        return self.table.get(symbol) is not None

    def get_address(self, symbol):
        """ Returns the address associated with the symbol.    """
        if symbol.isdigit():
            return '{0:015b}'.format(int(symbol))

        return self.table.get(symbol)


class Code:
    """ Translates Hack assembly language mnemonics into binary codes"""
    COMP_CODE = {'0': '110101010',
                 '1': '110111111',
                 '-1': '110111010',
                 'D': '110001100',
                 'A': '110110000',
                 '!D': '110001101',
                 '!A': '110110001',
                 '-D': '110001111',
                 '-A': '110110011',
                 'D+1': '110011111',
                 '1+D': '110011111',
                 'A+1': '110110111',
                 '1+A': '110110111',
                 'D-1': '110001110',
                 'A-1': '110110010',
                 'D+A': '110000010',
                 'A+D': '110000010',
                 'D-A': '110010011',
                 'A-D': '110000111',
                 'D&A': '110000000',
                 'A&D': '110000000',
                 'D|A': '110010101',
                 'A|D': '110010101',
                 'M': '111110000',
                 '!M': '111110001',
                 '-M': '111110011',
                 'M+1': '111110111',
                 '1+M': '111110111',
                 'M-1': '111110010',
                 'D+M': '111000010',
                 'M+D': '111000010',
                 'D-M': '111010011',
                 'M-D': '111000111',
                 'D&M': '111000000',
                 'M&D': '111000000',
                 'D|M': '111010101',
                 'M|D': '111010101',
                 'D>>': '010010000',
                 'D<<': '010110000',
                 'A>>': '010000000',
                 'A<<': '010100000',
                 'M>>': '011000000',
                 'M<<': '011100000'
                 }

    DEST_CODE = {'': '000',
                 'M': '001',
                 'D': '010',
                 'MD': '011',
                 'DM': '011',
                 'A': '100',
                 'AM': '101',
                 'MA': '101',
                 'AD': '110',
                 'DA': '110',
                 'AMD': '111',
                 'ADM': '111',
                 'MAD': '111',
                 'MDA': '111',
                 'DMA': '111',
                 'DAM': '111', }

    JUMP_CODE = {'': '000',
                 'JGT': '001',
                 'JEQ': '010',
                 'JGE': '011',
                 'JLT': '100',
                 'JNE': '101',
                 'JLE': '110',
                 'JMP': '111'}

    NULL = '000'

    def dest(self, mnemonic):
        """ Returns the binary code of the dest mnemonic."""
        assert mnemonic is not None, 'your mnemonic is: ' + str(mnemonic)
        return Code.DEST_CODE.get(mnemonic, Code.NULL)

    def comp(self, mnemonic):
        """ Returns the binary code of the comp mnemonic."""
        return Code.COMP_CODE.get(mnemonic)

    def jump(self, mnemonic):
        """ Returns the binary code of the jump mnemonic"""
        assert mnemonic is not None, 'your mnemonic is: ' + str(mnemonic)
        return Code.JUMP_CODE.get(mnemonic, Code.NULL)


class Parser:

    @staticmethod
    def is_comment(line):
        """
        Checks if given line is a comment.
        :param line: Line to check.
        :return: True iff line is a comment.
        """
        return line[0:2] == START_OF_COMMENT or (line in EMPTY_TRAILS)

    @staticmethod
    def strip_comments(line):
        """
        Strips comments off line of code.
        :param line: Given line of code.
        :return: New, comment-stripped line.
        """
        return line.split('//')[0]

    def __init__(self, path):
        """
        Opens the input file and gets ready to parse it.
        :param path: Path of the assembly code.
        """

        self.lines = self.first_run(path)
        self.index = 0

    def first_run(self, filepath):
        """
        Makes first run over code and removes comments and white spaces.
        In addition
        :param filepath: Path of the asm code.
        :return: List of all lines without comments and blank lines.
        """
        with open(filepath) as file:
            code_lines = []
            for line in file:
                line = (
                    line.split(START_OF_COMMENT, 1)[0].replace(SPACE, '').replace(TAB, '').replace(NEW_LINE_TRAIL, ''))
                if line != "":
                    code_lines.append(line)

            return code_lines

    def has_more_commands(self):
        """
        Checks if there any more commands in the input.
        :return:
        """
        return self.index < len(self.lines) - 1

    def advance(self):
        """
        Reads the next command from the input and makes it the current command.
        Should be called only if  hasMoreCommands() is true.
        Initially the is no current command.
        :return: True iff there are more commands to parse.
        """
        if self.has_more_commands():
            self.index += 1

    def reset(self):
        """
        Resets the Parser to the beginning of the code file.
        """
        self.index = 0

    def command_type(self):
        """
        :return: The type of the current 	command:
        - A_COMMAND for @Xxx where Xxx is either a symbol or a	decimal number
        - C_COMMAND for	dest=comp;jump
        - L_COMMAND (actually, pseudocommand) for (Xxx) where Xxx is a symbol.
        """
        first_char = self.lines[self.index][0]
        return {
            A_PREFIX: A_COMMAND,
            L_PREFIX: L_COMMAND
        }.get(first_char, C_COMMAND)

    def symbol(self):
        """
        :return: The symbol or decimal Xxx of the current command @Xxx or (Xxx). Should be called
        only when commandType() is A_COMMAND or L_COMMAND.
        """
        assert self.command_type() in [A_COMMAND, L_COMMAND]

        symbol = self.lines[self.index].lstrip(A_PREFIX + L_PREFIX)
        return symbol.rstrip(R_PREFIX) if (self.command_type() == L_COMMAND) else symbol

    def dest(self):
        """
        :return: The dest mnemonic in the current C-command (8 possiblities).
        Should be called only when commandType() is C_COMMAND.
        """
        assert (self.command_type() == C_COMMAND)
        return self.lines[self.index].rpartition(EQUAL)[0]  # if there is no '=' it returns ''

    def comp(self):
        """
        :return: The comp mnemonic in the current C-command (28 possibilities).
        Should be called only when commandType() is C_COMMAND.
        """
        assert (self.command_type() == C_COMMAND), 'your line is: ' + str(self.lines[self.index])
        comp = self.lines[self.index].rpartition(EQUAL)[-1]
        # if there is '=' we get the right side of it, else we got the string
        comp = comp.partition(SEMICOLON)[0]
        # if there is ';' we get the left side of it, else we got the same string
        return comp

    def jump(self):
        """
        :return: The jump mnemonic in the current C-command (8 possibilities).
        Should be called only when commandType() is C_COMMAND.
        """
        assert (self.command_type() == C_COMMAND)
        return self.lines[self.index].partition(SEMICOLON)[-1]


if __name__ == "__main__":
    file = sys.argv[1]
    if os.path.isfile(file):
        if file.endswith('.asm'):
            assembler = Assembler(file)
            assembler.assemble()

    elif os.path.isdir(file):
        for files in os.listdir(file):
            file = os.path.join(file, files)
            if file.endswith('.asm') and os.path.isfile(file):
                assembler = Assembler(file)
                assembler.assemble()
    else:
        print("invalid file path")
