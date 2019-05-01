class VMWriter:
    """
    This class writes VM commands into a file. It encapsulates the VM command syntax.
    """

    _GENERAL_COMMAND = '{} {{}} {{}}'  # used for formatting in the specific command
    _PUSH = _GENERAL_COMMAND.format('push')  # used for formatting in the segment and index
    _POP = _GENERAL_COMMAND.format('pop')

    def __init__(self, output_path):
        """
        Creates a new file and prepares it for writing VM commands.
        :param output_path:
        """
        self._file = open(output_path, 'w')
        # TODO when do we close the file?

    def write_push(self, segment, index):
        """
        Writes a VM push command.
        :param segment: CONST, ARG, LOCAL, STATIC, THIS, THAT, POINTER, TEMP
        :param index: int
        :return:
        """
        self._write_line(VMWriter._PUSH.format(segment, index))

    def write_pop(self, segment, index):
        """
        Writes a VM pop command.
        :param segment: CONST, ARG, LOCAL, STATIC, THIS, THAT, POINTER, TEMP
        :param index: int
        :return:
        """
        self._write_line(VMWriter._POP.format(segment, index))

    def write_arithmetic(self, command):
        """
        Writes a VM arithmetic command.
        :param command: ADD, SUB, NEG, EQ, GT, LT, AND, OR, NOT
        :return:
        """
        self._write_line(command)

    def write_label(self, label):
        """
        Writes a VM label command.
        :param label: string
        :return:
        """
        self._write_line('label ' + label)  # TODO generate unique labels?

    def write_go_to(self, label):
        """
        Writes a VM Go-To command.
        :param label: string
        :return:
        """
        self._write_line('goto ' + label)

    def write_if(self, label):
        """
        Writes a VM if-GoTo command.
        :param label: string
        :return:
        """
        self._write_line('if-goto ' + label)

    def write_call(self, name, n_of_args):
        """
        Writes a VM call command.
        :param name: string
        :param nArgs: int
        :return:
        """
        self._file.write('{0} {1} {2}\n'.format('call', name, n_of_args))

    def write_function(self, name, n_of_locals):
        """
        Writes a VM function command.
        :param name: string
        :param nLocals: int
        :return:
        """
        self._file.write('function {} {}\n'.format(name, n_of_locals))

    def write_return(self):
        """
        Writes a VM return command.
        :return:
        """
        self._file.write('return\n')

    def close(self):
        """
        Closes the output file.
        :return:
        """
        self._file.close()

    # Helper functions:

    def _write_line(self, line):
        """
        Writes a line to the file in a new line.
        :param line: lne to write
        :return:
        """
        self._file.write(line + '\n')

    def write_goto(self, label):
        self._file.write('{0} {1}\n'.format('goto', label))
