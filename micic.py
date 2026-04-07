import os
import argparse
from enum import Enum, auto

class TokenType(Enum):
    IDENTIFIER = auto()
    SEMICOLON = auto()
    KW_COMPONENT = auto()
    KW_SYSTEM = auto()
    KW_ARCHETYPE = auto()
    KW_WORLD = auto()
    KW_USE = auto()
    KW_INITIALIZE = auto()
    KW_DESTROY = auto()
    KW_PRE_UPDATE = auto()
    KW_UPDATE = auto()
    KW_POST_UPDATE = auto()
    LBRACE = auto()
    RBRACE = auto()
    EOF = auto()
    STRING = auto()
    C_BLOCK = auto()

KEYWORDS = {
    'component': TokenType.KW_COMPONENT,
    'system': TokenType.KW_SYSTEM,
    'archetype': TokenType.KW_ARCHETYPE,
    'world': TokenType.KW_WORLD,
    'use': TokenType.KW_USE,
    'initialize': TokenType.KW_INITIALIZE,
    'destroy': TokenType.KW_DESTROY,
    'pre_update': TokenType.KW_PRE_UPDATE,
    'update': TokenType.KW_UPDATE,
    'post_update': TokenType.KW_POST_UPDATE,
}

class Token:
    def __init__(self, lexer: Lexer, type: TokenType, value: str, line: int, col: int):
        self.lexer = lexer
        self.type = type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token(type: {self.type.name}, value: {self.value}, line: {self.line}, col: {self.col})"

class LexerException(Exception):
    def __init__(self, lexer: Lexer, message):
        super().__init__(f"{lexer.source_file}:{lexer.line}:{lexer.col}: {message}")

ESCAPE_CHARACTERS = {
    'n': '\n',
    't': '\t',
    'r': '\r',
    'a': '\a',
    'b': '\b',
    'f': '\f',
    'v': '\v',
    '\\': '\\',
    '\'': '\'',
    '\"': '\"',
    '0': '\0'
}

class LexerMode(Enum):
    RAW_C = auto()
    DEFAULT = auto

class Lexer:
    def __init__(self, source: str, source_file: str, source_directory: str):
        self.source = source
        self.source_file = source_file
        self.index = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []
        self.source_len = len(source)
        self.source_directory = source_directory
        self.mode: LexerMode = LexerMode.DEFAULT

    def advance(self):
        char = self.source[self.index]
        self.index += 1
        if (char == '\n'):
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return char
    
    def is_not_over(self) -> bool:
        return self.index < self.source_len

    def peek(self, offset: int = 0) -> str:
        index = self.index + offset
        return self.source[index] if index < self.source_len else ''
        
    def skip_empty(self):
        while self.is_not_over() and self.peek() in ' \t\r\n':
            self.advance()

    def skip_until_eol(self):
        while self.is_not_over() and self.peek() != '\n':
            self.advance()

    # /* are already consumed
    def skip_comment_block(self):
        while self.is_not_over():
            if self.peek() == '*' and self.peek(1) == '/':
                self.advance()
                self.advance()
                return
            self.advance()
        raise LexerException(self, "cannot find the end of \"/*\" comment")

    def get_next_token(self) -> Token:
        while self.is_not_over():
            if self.mode == LexerMode.DEFAULT: self.skip_empty()
            if not self.is_not_over():
                break

            current_char = self.peek()
            line = self.line
            col = self.col

            if current_char == "/" and self.peek(1) == "/":
                self.advance()
                self.advance()
                self.skip_until_eol()
                continue

            if current_char == "/" and self.peek(1) == "*":
                self.advance()
                self.advance()
                self.skip_comment_block()
                continue

            if self.mode == LexerMode.RAW_C:
                depth = 1
                code = []
                while self.is_not_over():
                    current_char = self.peek()
                    if current_char == "{":
                        depth += 1
                        code.append(self.advance())
                    elif (current_char == "}"):
                        depth -= 1
                        if depth == 0:
                            return Token(self, TokenType.C_BLOCK, ''.join(code), line, col)
                        code.append(self.advance())
                    else:
                        code.append(self.advance())
                continue

            if current_char == ';':
                token = Token(self, TokenType.SEMICOLON, ';', line, col)
                self.advance()
                return token

            if current_char == '{':
                token = Token(self, TokenType.LBRACE, '{', line, col)
                self.advance()
                return token

            if current_char == '}':
                token = Token(self, TokenType.RBRACE, '}', line, col)
                self.advance()
                return token

            if current_char.isalpha() or current_char == '_':
                start_position = self.index
                while self.is_not_over() and (self.peek().isalpha() or self.peek() == '_'):
                    self.advance()
                read_word = self.source[start_position:self.index]
                read_token_type = KEYWORDS.get(read_word, TokenType.IDENTIFIER)
                return Token(self, read_token_type, read_word, line, col)

            if current_char == '"':
                self.advance()
                start_position = self.index
                characters: list[str] = []
                while self.is_not_over():
                    read_char = self.advance()
                    if read_char == '\\' and self.is_not_over():
                        escape_char = self.advance()
                        if escape_char not in ESCAPE_CHARACTERS.keys():
                            raise LexerException(self, f"invalid escape character in string")
                        characters.append(ESCAPE_CHARACTERS[escape_char])
                    elif read_char == '"':
                        break
                    elif read_char == '\n':
                        raise LexerException(self, f"unterminated string")
                    else:
                        characters.append(read_char)
                read_string = ''.join(characters)
                return Token(self, TokenType.STRING, read_string, line, col)

            raise LexerException(self, f"unexpected character")

        return Token(self, TokenType.EOF, '', self.line, self.col)

