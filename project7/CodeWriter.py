import os
import sys

# main asm commands
PLC_HOLDER = 5
IS_DIR = True
NOT_DIR = False
TAKE_TO_D = '@SP\nA=M-1\nD=M\n'
LABEL_LINE = '({0})\n'
POP_ = '@SP\nA=A-1\nD=M\n'
INT_TO_M = 'M={0}\n'
SP = 'SP'
A_TO_M = 'M=A\n'
JUMP_COMMAND = "{0};{1}\n"
DECREASE_A = 'A=A-1\n'
TEMP_REG = 'R{0}'
POP_TO_D = "@SP\nAM=M-1\nD=M\n"
PUSH_D = '@SP\nAM=M+1\nA=A-1\nM=D\n'
D_TO_M = 'M=D\n'
A_TO_D = 'D=A\n'
M_TO_A = 'A=M\n'
M_TO_D = 'D=M\n'
SEGMENTS_INDEX = '{0}.{1}\n'
ASSIGN_TO_A = '@{0}\n'

TEMP_REG_INDEX = 5
PATH_INDEX = 1

CALL = 'call'
FUNCTION = 'function'
GOTO = 'goto'
IF = 'if-goto'
RETURN = 'return'
LABEL = 'label'
POP = 'pop'
PULL = 'pull'
PUSH = 'push'

C_LABEL = 'C_LABEL'
C_GOTO = 'C_GOTO'
C_ARITHMETICS = 'C_ARITHMETICS'
C_PUSH = 'C_PUSH'
C_POP = 'C_POP'
C_IF = 'C_IF'
C_FUNCTION = 'C_FUNCTION'
C_RETURN = 'C_RETURN'
C_CALL = 'C_CALL'

SEMICOLON = ';'
NEW_LINE_TRAIL = '\n'
START_OF_COMMENT = '//'
READ_MODE = 'r'
EMPTY_TRAILS = {'\n', '\r\n'}

LINE_BREAK = "\n"

WRITING_MODE = 'w'


