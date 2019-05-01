import os
import sys

# main asm commands
BOOTSTRAP = '@256\nD=A\n@SP\nM=D\n'
SEPERATOR = '$'
D_TO_A = 'A=D\n'
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
PUSH_ZERO = '@SP\nAM=M+1\nA=A-1\nM=0\n'
D_TO_M = 'M=D\n'
A_TO_D = 'D=A\n'
M_TO_A = 'A=M\n'
M_TO_D = 'D=M\n'
SEGMENTS_INDEX = '{0}.{1}'
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

    def __init__(self, input_file, bootstrap_flag):
        """
        Opens the output file/stream and gets ready to write into it.
        :param input_file: output file / stream.
        """
        self.temp_idx = 0
        self.function_name = ''
        self._parser = None
        self.label_idx = 0
        self.file_name = None
        self.output_file = open(input_file, WRITING_MODE)
        if bootstrap_flag:
            self._write(BOOTSTRAP)
            self._write_call('Sys.init', '0')

    def set_file_name(self, file_name):
        """
        Informs the code writer that the translation of a new VM file has started
        :param file_name: string.
        """
        self.file_name = file_name
        self._parser = Parser(file_name)

    def translate_dir(self, input_str):
        """ translates firectory by calling translate on all its files """
        for item in os.listdir(input_str):
            file = os.path.join(input_str, item)
            if file.endswith('.vm') and os.path.isfile(file):
                code_writer.translate(file)

    def translate(self, filename):

        """ performing the translation process"""
        self.set_file_name(filename)

        while self._parser.has_more_commands():
            self._parser.advance()
            # self._write("\n\t//" + str(self._parser.cur_line) + "\n\n")

            command, command_type = self._parser.command(), self._parser.command_type()
            arg1, arg2 = self._parser.arg1(), self._parser.arg2()
            if self.function_name != '':
                label = self.function_name + SEPERATOR
            else:
                label = ''

            if command_type == C_ARITHMETICS:
                self.write_arithmetic(command)
            elif command_type == C_PUSH:
                self._write_push(arg1, arg2)
            elif command_type == C_POP:
                self._write_pop(arg1, arg2)
            elif command_type == C_IF:
                self._write_if(label + arg1)
            elif command_type == C_LABEL:
                self._write_label(label + arg1)
            elif command_type == C_FUNCTION:
                self._write_function(arg1, arg2)
            elif command_type == C_CALL:
                self._write_call(arg1, arg2)
            elif command_type == C_RETURN:
                self._write_return()
            elif command_type == C_GOTO:
                self._write_goto(label + arg1)

    def _write(self, command):
        """ kind of a wrapper to writing a line to the output file"""
        self.output_file.write(command)

    def _write_assign_to_a(self, index):
        """ asm translation for assigning to a"""
        self.output_file.write(ASSIGN_TO_A.format(index))

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

    def _write_if(self, arg1):
        """ writes goto-if command to output file """
        self._write(POP_TO_D)
        self._write_assign_to_a(arg1)
        self._write(JUMP_COMMAND.format('D', 'JNE'))

    def _write_label(self, arg1):
        """ writes goto command to output file """
        self._write(LABEL_LINE.format(arg1))

    def _write_function(self, function_name, arg2):
        """ writing function command """
        self._write_label(function_name)
        for i in range(int(arg2)):
            self._write(PUSH_ZERO)
        self.function_name = function_name

    def _write_call(self, function_name, n_args):
        """ writing call command """

        # self.function_name = function_name
        # push return address
        return_label = function_name + str(self.label_idx)
        self._write_assign_to_a(return_label)
        self._write(A_TO_D)
        self._write(PUSH_D)
        # push LCL
        self._write_assign_to_a('LCL')
        self._write(M_TO_D)
        self._write(PUSH_D)
        # push ARG
        self._write_assign_to_a('ARG')
        self._write(M_TO_D)
        self._write(PUSH_D)
        # push THIS
        self._write_assign_to_a('THIS')
        self._write(M_TO_D)
        self._write(PUSH_D)
        # push THAT
        self._write_assign_to_a('THAT')
        self._write(M_TO_D)
        self._write(PUSH_D)
        # ARG = SP - 5 - nArgs
        self._write_assign_to_a(n_args)
        self._write(A_TO_D)
        self._write_assign_to_a(SP)
        self._write('D=M-D\n')
        self._write_assign_to_a(5)
        self._write('D=D-A\n')
        self._write_assign_to_a('ARG')
        self._write(D_TO_M)
        # LCL = SP
        self._write_assign_p1_to_p2(SP, 'LCL')
        # goto functionName
        self._write_goto(function_name)
        # (return address)
        self._write(LABEL_LINE.format(return_label))
        self.label_idx += 1
        # self.function_name = ''

    def _write_return(self):
        """ write the return asm commands to the output file"""
        end_frame = TEMP_REG.format(14)
        ret_address = TEMP_REG.format(15)
        # endFrame = LCL
        self._write_assign_p1_to_p2('LCL', end_frame)
        # retAddre = *(endframe-5)
        self._write_assign_to_a(5)
        self._write(A_TO_D)
        self._write_assign_p1_to_p2(end_frame, ret_address, modify_a_command='A=M-D\n')
        # ARG = pop()
        # self._write_assign_p1_to_p2(SP, 'ARG', change_p1='A=M-1\n')
        self._write_assign_to_a(SP)
        self._write('A=M-1\n')
        self._write(M_TO_D)
        self._write_assign_to_a('ARG')
        self._write(M_TO_A)
        self._write(D_TO_M)
        # SP = ARG+1
        self._write_assign_to_a('ARG')
        self._write(M_TO_D)
        self._write_assign_to_a(SP)
        self._write('M=D+1\n')
        # THAT = *(endframe-1)
        self._write_assign_p1_to_p2(end_frame, 'THAT', modify_a_command='A=M-1\n')
        # THIS = *(endframe-2)
        self._write_assign_to_a(2)
        self._write(A_TO_D)
        self._write_assign_p1_to_p2(end_frame, 'THIS', modify_a_command='A=M-D\n')
        # ARG = *(endframe-3)
        self._write_assign_to_a(3)
        self._write(A_TO_D)
        self._write_assign_p1_to_p2(end_frame, 'ARG', modify_a_command='A=M-D\n')
        # LCL = *(endframe-4)
        self._write_assign_to_a(4)
        self._write(A_TO_D)
        self._write_assign_p1_to_p2(end_frame, 'LCL', modify_a_command='A=M-D\n')
        # goto retAddr
        self._write_assign_to_a(ret_address)
        self._write(M_TO_A)
        self._write(JUMP_COMMAND.format(0, 'JMP'))
        # self.function_name = ''

    def _write_assign_p1_to_p2(self, p1, p2, modify_a_command=None):
        """ writing the assembly commands required for p2=p1 for two variables p1,p2.
        modify_a_command parameter is used when A instructions modification is required """
        self._write_assign_to_a(p1)
        if modify_a_command:
            self._write(modify_a_command)
        self._write(M_TO_D)

        self._write_assign_to_a(p2)
        self._write(D_TO_M)



    def _write_goto(self, arg1):
        """ writing go-to commands to asm file """
        self._write_assign_to_a(arg1)
        self._write(JUMP_COMMAND.format(0, 'JMP'))

    def close(self):
        """
        Closes the output file.
        """
        self.output_file.close()

    def _write_temp(self, index):
        pass


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
                line = (line.split('//', 1)[0].replace('\t', '').replace('\n', ''))

                if line != "":
                    command = line.partition(' ')[0]
                    arg1 = line.partition(' ')[-1].partition(' ')[0]
                    arg2 = line.partition(' ')[-1].partition(' ')[-1].strip()
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
        elif line.command == LABEL:
            return C_LABEL
        elif line.command == IF:
            return C_IF
        elif line.command == GOTO:
            return C_GOTO
        elif line.command == FUNCTION:
            return C_FUNCTION
        elif line.command == CALL:
            return C_CALL
        elif line.command == RETURN:
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
        """
        :return: current line command
        """
        return self.cur_line.command


if __name__ == "__main__":

    bootstrap_flag = True

    # Input string from user
    input_str = sys.argv[1]
    if os.path.isfile(input_str):
        # Translation of the single file
        vm_file = input_str
        output_file = input_str.replace('.vm', '.asm')
        code_writer = CodeWriter(output_file, bootstrap_flag)
        code_writer.translate(vm_file)
        code_writer.close()

    elif os.path.isdir(input_str):  # file is directory
        vm_dir = input_str
        basename = os.path.basename(input_str.rstrip(os.path.sep)) + '.asm'
        output_file = os.path.join(input_str, basename)
        code_writer = CodeWriter(output_file, bootstrap_flag)
        code_writer.translate_dir(vm_dir)
        code_writer.close()
    else:
        print("input should be a file or a directory")