class ParserException(Exception):
    def __init__(self, parser: Parser, message: str):
        super().__init__(f"{parser.source_file}:{parser.peek().line}:{parser.peek().col}: {message}")

class ComponentNode:
    def __init__(self, name: str, struct: Token):
        self.name = name
        self.struct = struct
        self.full_component_name = f"mici_component_{self.name}"
        self.header_file_name = f"{self.full_component_name}.h"
        self.header_guard = f"{self.full_component_name.upper()}_H_"
        self.type_name = f"{self.full_component_name}_t"

    def __repr__(self) -> str:
        return f"ComponentNode(name: {self.name}, struct: {self.struct})"


    def code_gen(self) -> str:

        header = '\n'.join([
            f"#ifndef {self.header_guard}",
            f"#define {self.header_guard}",
            "",
            "#include <mici.h>",
            "",
            f"// {self.struct.lexer.source_file}:{self.struct.line}:{self.struct.col}",
            f"typedef struct {self.type_name} {{{self.struct.value}}} {self.type_name};"
            "",
            "",
            f"#endif // #define {self.header_guard}"
        ])

        return {"header_file_name": self.header_file_name, "header": header}
    
class SystemNode:
    def __init__(self, name: str, source_file: str, source_directory: str, struct: Token, use_components: list[str], init: Token, destroy: Token, pre_update: Token, update: Token, post_update: Token, c_blocks: list[Token]):
        self.name = name
        self.struct = struct
        self.use_components = use_components
        self.init = init
        self.destroy = destroy
        self.pre_update = pre_update
        self.update = update
        self.post_update = post_update
        self.c_blocks = c_blocks
        self.source_file = source_file
        self.source_directory = source_directory

        self.full_system_name = f"mici_system_{self.name}"
        self.header_file_name = f"{self.full_system_name}.h"
        self.source_file_name = f"{self.full_system_name}.c"
        self.header_guard = f"{self.full_system_name.upper()}_H_"
        self.type_name = f"{self.full_system_name}_t"
        self.components = [self.parse_use_component(x) for x in self.use_components]

        self.initialize_function_name = f"mici_system_initialize_{self.name}"
        self.pre_update_function_name = f"mici_system_pre_update_{self.name}"
        self.update_function_name = f"mici_system_update_{self.name}"
        self.post_update_function_name = f"mici_system_post_update_{self.name}"
        self.destroy_function_name = f"mici_system_destroy_{self.name}"

    def __repr__(self) -> str:
        return f"SystemNode(name: {self.name}, struct: {self.struct}, components: {self.use_components})"

    # todo: refactor as the same function is being used quite a lot in other classes
    def parse_use_component(self, use: str) -> str:
        use_source_file = os.path.normpath(os.path.join(self.source_directory, use))
        use_source_directory = os.path.dirname(use_source_file)
        with open(use_source_file) as file:
            source = file.read()
        component = Parser(Lexer(source, use_source_file, use_source_directory), use_source_file).parse_component()
        
        include_path = os.path.join(os.path.dirname(use), component.header_file_name).replace('\\', '/')
        if not include_path.startswith('.'):
            include_path = f"./{include_path}"

        return {'use_directory': use_source_directory, 'include_path': include_path, 'component': component}

    def code_gen(self) -> str:
        
        update_parameters = ', '.join([f"{component['component'].type_name} *{component['component'].name}" for component in self.components])

        header = '\n'.join([
            f"#ifndef {self.header_guard}",
            f"#define {self.header_guard}",
            "",
            "#include <mici.h>",
            "",
            "\n".join([f"#include \"{x['include_path']}\"" for x in self.components]),
            "",
            f"typedef struct {self.type_name} {{{self.struct.value}}} {self.type_name};"
            "",
            f"void {self.initialize_function_name}({self.type_name} *self);",
            f"void {self.destroy_function_name}({self.type_name} *self);",
            f"void {self.pre_update_function_name}({self.type_name} *self);",
            f"void {self.update_function_name}({self.type_name} *self, {update_parameters});",
            f"void {self.post_update_function_name}({self.type_name} *self);",
            "",
            f"#endif // #define {self.header_guard}"
        ])

        source = '\n'.join([
            f"#include \"{self.header_file_name}\""
            "",
            "",
            "\n".join(map(lambda x: f"// {x.lexer.source_file}:{x.line}:{x.col}\n{x.value}", self.c_blocks)),
            "",
            f"// {self.init.lexer.source_file}:{self.init.line}:{self.init.col}",
            f"void {self.initialize_function_name}({self.type_name} *self) {{{self.init.value}}}",
            "",
            f"// {self.destroy.lexer.source_file}:{self.destroy.line}:{self.destroy.col}",
            f"void {self.destroy_function_name}({self.type_name} *self, {update_parameters}) {{{self.destroy.value}}}",
            "",
            f"// {self.pre_update.lexer.source_file}:{self.pre_update.line}:{self.pre_update.col}",
            f"void {self.pre_update_function_name}({self.type_name} *self) {{{self.pre_update.value}}}",
            "",
            f"// {self.update.lexer.source_file}:{self.update.line}:{self.update.col}",
            f"void {self.update_function_name}({self.type_name} *self) {{{self.update.value}}}",
            "",
            f"// {self.post_update.lexer.source_file}:{self.post_update.line}:{self.post_update.col}",
            f"void {self.post_update_function_name}({self.type_name} *self) {{{self.post_update.value}}}",
        ])

        return {"header_file_name": self.header_file_name, "header": header, "source_file_name": self.source_file_name, "source": source}

