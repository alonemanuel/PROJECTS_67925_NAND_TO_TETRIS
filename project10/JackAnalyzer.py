import os
import sys
from CompilationEngine import CompilationEngine

XML_EXTENSION = '.xml'
JACK_EXTENSION = '.jack'
INVALID_FILE_MSG = "input should be a file or a directory"


class JackAnalyzer:
    """
    Main module for analyzing and compiling .jack files. Has one public function, compile, that compiles either single
    files or directories.
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
            print(INVALID_FILE_MSG)

    def _compile_single_file(self, input_path):
        """
        Compiles a single .jack file.
        :param input_path: file input.
        """
        output_path = input_path.replace(JACK_EXTENSION, XML_EXTENSION)
        self.compilation_engine = CompilationEngine(input_path, output_path)
        self.compilation_engine.compile()

    def _compile_dir(self, input_path):
        """
        Compiles directory of .jack files.
        :param input_path: directory path.
        """
        for item in os.listdir(input_path):
            file = os.path.join(input_path, item)
            if file.endswith(JACK_EXTENSION) and os.path.isfile(file):
                self._compile_single_file(file)


if __name__ == "__main__":
    # Input string from user
    input_file = sys.argv[1]
    analyzer = JackAnalyzer(input_file)
    analyzer.compile()
