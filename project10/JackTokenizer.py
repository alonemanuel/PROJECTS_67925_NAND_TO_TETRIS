SYMBOL = 'SYMBOL'
KEYWORD = 'KEYWORD'
INT_CONST = 'INT_CONST'
IDENTIFIER = 'IDENTIFIER'
STRING_CONST = 'STRING_CONST'
COMMENT_BLOCK = 'COMMENT_BLOCK'
NEW_LINE = '\n'
COMMENT = 'COMMENT'
CODE = 'CODE'
READ_MODE = 'r'


class JackTokenizer:
    keywords = {'class', 'method', 'function', 'constructor', 'int', 'boolean', 'char', 'void', 'var', 'static',
                'field', 'let', 'do', 'if', 'else', 'while', 'return', 'true', 'false', 'null', 'this'}
    symbols = {'{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~'}

    def __init__(self, file_path):
        self.idx = 0

        # a functions dictionary for each comment type
        self.comment_function = {COMMENT: self.comment_check,
                                 COMMENT_BLOCK: self.comment_block_check, }

        # a functions dictionary for each token type
        self.modes_function = {SYMBOL: self.symbol_check,
                               INT_CONST: self.int_check,
                               IDENTIFIER: self.identifier_check,
                               STRING_CONST: self.string_check}

        self.file_path = file_path
        self.token_type = ''
        self.temp_token = ''
        self.token = ''
        self.code = ''
        self.next_token = ''
        self.mode = CODE
        self.token_generator = self.parse_file()
        self.next_token = next(self.token_generator)

    def has_more_tokens(self):
        """ return weather there is more tokens in the file """
        return self.next_token and self.mode != CODE

    def advance(self):
        """ set the token to be the next token """
        self.token = self.next_token[1:] if self.mode == STRING_CONST else self.next_token
        self.next_token = next(self.token_generator)

    def parse_file(self):
        """ a generator function who parse the file to tokens """
        with open(self.file_path, READ_MODE) as file:
            self.code = file.read()
            while self.idx < len(self.code):
                if self.mode == CODE:
                    if self.code[self.idx].isspace():
                        self.idx += 1
                        continue
                    self.set_mode()
                elif COMMENT in self.mode:
                    self.comment_function[self.mode]()
                    self.idx += 1
                else:
                    self.temp_token += self.code[self.idx]
                    if self.modes_function[self.mode]():
                        yield self.temp_token
                        self.reset_type_and_mode()
                    self.idx += 1
            yield None

    def peek(self):
        """ peek to the next token """
        return self.next_token[1:] if self.mode == STRING_CONST else self.next_token

    def set_mode(self):
        """ set the parsing mode according to the parser code current character """
        if self.code[self.idx] == '/':
            if len(self.code) > self.idx + 1 and self.code[self.idx + 1].startswith('/'):
                self.mode = COMMENT
                return
            elif len(self.code) > self.idx + 1 and self.code[self.idx + 1:].startswith('**'):
                self.mode = COMMENT_BLOCK
                return
        if self.code[self.idx].isalpha():
            self.mode = IDENTIFIER
        elif self.code[self.idx].isdigit():
            self.mode = INT_CONST
        elif self.code[self.idx] == '"':
            self.mode = STRING_CONST
        elif self.code[self.idx] in self.symbols:
            self.mode = SYMBOL

    def reset_type_and_mode(self):
        """ reset the token type, the temp token and the parsing mode """
        self.token_type = KEYWORD if self.temp_token in self.keywords else self.mode
        self.temp_token = ''
        self.mode = CODE

    def symbol_check(self):
        """ perform the specific check for a symbol token case """
        return True

    def int_check(self):
        """ perform the specific check for a int token case """
        return not (self.idx + 1 < len(self.code) and self.code[self.idx + 1].isdigit())

    def is_identifier(self):
        return self.code[self.idx + 1].isalpha() or self.code[self.idx + 1].isdigit() or self.code[self.idx + 1] == '_'

    def identifier_check(self):
        """ perform the specific check for a identifier token case """
        return not (self.idx + 1 < len(self.code) and self.is_identifier())

    def string_check(self):
        """ perform the specific check for a string token case """
        if self.idx + 1 < len(self.code) and self.code[self.idx + 1] == '"':
            self.idx += 1
            return True
        return False

    def comment_check(self):
        """ perform the specific check for a comment line case """
        if self.code[self.idx] == NEW_LINE:
            self.mode = CODE

    def comment_block_check(self):
        """ perform the specific check for a comment block case """
        if self.code[self.idx - 1:self.idx + 1] == '*/':
            self.mode = CODE

    def token_type(self):
        """ returns the type of the current token """
        return self.token_type

    def key_word(self):
        """ returns an keyword token """
        return self.token

    def symbol(self):
        """ returns a symbol token """
        return self.token

    def identifier(self):
        """ returns a identifier token """
        return self.token

    def int_val(self):
        """ returns a int constant token """
        return self.token

    def string_val(self):
        """ returns a string constant token """
        return self.token