class CodeWriter:
    """  a class that represent an assembler object who takes a list of instructions in assembly language and
    translate them to machine language """

    TEMP_IDX = ''

    COMPARING_BINARY_COMMANDS = {'lt', 'gt'}
    BINARY_COMMANDS = {'and', 'or', 'add', 'sub', 'eq', 'lt', 'gt'}
    UNARY_COMMANDS = {'not', 'neg'}
    ARITHMETIC_COMMANDS = {"add": 'M=M+D\n',
                           "sub": 'M=M-D\n',
                           "neg": '@SP\nA=M-1\nM=-M\n',
                           "eq": 'D=M-D\n',
                           "gt": '',
                           "lt": '',
                           "and": 'M=D&M\n',
                           "or": 'M=D|M\n',
                           "not": '@SP\nA=M-1\nM=!M\n'
                           }

    REG_NAMES = {'local': 'LCL', 'argument': 'ARG', 'this': 'THIS', 'that': 'THAT'}
    POINTER_IDX = {'0': 'THIS', '1': 'THAT'}

    def __init__(self, input_file, is_dir):
        """
        Opens the output file/stream and gets ready to write into it.
        :param input_file: output file / stream.
        """
        self._parser = None
        self.label_idx = 0
        self.file_name = None
        if is_dir:  # if file is directory
            self.output_file = open(os.path.join(os.path.normpath(input_file), os.path.basename(input_file) + '.asm'),
                                    WRITING_MODE)
        else:  # if file is single file
            self.output_file = open(input_file.replace('.vm', '.asm'), WRITING_MODE)

    def set_file_name(self, file_name):
        """
        Informs the code writer that the translation of a new VM file has started
        :param file_name: string.
        """
        self.file_name = file_name
        self._parser = Parser(file_name)

    def translate_dir(self, filename):
        """ translates firectory by calling translate on all its files """
        for file in os.listdir(filename):
            if file.endswith('.vm'):
                self.translate(os.path.abspath(os.path.join(filename, file)))

    def translate(self, filename):
        """ performing the translation process"""
        self.set_file_name(filename)

        while self._parser.has_more_commands():
            self._parser.advance()

            command, command_type = self._parser.command(), self._parser.command_type()
            arg1, arg2 = self._parser.arg1(), self._parser.arg2()

            if command_type == C_ARITHMETICS:
                self.write_arithmetic(command)
            elif command_type == C_PUSH:
                self._write_push(arg1, arg2)
            elif command_type == C_POP:
                self._write_pop(arg1, arg2)

    def _write(self, command):
        """ kind of a wrapper to writing a line to the output file"""
        self.output_file.write(command)

    def _write_pop_to_predefined(self, segment, index):
        """ poping tha last value in the stack to the segment[index]"""
        temp = TEMP_REG.format(str(13))

        self._write_assign_to_a(index)
        self._write(A_TO_D)
        self._write_assign_to_a(self.REG_NAMES[segment])
        self._write('D=D+M\n')
        self._write_assign_to_a(temp)
        self._write(D_TO_M)
        self._write(POP_TO_D)
        self._write_assign_to_a(temp)
        self._write(M_TO_A)
        self._write(D_TO_M)

    def _write_pop(self, segment, index):
        """ writing the pop asm commands  """

        if segment in self.REG_NAMES:
            self._write_pop_to_predefined(segment, index)
        elif segment == 'temp':
            self._write(POP_TO_D)
            cur_temp = TEMP_REG.format((PLC_HOLDER + int(index)))
            self._write_assign_to_a(cur_temp)
            self._write(D_TO_M)
        elif segment == 'pointer':
            self._write(POP_TO_D)
            self._write_assign_to_a(self.POINTER_IDX[index])
            self._write(D_TO_M)
        elif segment == 'static':
            self._write(POP_TO_D)
            self._write_assign_to_a(SEGMENTS_INDEX.format(os.path.basename(os.path.normpath(self.file_name)), index))
            self._write(D_TO_M)

    def write_push_pop(self, command, segment, index):
        """
        Writes the assembly code that is the translation of the given command, where command is wither C_PUSH or C_POP.
        :param command: C_PUSH or C_POP.
        :param segment: string.
        :param index: int.
        """
        if command == 'push':
            self._write_push(segment, index)
        elif command == 'pull':
            self._write_pop(segment, index)

    def write_arithmetic(self, command):
        """
        Writes the assembly code code that is the translation of the given arithmetic command.
        :param command: string.
        """
        if command in CodeWriter.BINARY_COMMANDS:
            self._write(POP_TO_D)
            if command in CodeWriter.COMPARING_BINARY_COMMANDS:
                self._write_compare_arithmetic(command)
            else:
                self._write(DECREASE_A)
                self._write(self.ARITHMETIC_COMMANDS[command])
                if command == 'eq':
                    self._write_eq()
        else:
            # command is unary
            self._write(self.ARITHMETIC_COMMANDS[command])

    def _write_assign_to_a(self, index):
        """ asm translation for assigning to a"""
        self.output_file.write(ASSIGN_TO_A.format(index))

    def _write_push(self, segment, index):
        """writing push command"""
        if segment == 'constant':
            self._write_assign_to_a(index)
            self._write(A_TO_D)
        else:
            if segment in self.REG_NAMES:
                self._write_assign_to_a(index)
                self._write(A_TO_D)
                self._write_assign_to_a(self.REG_NAMES[segment])
                self._write('A=D+M\n')
                self._write(M_TO_D)
            else:
                if segment == 'temp':
                    temp = TEMP_REG.format(TEMP_REG_INDEX + int(index))
                    self._write_assign_to_a(temp)
                elif segment == 'pointer':
                    self._write_assign_to_a(self.POINTER_IDX[index])
                elif segment == 'static':
                    self._write_assign_to_a(SEGMENTS_INDEX.format(os.path.basename(os.path.normpath(self.file_name))
                                                                  , index))
                self._write(M_TO_D)
        self._write(PUSH_D)

    def _write_compare_arithmetic(self, command):
        """ writing the arithmetic comperation commands and deals with overflaws """

        xbigger_name = 'XBIGGER' + str(self.label_idx)
        ybigger_name = 'YBIGGER' + str(self.label_idx)
        ypos_name = 'YPOS' + str(self.label_idx)
        end_name = 'END' + str(self.label_idx)
        treat_name = 'TREAT' + str(self.label_idx)
        xbigger_label = LABEL_LINE.format(xbigger_name)
        ybigger_label = LABEL_LINE.format(ybigger_name)
        ypos_label = LABEL_LINE.format(ypos_name)
        end_label = LABEL_LINE.format(end_name)
        treat_label = LABEL_LINE.format(treat_name)

        my_jmp = 'JGT' if command == 'gt' else 'JLT'

        self._write_assign_to_a(ypos_name)
        self._write(JUMP_COMMAND.format('D', my_jmp))
        self._write(TAKE_TO_D)
        self._write_assign_to_a(xbigger_name)
        self._write(JUMP_COMMAND.format('D', my_jmp))

        self._write_assign_to_a(treat_name)
        self._write(JUMP_COMMAND.format('0', 'JMP'))

        self._write(ypos_label)
        self._write(TAKE_TO_D)

        my_else_jmp = 'JLE' if command == 'gt' else 'JGE'

        self._write_assign_to_a(ybigger_name)
        self._write(JUMP_COMMAND.format('D', my_else_jmp))

        self._write(treat_label)
        self._write(TAKE_TO_D)

        self._write_assign_to_a(SP)
        self._write(M_TO_A)
        self._write('D=D-M\n')

        self._write_assign_to_a(xbigger_name)
        self._write(JUMP_COMMAND.format('D', my_jmp))

        self._write_assign_to_a(ybigger_name)
        self._write(JUMP_COMMAND.format('0', 'JMP'))

        self._write(xbigger_label)
        self._write_assign_to_a(SP)
        self._write('A=M-1\n')
        self._write(INT_TO_M.format(-1))
        self._write_assign_to_a(end_name)
        self._write(JUMP_COMMAND.format('0', 'JMP'))

        self._write(ybigger_label)
        self._write_assign_to_a(SP)
        self._write('A=M-1\n')
        self._write(INT_TO_M.format(0))

        self._write(end_label)

        self.label_idx += 1

    def close(self):
        """
        Closes the output file.
        """
        self.output_file.close()

    def _write_eq(self):
        """'write asm equality command"""
        iseq_name = 'ISEQ' + str(self.label_idx)
        end_name = 'END' + str(self.label_idx)
        iseq_label = LABEL_LINE.format(iseq_name)
        end_label = LABEL_LINE.format(end_name)
        self._write_assign_to_a(iseq_name)
        self._write(JUMP_COMMAND.format('D', 'JEQ'))
        self._write('@SP\nA=M-1\n')
        self._write(INT_TO_M.format(0))
        self._write_assign_to_a(end_name)

        self._write(JUMP_COMMAND.format('0', 'JMP'))
        self._write(iseq_label)

        self._write('@SP\nA=M-1\n')
        self._write(INT_TO_M.format(-1))

        self._write(end_label)

        self.label_idx += 1