class ArchetypeNode:
    def __init__(self, name: str, source_file: str, source_directory: str, use_components: list[str]):
        self.name = name
        self.use_components = use_components
        self.source_file = source_file
        self.source_directory = source_directory

        self.full_name = f"mici_archetype_{self.name}"
        self.header_file_name = f"{self.full_name}.h"
        self.source_file_name = f"{self.full_name}.c"
        self.header_guard = f"{self.full_name.upper()}_H_"
        self.type_name = f"{self.full_name}_t"
        self.components = [self.parse_use_component(x) for x in self.use_components]

    # todo: refactor as the same function is being used quite a lot in other classes
    def parse_use_component(self, use: str) -> str:
        use_source_file = os.path.normpath(os.path.join(self.source_directory, use))
        use_source_directory = os.path.dirname(use_source_file)
        with open(use_source_file) as file:
            source = file.read()
        
        component = Parser(Lexer(source, use_source_file, use_source_directory), use_source_file).parse_component()
        
        include_path = os.path.join(os.path.dirname(use), component.header_file_name).replace('\\', '/')
        if not include_path.startswith('.'):
            include_path = f"./{include_path}"

        return {'use_directory': use_source_directory, 'include_path': include_path, 'component': component}

    def code_gen(self) -> dict:
        component_pointers = '\n'.join([f"\t{component['component'].type_name} *{component['component'].name};" for component in self.components])
        header = '\n'.join([
            f"#ifndef {self.header_guard}",
            f"#define {self.header_guard}",
            "",
            "#include <mici.h>\n",
            ""
            "\n".join([f"#include \"{x['include_path']}\"" for x in self.components]),
            "",
            f"typedef struct {self.type_name} {{\n{component_pointers}\n\tsize_t count; size_t capacity;\n}} {self.type_name};"
            "",
            "",
            f"#endif // #define {self.header_guard}"
        ])

        return {"header_file_name": self.header_file_name, "header": header}

    def __repr__(self) -> str:
        return f"ArchetypeNode(name: {self.name}, components: {self.use_components})"

