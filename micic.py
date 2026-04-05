import os
import argparse
from enum import Enum, auto

class TokenType(Enum):
    IDENTIFIER = auto()
    SEMICOLON = auto()
    KW_COMPONENT = auto()
    KW_SYSTEM = auto()
    KW_USE = auto()
    KW_INIT = auto()
    KW_DESTROY = auto()
    KW_UPDATE = auto()
    C_BLOCK = auto()
    EOF = auto()
    STRING = auto()

KEYWORDS = {
    'component': TokenType.KW_COMPONENT,
    'system': TokenType.KW_SYSTEM,
    'use': TokenType.KW_USE,
    'initialize': TokenType.KW_INIT,
    'destroy': TokenType.KW_DESTROY,
    'update': TokenType.KW_UPDATE
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

class Lexer:
    def __init__(self, source: str, source_file: str):
        self.source = source
        self.source_file = source_file
        self.index = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []
        self.source_len = len(source)

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

    def tokenize(self) -> list[Token]:
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

            # C block
            if current_char == "{":
                depth = 1
                code = []
                self.advance()
                while self.is_not_over():
                    current_char = self.peek()
                    if current_char == "{":
                        depth += 1
                        code.append(self.advance())
                    elif (current_char == "}"):
                        depth -= 1
                        if depth == 0:
                            self.advance() # consume remaining }
                            self.tokens.append(Token(self, TokenType.C_BLOCK, ''.join(code), line, col))
                            break
                        code.append(self.advance())
                    else:
                        code.append(self.advance())
                continue

            if current_char == ';':
                self.tokens.append(Token(self, TokenType.SEMICOLON, ';', line, col))
                self.advance()
                continue

            if current_char.isalpha() or current_char == '_':
                start_position = self.index
                while self.is_not_over() and (self.peek().isalpha() or self.peek() == '_'):
                    self.advance()
                read_word = self.source[start_position:self.index]
                read_token_type = KEYWORDS.get(read_word, TokenType.IDENTIFIER)
                self.tokens.append(Token(self, read_token_type, read_word, line, col))
                continue

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
                self.tokens.append(Token(self, TokenType.STRING, read_string, line, col))
                print(read_string)
                continue

            raise LexerException(self, f"unexpected character")

        self.tokens.append(Token(self, TokenType.EOF, '', line, col))
        return self.tokens

class ParserException(Exception):
    def __init__(self, parser: Parser, message: str):
        super().__init__(f"{parser.source_file}:{parser.peek().line}:{parser.peek().col}: {message}")

class ComponentNode:
    def __init__(self, name: str, struct: Token):
        self.name = name
        self.struct = struct
        self.full_component_name = f"mici_component_{self.name}"
        self.header_file_name = f"{self.full_component_name}.h"

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
    def __init__(self, name: str, struct: Token, uses: list[str], init: Token, destroy: Token, update: Token, c_blocks: list[Token]):
        self.name = name
        self.struct = struct
        self.uses = uses
        self.init = init
        self.destroy = destroy
        self.update = update
        self.c_blocks = c_blocks
        self.full_system_name = f"mici_system_{self.name}"
        self.header_file_name = f"{self.full_system_name}.h"
        self.source_file_name = f"{self.full_system_name}.c"

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
            "\n".join(map(lambda use: f"#include \"{self.use_to_include(use)}\"", self.uses)),
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

class Parser():
    def __init__(self, tokens: list[Token], source_file: str):
        self.tokens = tokens
        self.tokens_len = len(tokens)
        self.source_file = source_file
        self.index = 0

    def is_not_over(self) -> bool:
        return self.tokens[self.index].type != TokenType.EOF

    def peek(self, offset: int = 0) -> Token:
        index = self.index + offset
        return self.tokens[index] if index < self.tokens_len else None

    def advance(self) -> Token:
        token = self.peek()
        if token.type != TokenType.EOF: self.index += 1
        return token

    def expect(self, type: TokenType):
        token = self.peek()
        if token.type != type:
            raise ParserException(self, f"expected {type.name}, but got {token.type}")
        return self.advance()
    
    def parse_component(self) -> ComponentNode:
        self.expect(TokenType.KW_COMPONENT)
        component_name = self.expect(TokenType.IDENTIFIER).value
        component_struct = self.expect(TokenType.C_BLOCK)
        self.expect(TokenType.SEMICOLON)

        while self.is_not_over():
            token = self.peek()
            raise ParserException(self, f"unexpected token {token.type.name} ({token.value})")

        self.expect(TokenType.EOF)
        return ComponentNode(component_name, component_struct)

    def parse_system(self) -> SystemNode:
        self.expect(TokenType.KW_SYSTEM)
        system_name = self.expect(TokenType.IDENTIFIER).value
        system_struct = self.expect(TokenType.C_BLOCK)
        self.expect(TokenType.SEMICOLON)

        system_uses: list[str] = []
        system_init: Token = None
        system_destroy: Token = None
        system_update: Token = None
        system_c_blocks: list[Token] = []

        while self.is_not_over():
            token = self.peek()

            if token.type == TokenType.KW_USE:
                self.advance()
                system_uses.append(self.expect(TokenType.STRING).value)
                self.expect(TokenType.SEMICOLON)
                continue

            if token.type == TokenType.KW_INIT:
                if system_init != None:
                    raise ParserException(self, "only one init allowed per system")
                self.advance()
                system_init = self.expect(TokenType.C_BLOCK)
                continue

            if token.type == TokenType.KW_DESTROY:
                if system_destroy != None:
                    raise ParserException(self, "only one destroy allowed per system")
                self.advance()
                system_destroy = self.expect(TokenType.C_BLOCK)
                continue
            
            if token.type == TokenType.KW_UPDATE:
                if system_update != None:
                    raise ParserException(self, "only one update allowed per system")
                self.advance()
                system_update = self.expect(TokenType.C_BLOCK)
                continue

            if token.type == TokenType.C_BLOCK:
                self.advance()
                system_c_blocks.append(token)
                continue

            raise ParserException(self, f"unexpected token {token.type.name} ({token.value})")

        self.expect(TokenType.EOF)
        return SystemNode(system_name, system_struct, system_uses, system_init, system_destroy, system_update, system_c_blocks)
    

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("files", nargs="+")
    argumets = argument_parser.parse_args()

    for file_path in argumets.files:
        base_name = os.path.basename(file_path)
        extension = os.path.splitext(file_path)[1]

        print(base_name, extension)

        with open(file_path) as file:
            source = file.read()

        tokens = Lexer(source, file_path).tokenize()
        parser = Parser(tokens, file_path)

        if extension == ".mcc":
            node = parser.parse_component()
            print(node.code_gen())

        if extension == '.mcs':
            node = parser.parse_system()
            print(node.code_gen()['mici_system_render.c'])