class Parser:
    """Class that handles the parsing stage of the translation"""
    ARITHMETICS = {'add', 'neg', 'mult', 'sub', 'gt', 'eq', 'lt', 'and', 'or', 'not'}

    def __init__(self, path):
        """
        Opens the input file and gets ready to parse it.
        :param path: Path of the assembly code.
        """

        self.lines = self.first_run(path)
        self.index = -1
        self.cur_line = self.lines[self.index] if self.lines else None  # if lines isn't empty

    class Line:
        def __init__(self, command, arg1, arg2):
            self.command = command
            self.arg1 = arg1
            self.arg2 = arg2

        def __repr__(self):
            s = self.command
            if self.arg1 != "":
                s += ' ' + (self.arg1)
            if self.arg2 != "":
                s += ' ' + (self.arg2)
            return s

    def first_run(self, filepath):
        """
        Makes first run over code and removes comments and white spaces.
        In addition
        :param filepath: Path of the asm code.
        :return: List of all lines without comments and blank lines.
        """
        with open(filepath, READ_MODE) as file:
            code_lines = []
            for line in file:
                line = line.split('//', 1)[0].replace('\t', '').replace('\n', '').replace('\r', '').strip()

                if line != "":
                    command = line.partition(' ')[0]
                    arg1 = line.partition(' ')[-1].partition(' ')[0]
                    arg2 = line.partition(' ')[-1].partition(' ')[-1]
                    code_lines.append(Parser.Line(command, arg1, arg2))

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
            self.cur_line = self.lines[self.index]

    def reset(self):
        """
        Resets the Parser to the beginning of the code file.
        """
        self.index = 0

    def command_type(self):
        """
        :return: the command type of the current line
        """
        line = self.cur_line
        if line.command in Parser.ARITHMETICS:
            return C_ARITHMETICS
        elif line.command == PUSH:
            return C_PUSH
        elif line.command == POP:
            return C_POP
        elif line.command is LABEL:
            return C_LABEL
        elif line.command is IF:
            return C_IF
        elif line.command is GOTO:
            return C_GOTO
        elif line.command is FUNCTION:
            return C_FUNCTION
        elif line.command is CALL:
            return C_CALL
        elif line.command is RETURN:
            return C_RETURN

    def arg1(self):
        """
        :return: first argument of the current line
        """
        return self.cur_line.arg1

    def arg2(self):
        """
        :return: second argument of the current line, an integer
        """
        return self.cur_line.arg2

    def command(self):
        return self.cur_line.command


if __name__ == "__main__":

    # Input string from user
    input_str = sys.argv[1]
    if os.path.isfile(input_str):
        if not os.path.isdir(input_str) and input_str.endswith(".vm"):
            # Translation of the single file
            vm_file = input_str
            code_writer = CodeWriter(vm_file, NOT_DIR)
            code_writer.translate(vm_file)
            code_writer.close()

    elif os.path.isdir(input_str):  # file is directory
        vm_dir = input_str
        code_writer = CodeWriter(vm_dir, IS_DIR)
        code_writer.translate_dir(vm_dir)
        code_writer.close()
