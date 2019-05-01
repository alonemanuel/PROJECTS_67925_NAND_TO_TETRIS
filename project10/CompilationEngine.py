from JackTokenizer import JackTokenizer
import os

WRITING_MODE = 'w'


class CompilationEngine:
    """
    Module for compiling a single .jack files. Has one public function, compile, which compiles a .jack file into an
    .xml file.
    """
    TAB = '\t'
    END_OF_LINE = '\n'

    CLASS_VAR_DECS = {'static', 'field'}  # class variable prefixes
    SUBROUTINE_DECS = {'constructor', 'function', 'method'}  # subroutine declaration prefixes
    TYPES = {'int', 'char', 'boolean'}  # types of variables
    STATEMENTS = {'let', 'if', 'while', 'do', 'return'}
    OPS = {'+', '-', '*', '/', '&', '|', '<', '>', '='}  # operators
    UNARY_OPS = {'-', '~'}  # unary operators
    CONSTANTS = {'INT_CONST', 'STRING_CONST'}

    def __init__(self, input_file, output_file):
        """
        Constructor for a the compilation engine.
        :param input_file: .jack file to read from.
        :param output_file: .xml file to write to.
        """
        self.tok = JackTokenizer(input_file)  # tokenizer
        self.output_file = open(output_file, WRITING_MODE)
        self._indent = 0

    def compile(self):
        """
        Compiles the file.
        """
        self.call_non_terminal(self.compile_class, 'class', True)  # compiles with that special 'class' header

    def call_non_terminal(self, func, header, is_eof=False):
        """
        Wrappes a non-terminal (recursive) element. Adds the appropriate line-breaks and spacing.
        :param func: function to be wrapped.
        :param header: header and footer tags.
        :param is_eof: in case the element is at the end of the file.
        """
        self.open_header(header)
        self._indent += 1
        func()
        self._indent -= 1
        self.close_header(header, is_eof)

    def compile_tokens(self):
        """
        Compiles multiple tokens.
        """
        if self.tok.has_more_tokens():
            self.tok.advance()
            self.call_non_terminal(self.compile_class, 'class')

    def compile_class(self):
        """
        Compiles a class.
        """
        if self.tok.has_more_tokens():
            self.tok.advance()
            self.write_tag('class', self.tok.token, 'keyword')
            self.write_class_name()
            self.write_in_curly_brackets(self.compile_class_var_decs, self.compile_subroutine_decs)

    def compile_class_var_decs(self):
        """
        Compiles class variable declarations.
        """
        while self.tok.token in self.CLASS_VAR_DECS:
            self.call_non_terminal(self.compile_class_var_dec, 'classVarDec')

    def compile_subroutine_decs(self):
        """
        Compiles subroutine declarations.
        """
        while self.tok.token in self.SUBROUTINE_DECS:
            self.call_non_terminal(self.compile_subroutine_dec, 'subroutineDec')

    def compile_var_dec(self, is_class=False):
        """
        Compiles a variable declaration.
        :param is_class: whether the variables are class variables.
        """
        self.write_keyword(self.CLASS_VAR_DECS if is_class else 'var')
        self.write_type()
        self.write_var_name()
        while self.tok.token == ',':
            self.write_symbol(',')
            self.write_var_name()
        self.write_semi_col()

    def write_type(self, is_subroutine=False):
        """
        Writes a 'type' element to the output file.
        :param is_subroutine: true iff the types are a subroutine return types.
        """
        is_identifier = (self.tok.token_type == 'IDENTIFIER')
        expected = 'IDENTIFIER' if is_identifier else (self.TYPES.union({'void'}) if is_subroutine else self.TYPES)
        actual = self.tok.token_type if is_identifier else self.tok.token
        tag = 'identifier' if is_identifier else 'keyword'
        label = self.tok.token
        self.write_tag(expected, actual, tag, label)

    def compile_subroutine_dec(self):
        """
        Compiles a subroutine declaration.
        """
        self.write_keyword(self.SUBROUTINE_DECS)
        self.write_type(True)
        self.write_subroutine_name()
        self.write_symbol('(')
        self.call_non_terminal(self.compile_parameter_list, 'parameterList')
        self.write_symbol(')')
        self.call_non_terminal(self.compile_subroutine_body, 'subroutineBody')

    def compile_parameter_list(self):
        """
        Compiles parameters list
        """
        if not self.tok.token == ')':
            self.write_type()
            self.write_tag('IDENTIFIER', self.tok.token_type, 'identifier', self.tok.token)
            while self.tok.token == ',':
                self.write_tag(',', self.tok.token, 'symbol', self.tok.token)
                self.write_type()
                self.write_tag('IDENTIFIER', self.tok.token_type, 'identifier', self.tok.token)

    def compile_class_var_dec(self):
        """
        Compiles class variables declaration.
        """
        self.compile_var_dec(True)

    def compile_subroutine_body(self):
        """
        Compiles subroutine body.
        """
        self.write_symbol('{')
        while self.tok.token == 'var':
            self.call_non_terminal(self.compile_var_dec, 'varDec')
        self.call_non_terminal(self.compile_statements, 'statements')
        self.write_tag('}', self.tok.token, 'symbol', self.tok.token)

    def compile_subroutine_call(self):
        """
        Compiles a call to a subroutine.
        """
        self.write_identifier()
        if self.tok.token == '.':
            self.write_symbol('.')
            self.write_subroutine_name()
        self.write_symbol('(')
        self.call_non_terminal(self.compile_expression_list, 'expressionList')
        self.write_symbol(')')

    def write_subroutine_args(self):
        """
        Write subroutine's args to output file.
        """
        if not self.tok.token == ')':
            self.call_non_terminal(self.compile_expression_list)

    def compile_statements(self):
        """
        Compiles statements.
        """
        while self.tok.token in self.STATEMENTS:
            self.compile_statement()

    def compile_statement(self):
        """
        Compiles statement.
        """
        if self.tok.token == 'let':
            self.call_non_terminal(self.compile_let, 'letStatement')
            return
        if self.tok.token == 'if':
            self.call_non_terminal(self.compile_if, 'ifStatement')
            return
        if self.tok.token == 'while':
            self.call_non_terminal(self.compile_while, 'whileStatement')
            return
        if self.tok.token == 'do':
            self.call_non_terminal(self.compile_do, 'doStatement')
            return
        if self.tok.token == 'return':
            self.call_non_terminal(self.compile_return, 'returnStatement')
            return

    def compile_do(self):
        """
        Compiles a do statement.
        """
        self.write_keyword('do')
        self.compile_subroutine_call()
        self.write_semi_col()

    def compile_let(self):
        """
        Compiles a let statement.
        """
        self.write_keyword('let')
        self.write_var_name()
        if self.tok.token == '[':
            self.write_symbol('[')
            self.call_non_terminal(self.compile_expression, 'expression')
            self.write_symbol(']')
        self.write_symbol('=')
        self.call_non_terminal(self.compile_expression, 'expression')
        self.write_semi_col()

    def compile_while(self):
        """
        Compiles a while statement.
        """
        self.write_keyword('while')
        self.write_symbol('(')
        self.call_non_terminal(self.compile_expression, 'expression')
        self.write_symbol(')')
        self.write_symbol('{')
        self.call_non_terminal(self.compile_statements, 'statements')
        self.write_symbol('}')

    def compile_return(self):
        """
        Compiles a return statement.
        """
        self.write_keyword('return')
        if not self.tok.token == ';':
            self.call_non_terminal(self.compile_expression, 'expression')
        self.write_semi_col()

    def compile_if(self):
        """
        Compiles an if statement.
        """
        self.write_keyword('if')
        self.write_symbol('(')
        self.call_non_terminal(self.compile_expression, 'expression')
        self.write_symbol(')')
        self.write_symbol('{')
        self.call_non_terminal(self.compile_statements, 'statements')
        self.write_symbol('}')
        if self.tok.token == 'else':
            self.write_keyword('else')
            self.write_symbol('{')
            self.call_non_terminal(self.compile_statements, 'statements')
            self.write_symbol('}')

    def compile_expression(self):
        """
        Compiles an expression.
        """
        self.call_non_terminal(self.compile_term, 'term')
        while self.tok.token in self.OPS:
            self.write_symbol(self.OPS)
            self.call_non_terminal(self.compile_term, 'term')

    def compile_term(self):
        """
        Compiles term.
        """
        token = self.tok.token
        if token == '(':
            self.write_symbol('(')
            self.call_non_terminal(self.compile_expression, 'expression')
            self.write_symbol(')')
            return
        if self.tok.token_type in self.CONSTANTS:
            self.write_const()
            return
        if self.tok.token_type == 'KEYWORD':
            self.write_keyword(token)
            return
        if self.tok.token_type == 'IDENTIFIER':
            self.compile_identifier_term()
            return
        if self.tok.token in self.UNARY_OPS:
            self.write_symbol(self.tok.token)
            self.call_non_terminal(self.compile_term, 'term')
            return

    def compile_identifier_term(self):
        """
        Compiles an identifier term.
        """
        if self.tok.peek() == '.' or self.tok.peek() == '(':
            self.compile_subroutine_call()
            return
        self.write_identifier()
        if self.tok.token == '[':
            self.write_symbol('[')
            self.call_non_terminal(self.compile_expression, 'expression')
            self.write_symbol(']')

    def compile_expression_list(self):
        """
        Compiles an expression list.
        """
        if not self.tok.token == ')':
            self.call_non_terminal(self.compile_expression, 'expression')
            while self.tok.token == ',':
                self.write_symbol(',')
                self.call_non_terminal(self.compile_expression,
                                       'expression')

    def write_in_curly_brackets(self, *funcs):
        """
        Write functions enclosed in curly brackets.
        :param funcs: function to call.
        """
        self.write_in_all_brackets(True, *funcs)

    def write_in_brackets(self, *funcs):
        """
        Write functions enclosed in round brackets.
        :param funcs: function to call.
        """
        self.write_in_all_brackets(False, *funcs)

    def write_in_all_brackets(self, is_curly, *funcs):
        """
        Writes functions in brackets.
        :param is_curly: true iff functions should be enclosed in curly brackets.
        :param funcs: function to call.
        """
        self.write_symbol('{' if is_curly else '(')
        for func in funcs:
            func()
        self.write_symbol('}' if is_curly else ')')

    def write_subroutine_name(self):
        """
        Writes a subroutine name to the output file.
        """
        self.write_identifier()

    def write_class_name(self):
        """
        Writes a class name to the output file.
        """
        self.write_identifier()

    def write_var_name(self):
        """
        Writes variable name to the output file.
        :return:
        """
        self.write_identifier()

    def write_const(self):
        """
        Writes a constant to the output file.
        """
        if self.tok.token_type == 'STRING_CONST':  # handles string constants
            self.write_tag(self.CONSTANTS, self.tok.token_type, 'stringConstant', self.tok.token)
            return
        if self.tok.token_type == 'INT_CONST':  # handles int constants
            self.write_tag(self.CONSTANTS, self.tok.token_type, 'integerConstant', self.tok.token)
            return

    def write_symbol(self, expected):
        """
        Writes a synbol to the output file.
        :param expected: the expected domain of the symbol.
        """
        self.write_tag(expected, self.tok.token, 'symbol', self.tok.token)

    def write_keyword(self, expected):
        """
        Writes a keyword to the output file.
        :param expected: the expected domain of the keyword.
        """
        self.write_tag(expected, self.tok.token, 'keyword', self.tok.token)

    def write_identifier(self):
        """
        Writes an identifier to the output file.
        """
        self.write_tag('IDENTIFIER', self.tok.token_type, 'identifier', self.tok.token)

    def write_semi_col(self):
        """
        Writes a semi-colon to the output file.
        """
        self.write_tag(';', self.tok.token, 'symbol', self.tok.token)

    def open_tag(self, tag):
        """
        Writes an opening tag.
        :param tag: the tag.
        """
        return '<' + tag + '>'

    def close_tag(self, tag):
        """
        Writes an closing tag.
        :param tag: the tag.
        """
        return '</' + tag + '>'

    def open_header(self, header):
        """
        Opens a header to the output file.
        :param header: the header.
        """
        self.output_file.write(self.TAB * self._indent)
        self.output_file.write(self.open_tag(header) + self.END_OF_LINE)

    def close_header(self, header, is_eof):
        """
        Closes header.
        :param header: the header.
        :param is_eof: true iff end of file.
        """
        self.output_file.write(self.TAB * self._indent)
        end_of_line = self.END_OF_LINE if not is_eof else ''
        self.output_file.write(self.close_tag(header) + end_of_line)

    def translate_symbol(self, symbol):
        """
        Translate a symbol to its xml appropriate version.
        :param symbol: the symbol to translate.
        """
        new_symbol = symbol.replace('&', '&amp;')
        new_symbol = new_symbol.replace('<', '&lt;')
        new_symbol = new_symbol.replace('>', '&gt;')
        return new_symbol.replace('"', '&quot;')

    def write_tag(self, expected, actual, tag, label=False):
        """
        Writes a tag to the output file.
        :param expected: expected domain for the writing.
        :param actual: actual writing value.
        :param tag: tag to write.
        :param label: label to put inside tags.
        """
        # if actual != expected
        if (type(expected) is set and actual not in expected) or (type(expected) is str and not actual == expected):
            if type(expected) is set:
                raise Exception("Compilation error. Expected: " + repr(expected) + ', got: ' + actual)
            else:
                raise Exception("Compilation error. Expected: " + expected + ', got: ' + actual)

        # else - writing is valid
        self.output_file.write(self.TAB * self._indent)
        self.output_file.write(
            self.open_tag(tag) + ' ' + self.translate_symbol(label if label else actual) + ' ' + self.close_tag(
                tag) + self.END_OF_LINE)
        if self.tok.has_more_tokens():
            self.tok.advance()
