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
    KW_INIT = auto()
    KW_DESTROY = auto()
    KW_PRE_UPDATE = auto()
    KW_UPDATE = auto()
    KW_POST_UPDATE = auto()
    KW_BEHAVIOUR = auto()
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
    'initialize': TokenType.KW_INIT,
    'destroy': TokenType.KW_DESTROY,
    'pre_update': TokenType.KW_PRE_UPDATE,
    'update': TokenType.KW_UPDATE,
    'post_update': TokenType.KW_POST_UPDATE,
    'behaviour': TokenType.KW_BEHAVIOUR,
    'behavior': TokenType.KW_BEHAVIOUR,
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
    def __init__(self, source: str, source_file: str):
        self.source = source
        self.source_file = source_file
        self.index = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []
        self.source_len = len(source)
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
            self.skip_empty()
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

    def __repr__(self) -> str:
        return f"ComponentNode(name: {self.name}, struct: {self.struct})"


    def code_gen(self) -> str:
        header_guard = f"{self.full_component_name.upper()}_H_"

        header = '\n'.join([
            f"#ifndef {header_guard}",
            f"#define {header_guard}",
            "",
            f"// {self.struct.lexer.source_file}:{self.struct.line}:{self.struct.col}",
            f"typedef struct {self.full_component_name}_t {{{self.struct.value}}} {self.full_component_name}_t;"
            "",
            "",
            f"#endif // #define {header_guard}"
        ])

        return {self.header_file_name: header}
    
class SystemNode:
    def __init__(self, name: str, struct: Token, use_components: list[str], init: Token, destroy: Token, pre_update: Token, update: Token, post_update: Token, c_blocks: list[Token]):
        self.name = name
        self.struct = struct
        self.use_components = use_components
        self.init = init
        self.destroy = destroy
        self.pre_update = pre_update
        self.update = update
        self.post_update = post_update
        self.c_blocks = c_blocks
        self.full_system_name = f"mici_system_{self.name}"
        self.header_file_name = f"{self.full_system_name}.h"
        self.source_file_name = f"{self.full_system_name}.c"

    def __repr__(self) -> str:
        return f"SystemNode(name: {self.name}, struct: {self.struct}, components: {self.use_components})"

    def use_to_include(self, use: str) -> str:
        with open(use) as file:
            source = file.read()
        
        use_directory = os.path.dirname(use)
        component = Parser(Lexer(source, use).tokenize(), use).parse_component()
        
        include_path = os.path.join(use_directory, component.header_file_name).replace('\\', '/')
        if not include_path.startswith('.'):
            include_path = f"./{include_path}"

        return include_path

    def code_gen(self) -> str:
        header_guard = f"{self.full_system_name.upper()}_H_"
        typename = f"{self.full_system_name}_t"

        header = '\n'.join([
            f"#ifndef {header_guard}",
            f"#define {header_guard}",
            "",
            "\n".join(map(lambda use: f"#include \"{self.use_to_include(use)}\"", self.use_components)),
            "",
            f"typedef struct {typename} {{{self.struct.value}}} {typename};"
            "",
            f"void mici_system_initialize_{self.name}({typename} *self);",
            f"void mici_system_destroy_{self.name}({typename} *self);",
            f"void mici_system_update_{self.name}({typename} *self);",
            "",
            f"#endif // #define {header_guard}"
        ])

        source = '\n'.join([
            f"#include \"{self.header_file_name}\""
            "",
            "",
            "\n".join(map(lambda x: f"// {x.lexer.source_file}:{x.line}:{x.col}\n{x.value}", self.c_blocks)),
            "",
            f"// {self.init.lexer.source_file}:{self.init.line}:{self.init.col}",
            f"void mici_system_initialize_{self.name}({typename} *self) {{{self.init.value}}}",
            "",
            f"// {self.destroy.lexer.source_file}:{self.destroy.line}:{self.destroy.col}",
            f"void mici_system_destroy_{self.name}({typename} *self) {{{self.destroy.value}}}",
            "",
            f"// {self.update.lexer.source_file}:{self.update.line}:{self.update.col}",
            f"void mici_system_update_{self.name}({typename} *self) {{{self.update.value}}}",
        ])

        return {self.header_file_name: header, self.source_file_name: source}

class ArchetypeNode:
    def __init__(self, name: str, use_components: list[str]):
        self.name = name
        self.use_components = use_components

    def __repr__(self) -> str:
        return f"ArchetypeNode(name: {self.name}, components: {self.use_components})"

class WorldNode:
    def __init__(self, name, use_archetypes, use_systems, behaviour):
        self.name = name
        self.use_archetypes = use_archetypes
        self.use_systems = use_systems
        self.behaviour = behaviour
        pass

    def __repr__(self) -> str:
        return f"WorldNode(name: {self.name}, archetypes: {self.use_archetypes}, systems: {self.use_systems}, behaviour: {self.behaviour})"

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

            if token.type == TokenType.KW_INIT:
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
        return SystemNode(system_name, system_struct, system_use_components, system_init, system_destroy, system_pre_update, system_update, system_post_update, system_c_blocks)
    
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
        return ArchetypeNode(archetype_name, archetype_use_components)
    
    def parse_world(self) -> WorldNode:
        self.expect(TokenType.KW_WORLD)
        world_name = self.expect(TokenType.IDENTIFIER).value
        world_use_archetypes: list[str] = []
        world_use_systems: list[str] = []
        world_behaviour: list[str] = []
        self.expect(TokenType.SEMICOLON)

        while self.is_not_over():
            token = self.peek()

            if token.type == TokenType.KW_USE:
                self.advance()
                use_type = self.expect(TokenType.KW_SYSTEM, TokenType.KW_COMPONENT, TokenType.KW_ARCHETYPE, TokenType.KW_WORLD)
                if use_type.type not in [TokenType.KW_SYSTEM, TokenType.KW_ARCHETYPE]:
                    raise ParserException(self, "only systems and archetypes are allowed to be inside a world")
                use_name = self.expect(TokenType.STRING).value
                if use_type.type == TokenType.KW_SYSTEM: world_use_systems.append(use_name)
                elif use_type.type == TokenType.KW_ARCHETYPE: world_use_archetypes.append(use_name)
                self.expect(TokenType.SEMICOLON)
                continue

            if token.type == TokenType.KW_BEHAVIOUR:
                if world_behaviour:
                    raise ParserException(self, "behaviour is already set in this world")
                self.advance()
                self.expect(TokenType.LBRACE)
                self.lexer.mode = LexerMode.DEFAULT
                while self.is_not_over() and self.peek().type != TokenType.RBRACE:
                    world_behaviour.append(self.expect(TokenType.IDENTIFIER).value)
                    self.expect(TokenType.SEMICOLON)
                self.expect(TokenType.RBRACE)
                continue

            raise ParserException(self, f"unexpected token {token.type.name} ({token.value})")

        return WorldNode(world_name, world_use_archetypes, world_use_systems, world_behaviour)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("files", nargs="+")
    argumets = argument_parser.parse_args()

    for file_path in argumets.files:
        base_name = os.path.basename(file_path)
        extension = os.path.splitext(file_path)[1]

        with open(file_path) as file:
            source = file.read()

        lexer = Lexer(source, file_path)
        parser = Parser(lexer, file_path)

        if extension == ".mcc":
            node = parser.parse_component()
            print(node)

        if extension == '.mcs':
            node = parser.parse_system()
            print(node)

        if extension == '.mca':
            node = parser.parse_archetype()
            print(node)

        if extension == '.mcw':
            node = parser.parse_world()
            print(node)