class WorldNode:
    def __init__(self, name, source_file, source_directory, use_archetypes: list[str], use_systems: list[str], initialize_order: list[str], update_order: list[str], destroy_order: list[str]):
        self.name = name
        self.use_archetypes = use_archetypes
        self.use_systems = use_systems
        self.initialize_order = initialize_order
        self.update_order = update_order
        self.destroy_order = destroy_order
        self.source_file = source_file
        self.source_directory = source_directory

        if len(initialize_order) == 0: initialize_order = use_systems.copy()
        if len(update_order) == 0: update_order = use_systems.copy()
        if len(destroy_order) == 0: destroy_order = use_systems.copy()

        self.full_name = f"mici_world_{self.name}"
        self.header_file_name = f"{self.full_name}.h"
        self.source_file_name = f"{self.full_name}.c"
        self.header_guard = f"{self.full_name.upper()}_H_"
        self.type_name = f"{self.full_name}_t"
        self.archetypes = [self.parse_use_archetype(x) for x in self.use_archetypes]
        self.systems = [self.parse_use_system(x) for x in self.use_systems]

        self.initialize_function_name = f"mici_world_initialize_{self.name}"
        self.update_function_name = f"mici_world_update_{self.name}"
        self.destroy_function_name = f"mici_world_destroy_{self.name}"
        
    # todo: refactor as the same function is being used quite a lot in other classes
    def parse_use_archetype(self, use: str) -> str:
        use_source_file = os.path.normpath(os.path.join(self.source_directory, use))
        use_source_directory = os.path.dirname(use_source_file)
        with open(use_source_file) as file:
            source = file.read()

        archetype = Parser(Lexer(source, use_source_file, use_source_directory), use_source_file).parse_archetype()
        
        include_path = os.path.join(os.path.dirname(use), archetype.header_file_name).replace('\\', '/')
        if not include_path.startswith('.'):
            include_path = f"./{include_path}"

        return {'use_directory': use_source_directory, 'include_path': include_path, 'archetype': archetype}
    
    # todo: refactor as the same function is being used quite a lot in other classes
    def parse_use_system(self, use: str) -> str:
        use_source_file = os.path.normpath(os.path.join(self.source_directory, use))
        use_source_directory = os.path.dirname(use_source_file)
        with open(use_source_file) as file:
            source = file.read()
    
        system = Parser(Lexer(source, use_source_file, use_source_directory), use_source_file).parse_system()
        
        include_path = os.path.join(os.path.dirname(use), system.header_file_name).replace('\\', '/')
        if not include_path.startswith('.'):
            include_path = f"./{include_path}"

        return {'use_directory': use_source_directory, 'include_path': include_path, 'system': system}

    def __repr__(self) -> str:
        return f"WorldNode(name: {self.name}, archetypes: {self.use_archetypes}, systems: {self.use_systems}, initialize_order: {self.initialize_order}, update_order: {self.update_order}, destroy_order: {self.destroy_order})"

    def code_gen(self) -> dict:
        archetype_instances = '\n'.join([f"\t{x['archetype'].type_name} {x['archetype'].name};" for x in self.archetypes])
        system_instances = '\n'.join([f"\t{x['system'].type_name} {x['system'].name};" for x in self.systems])

        initialize_calls: dict = {system['system'].name: f"{system['system'].initialize_function_name}(self->{system['system'].name});" for system in self.systems}
        update_calls: dict = {}
        destroy_calls: dict = {system['system'].name: f"{system['system'].destroy_function_name}(self->{system['system'].name});" for system in self.systems}

        for system in self.systems:
            required_components = {x['component'].name for x in system['system'].components}
            eligible_archetypes = [x['archetype'] for x in self.archetypes if required_components.issubset({y['component'].name for y in x['archetype'].components})]

            for archetype in eligible_archetypes:
                component_for_update = ", ".join([f"self->{archetype.name}.{x['component'].name}[__mici_archetype_instance_index]" for x in system['system'].components])
                pre_update_call = f"{system['system'].pre_update_function_name}(self->{system['system'].name});"
                update_call = f"\t{system['system'].update_function_name}(self->{system['system'].name}, {component_for_update});"
                post_update_call = f"{system['system'].post_update_function_name}(self->{system['system'].name});"
                update_calls[system['system'].name] = (f"{pre_update_call}\n\tfor (size_t __mici_archetype_instance_index = 0; __mici_archetype_instance_index < self->{archetype.name}.count; ++__mici_archetype_instance_index) {{\n\t{update_call}\n\t}}\n\t{post_update_call}")

        header = '\n'.join([
            f"#ifndef {self.header_guard}",
            f"#define {self.header_guard}",
            "",
            "#include <mici.h>",
            "",
            "\n".join([f"#include \"{x['include_path']}\"" for x in self.archetypes]),
            "",
            "\n".join([f"#include \"{x['include_path']}\"" for x in self.systems]),
            "",
            f"typedef struct {self.type_name} {{\n{archetype_instances}\n{system_instances}\n}} {self.type_name};\n"
            "",
            f"void {self.initialize_function_name}({self.type_name} *self);",
            f"void {self.update_function_name}({self.type_name} *self);",
            f"void {self.destroy_function_name}({self.type_name} *self);",
            "",
            f"#endif // #define {self.header_guard}"
        ])

        source = '\n'.join([
            f"#include {self.header_file_name}",
            "",
            f"void {self.initialize_function_name}({self.type_name} *self) {{\n{'\n'.join([f"\t{initialize_calls[system]}" for system in self.initialize_order])}\n}}",
            f"void {self.update_function_name}({self.type_name} *self) {{\n{'\n\n'.join([f"\t{update_calls[system]}" for system in self.initialize_order])}\n}}",
            f"void {self.destroy_function_name}({self.type_name} *self) {{\n{'\n'.join([f"\t{destroy_calls[system]}" for system in self.initialize_order])}\n}}",
        ])

        return {"header_file_name": self.header_file_name, "header": header, "source_file_name": self.source_file_name, "source": source}
        

