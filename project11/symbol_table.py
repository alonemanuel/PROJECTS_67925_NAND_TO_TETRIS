class SymbolTable:
    """
    This module provides services for creating, populating, and using a symbol table. Recall that
    each symbol has a scope from which it is visible in the source code. In the symbol table, each
    symbol is given a running number (index) within the scope, where the index starts at 0 and is
    reset when starting a new scope. The following kinds of identifiers may appear in the symbol
    table:
        Static: Scope: class.
        Field: Scope: class.
        Argument: Scope: subroutine (method/function/constructor).
        Var: Scope: subroutine (method/function/constructor).
    When compiling code, any identifier not found in the symbol table may be assumed to be a
    subroutine name or a class name. Since the Jack language syntax rules suffice for distinguishing
    between these two possibilities, and since no "linking" needs to be done by the compiler, these
    identifiers do not have to be kept in the symbol table.
    """
    CLASS_VAR_KINDS = {'static', 'field'}
    SUBROUTINE_VAR_KINDS = {'argument', 'var'}
    SUBROUTINE_KINDS = {'constructor', 'function', 'method'}

    def __init__(self):
        """
        Creates new empty symbol table.
        """
        self._class_table = {}
        self._subroutine_table = {}
        self._class_name = ''
        self._kind_counter = {'field': 0, 'static': 0, 'argument': 0, 'var': 0}

    def set_class_name(self, class_name):
        """
        Sets the class name
        :param class_name:
        :return:
        """
        self._class_name = class_name

    def get_class_name(self):
        """
        Gets the class name.
        :return:
        """
        return self._class_name

    def start_subroutine(self):
        """
        Starts a new subroutine scope (i.e. erases all names in the previous subroutine's scope.)
        :return:
        """

        self._subroutine_table.clear()
        self._kind_counter['argument'] = 0
        self._kind_counter['var'] = 0

    def define(self, name, symbol_type, kind):
        """
        Defines a new identifier of a given name, type, and kind and assigns it a running index.
        STATIC and FIELD identifiers have a class scope, while ARG and VAR identifiers have a subroutine scope.
        :param name: string
        :param symbol_type: string
        :param kind: STATIC, FIELD, or ARG
        :return: int
        """

        if kind == 'var' and name in self._subroutine_table:
            self._kind_counter[kind] += 1
            return
        relevant_table = self._get_table_from_kind(kind)
        relevant_table[name] = (symbol_type, kind, self._kind_counter[kind])
        self._kind_counter[kind] += 1

    def var_count(self, kind):
        """
        Returns the number of variables of the given kind already defined in the current scope.
        :param kind: STATIC, FIELD, ARG, or VAR
        :return: int
        """
        return self._kind_counter[kind]

    def kind_of(self, name):
        """
        Returns the kind of the names identifier in the current scope. Returns NONE if the identifier is unknown in the
        current scope.
        :param name: string
        :return: STATIC, FIELD, ARG, VAR, NONE
        """
        relevant_table = self._get_table_from_name(name)
        return relevant_table[name][1] if relevant_table else None

    def type_of(self, name):
        """
        Returns the type of the named identifier in the current scope.
        :param name: string
        :return: string
        """
        relevant_table = self._get_table_from_name(name)
        return relevant_table[name][0] if relevant_table else None

    def index_of(self, name):
        """
        Returns the index assigned to named identifier.
        :param name: string
        :return: int
        """
        relevant_table = self._get_table_from_name(name)
        return relevant_table[name][2] if relevant_table else None

    def class_of(self, name):
        relevant_table = self._get_table_from_name(name)
        return relevant_table[name][0] if relevant_table else None

    # Helpers

    def _get_table_from_name(self, name):
        """
        Returns the relevant table according to the name.
        :param name: string
        :return: table
        """
        if name in self._subroutine_table and name in self._class_table:
            return self._subroutine_table
        elif name in self._subroutine_table:
            return self._subroutine_table
        elif name in self._class_table:
            return self._class_table

    def _get_table_from_kind(self, kind):
        """
        Returns the relevant table according to the kind.
        :param kind: string
        :return: table
        """
        if kind in self.CLASS_VAR_KINDS:
            return self._class_table
        if kind in self.SUBROUTINE_VAR_KINDS:
            return self._subroutine_table
        else:
            raise Exception("Error: no such kind '" + kind + "'.")
