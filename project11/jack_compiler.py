import os
from compilation_engine import CompilationEngine


class JackCompiler:
    """
    The program receives a name of a file or a directory, and compiles the file, or all the jack files in this directory.
    For each Xxx.jack file, it creates a Xxx.vm file in the same directorry.
    """

    def __init__(self, input_path):
        """
        Constructor for the JackAnalyzer.
        :param input_path: either a .jack file, or a directory with .jack files in it.
        """
        self._input_path = input_path
        self.compilation_engine = None

    def compile(self):
        """
        Compiles the file.
        """
        if os.path.isfile(self._input_path):
            self._compile_single_file(self._input_path)
        elif os.path.isdir(self._input_path):  # file is directory
            self._compile_dir(self._input_path)
        else:
            print("Error: Invalid path.")

    def _compile_single_file(self, input_path):
        """
        Compiles a single .jack file.
        :param input_path: file input.
        """
        output_path = input_path.replace('.jack', '.vm')
        self.compilation_engine = CompilationEngine(input_path, output_path)
        self.compilation_engine.compile_class()

    def _compile_dir(self, input_path):
        """
        Compiles directory of .jack files.
        :param input_path: directory path.
        """
        for item in os.listdir(input_path):
            file = os.path.join(input_path, item)
            if file.endswith('.jack') and os.path.isfile(file):
                self._compile_single_file(file)


if __name__ == "__main__":
    # Input string from user
    input_file = os.sys.argv[1]
    compiler = JackCompiler(input_file)
    compiler.compile()