class Parser():
    def __init__(self, lexer: Lexer, source_file: str):
        self.lexer = lexer
        self.source_file = source_file
        self.buffer: list[Token] = []
        self.fill_buffer()

    def fill_buffer(self):
        if not self.buffer:
            self.buffer.append(self.lexer.get_next_token())

    def is_not_over(self) -> bool:
        return self.peek() and self.peek().type != TokenType.EOF

    def peek(self) -> Token:
        self.fill_buffer()
        return self.buffer[0]

    def advance(self) -> Token:
        return self.buffer.pop(0)

    def expect(self, *types: TokenType):
        token = self.peek()
        if token.type not in types:
            raise ParserException(self, f"expected {types}, but got {token.type}")
        return self.advance()
    
    def parse_component(self) -> ComponentNode:
        self.expect(TokenType.KW_COMPONENT)
        component_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LBRACE)
        self.lexer.mode = LexerMode.RAW_C
        component_struct = self.expect(TokenType.C_BLOCK)
        self.lexer.mode = LexerMode.DEFAULT
        self.expect(TokenType.RBRACE)
        self.expect(TokenType.SEMICOLON)

        while self.is_not_over():
            token = self.peek()
            raise ParserException(self, f"unexpected token {token.type.name} ({token.value})")

        self.expect(TokenType.EOF)
        return ComponentNode(component_name, component_struct)

    def parse_system(self) -> SystemNode:
        self.expect(TokenType.KW_SYSTEM)
        system_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LBRACE)
        self.lexer.mode = LexerMode.RAW_C
        system_struct = self.expect(TokenType.C_BLOCK)
        self.lexer.mode = LexerMode.DEFAULT
        self.expect(TokenType.RBRACE)
        self.expect(TokenType.SEMICOLON)

        system_use_components: list[str] = []
        system_init: Token = None
        system_destroy: Token = None
        system_pre_update: Token = None
        system_update: Token = None
        system_post_update: Token = None
        system_c_blocks: list[Token] = []

        while self.is_not_over():
            token = self.peek()

            if token.type == TokenType.KW_USE:
                self.advance()
                use_type = self.expect(TokenType.KW_SYSTEM, TokenType.KW_COMPONENT, TokenType.KW_ARCHETYPE, TokenType.KW_WORLD)
                if use_type.type != TokenType.KW_COMPONENT:
                    raise ParserException(self, "only components are allowed to be inside a system")
                system_use_components.append(self.expect(TokenType.STRING).value)
                self.expect(TokenType.SEMICOLON)
                continue

            if token.type == TokenType.KW_INITIALIZE:
                if system_init != None:
                    raise ParserException(self, "only one init allowed per system")
                self.advance()
                self.expect(TokenType.LBRACE)
                self.lexer.mode = LexerMode.RAW_C
                system_init = self.expect(TokenType.C_BLOCK)
                self.lexer.mode = LexerMode.DEFAULT
                self.expect(TokenType.RBRACE)
                continue

            if token.type == TokenType.KW_DESTROY:
                if system_destroy != None:
                    raise ParserException(self, "only one destroy allowed per system")
                self.advance()
                self.expect(TokenType.LBRACE)
                self.lexer.mode = LexerMode.RAW_C
                system_destroy = self.expect(TokenType.C_BLOCK)
                self.lexer.mode = LexerMode.DEFAULT
                self.expect(TokenType.RBRACE)
                continue
            
            if token.type == TokenType.KW_PRE_UPDATE:
                if system_pre_update != None:
                    raise ParserException(self, "only one pre_update allowed per system")
                self.advance()
                self.expect(TokenType.LBRACE)
                self.lexer.mode = LexerMode.RAW_C
                system_pre_update = self.expect(TokenType.C_BLOCK)
                self.lexer.mode = LexerMode.DEFAULT
                self.expect(TokenType.RBRACE)
                continue

            if token.type == TokenType.KW_UPDATE:
                if system_update != None:
                    raise ParserException(self, "only one update allowed per system")
                self.advance()
                self.expect(TokenType.LBRACE)
                self.lexer.mode = LexerMode.RAW_C
                system_update = self.expect(TokenType.C_BLOCK)
                self.lexer.mode = LexerMode.DEFAULT
                self.expect(TokenType.RBRACE)
                continue

            if token.type == TokenType.KW_POST_UPDATE:
                if system_post_update != None:
                    raise ParserException(self, "only one post_update allowed per system")
                self.advance()
                self.expect(TokenType.LBRACE)
                self.lexer.mode = LexerMode.RAW_C
                system_post_update = self.expect(TokenType.C_BLOCK)
                self.lexer.mode = LexerMode.DEFAULT
                self.expect(TokenType.RBRACE)
                continue

            if token.type == TokenType.LBRACE:
                self.advance()
                self.lexer.mode = LexerMode.RAW_C
                system_c_blocks.append(self.expect(TokenType.C_BLOCK))
                self.lexer.mode = LexerMode.DEFAULT
                self.expect(TokenType.RBRACE)
                continue

            raise ParserException(self, f"unexpected token {token.type.name} ({token.value})")

        self.expect(TokenType.EOF)
        return SystemNode(system_name, self.lexer.source_file, self.lexer.source_directory, system_struct, system_use_components, system_init, system_destroy, system_pre_update, system_update, system_post_update, system_c_blocks)
    
    def parse_archetype(self) -> ArchetypeNode:
        self.expect(TokenType.KW_ARCHETYPE)
        archetype_name = self.expect(TokenType.IDENTIFIER).value
        archetype_use_components: list[Token] = []
        self.expect(TokenType.SEMICOLON)
        while self.is_not_over():
            token = self.peek()

            if token.type == TokenType.KW_USE:
                self.advance()
                use_type = self.expect(TokenType.KW_SYSTEM, TokenType.KW_COMPONENT, TokenType.KW_ARCHETYPE, TokenType.KW_WORLD)
                if use_type.type != TokenType.KW_COMPONENT:
                    raise ParserException(self, "only components are allowed to be inside an archetype")
                archetype_use_components.append(self.expect(TokenType.STRING).value)
                self.expect(TokenType.SEMICOLON)
                continue

            raise ParserException(self, f"unexpected token {token.type.name} ({token.value})")
        return ArchetypeNode(archetype_name, self.lexer.source_file, self.lexer.source_directory, archetype_use_components)
    
    def parse_world(self) -> WorldNode:
        self.expect(TokenType.KW_WORLD)
        world_name = self.expect(TokenType.IDENTIFIER).value
        world_use_archetypes: list[str] = []
        world_use_systems: list[str] = []
        world_initialize_order: list[str] = []
        world_update_order: list[str] = []
        world_destroy_order: list[str] = []
        self.expect(TokenType.SEMICOLON)

        # todo: cache those. I keep re-parsing them
        parsed_use_systems = {}

        while self.is_not_over():
            token = self.peek()

            if token.type == TokenType.KW_USE:
                self.advance()
                use_type = self.expect(TokenType.KW_SYSTEM, TokenType.KW_COMPONENT, TokenType.KW_ARCHETYPE, TokenType.KW_WORLD)
                if use_type.type not in [TokenType.KW_SYSTEM, TokenType.KW_ARCHETYPE]:
                    raise ParserException(self, "only systems and archetypes are allowed to be inside a world")
                use_name = self.expect(TokenType.STRING).value
                if use_type.type == TokenType.KW_SYSTEM: 
                    world_use_systems.append(use_name)
                    use_source_file = os.path.join(self.lexer.source_directory, use_name)
                    use_source_directory = os.path.dirname(use_source_file)
                    with open(use_source_file) as file:
                        source = file.read()
                    system = Parser(Lexer(source, use_source_file, use_source_directory), use_source_file).parse_system()
                    parsed_use_systems[system.name] = system
                elif use_type.type == TokenType.KW_ARCHETYPE: world_use_archetypes.append(use_name)
                self.expect(TokenType.SEMICOLON)

                continue

            if token.type == TokenType.KW_INITIALIZE:
                if world_initialize_order:
                    raise ParserException(self, "initialize order is already set in this world")
                self.advance()
                self.expect(TokenType.LBRACE)
                self.lexer.mode = LexerMode.DEFAULT
                while self.is_not_over() and self.peek().type != TokenType.RBRACE:
                    system = self.expect(TokenType.IDENTIFIER).value
                    if system not in parsed_use_systems:
                        raise ParserException(self, f"undefined system `{system}` is present in the initialize block")
                    world_initialize_order.append(system)
                    self.expect(TokenType.SEMICOLON)
                self.expect(TokenType.RBRACE)
                if len(world_initialize_order) != len(parsed_use_systems):
                    raise ParserException(self, "not all systems are present in the initialize block")
                continue

            if token.type == TokenType.KW_UPDATE:
                if world_update_order:
                    raise ParserException(self, "update order is already set in this world")
                self.advance()
                self.expect(TokenType.LBRACE)
                self.lexer.mode = LexerMode.DEFAULT
                while self.is_not_over() and self.peek().type != TokenType.RBRACE:
                    system = self.expect(TokenType.IDENTIFIER).value
                    if system not in parsed_use_systems:
                        raise ParserException(self, f"undefined system `{system}` is present in the update block")
                    world_update_order.append(system)
                    self.expect(TokenType.SEMICOLON)
                self.expect(TokenType.RBRACE)
                if len(world_update_order) != len(parsed_use_systems):
                    raise ParserException(self, "not all systems are present in the update block")
                continue

            if token.type == TokenType.KW_DESTROY:
                if world_destroy_order:
                    raise ParserException(self, "destroy order is already set in this world")
                self.advance()
                self.expect(TokenType.LBRACE)
                self.lexer.mode = LexerMode.DEFAULT
                while self.is_not_over() and self.peek().type != TokenType.RBRACE:
                    system = self.expect(TokenType.IDENTIFIER).value
                    if system not in parsed_use_systems:
                        raise ParserException(self, f"undefined system `{system}` is present in the destroy block")
                    world_destroy_order.append(system)
                    self.expect(TokenType.SEMICOLON)
                self.expect(TokenType.RBRACE)
                if len(world_destroy_order) != len(parsed_use_systems):
                    raise ParserException(self, "not all systems are present in the destroy block")
                continue

            raise ParserException(self, f"unexpected token {token.type.name} ({token.value})")

        return WorldNode(world_name, self.lexer.source_file, self.lexer.source_directory, world_use_archetypes, world_use_systems, world_initialize_order, world_update_order, world_destroy_order)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("files", nargs="+")
    argument_parser.add_argument("--output-include", "-oi", type=str, required=True)
    argument_parser.add_argument("--output-source", "-os", type=str, required=True)
    argument_parser.add_argument("--input-base", "-ib", type=str, required=True)
    arguments = argument_parser.parse_args()

    base_path = os.path.abspath(arguments.input_base)
    output_include_path = os.path.abspath(arguments.output_include)
    output_source_path = os.path.abspath(arguments.output_source)

    for file_path in arguments.files:
        file_absolute_path = os.path.abspath(file_path)

        if not file_absolute_path.startswith(base_path + os.sep):
            raise ValueError(f"{file_absolute_path} is not inside base path {base_path}")
        
        file_base_path = os.path.dirname(os.path.relpath(file_absolute_path, base_path))

        file_directory = os.path.dirname(file_path)
        extension = os.path.splitext(file_path)[1]

        with open(file_path) as file:
            source = file.read()

        lexer = Lexer(source, file_path, file_directory)
        parser = Parser(lexer, file_path)

        result = {}

        if extension == ".mcc":
            node = parser.parse_component()
            result = node.code_gen()

        if extension == '.mcs':
            node = parser.parse_system()
            result = node.code_gen()

        if extension == '.mca':
            node = parser.parse_archetype()
            result = node.code_gen()

        if extension == '.mcw':
            node = parser.parse_world()
            result = node.code_gen()

        if "header_file_name" in result:
            header_file = os.path.join(output_include_path, file_base_path, result['header_file_name'])
            print(f"{file_absolute_path} generated: {header_file}")
            os.makedirs(os.path.dirname(header_file), exist_ok=True)
            with open(header_file, "w") as f:
                f.write(result['header'])

        if "source_file_name" in result:
            source_file = os.path.join(output_source_path, file_base_path, result['source_file_name'])
            print(f"{file_absolute_path} generated: {source_file}")
            os.makedirs(os.path.dirname(source_file), exist_ok=True)
            with open(source_file, "w") as f:
                f.write(result['source'])

        # return {"header_file_name": self.header_file_name, "header": header, "source_file_name": self.source_file_name, "source": source}
