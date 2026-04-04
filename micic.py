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

KEYWORDS = {
    'component': TokenType.KW_COMPONENT,
    'system': TokenType.KW_SYSTEM,
    'use': TokenType.KW_USE,
    'initialize': TokenType.KW_INIT,
    'destroy': TokenType.KW_DESTROY,
    'update': TokenType.KW_UPDATE
}

class Token:
    def __init__(self, type: TokenType, value: str, line: int, col: int):
        self.type = type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token(type: {self.type.name}, value: {self.value}, line: {self.line}, col: {self.col})"

class LexerException(Exception):
    pass

class Lexer:
    def __init__(self, source: str):
        self.source = source
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
        raise LexerException("cannot find the end of \"/*\" comment")

    def tokenize(self) -> list[Token]:
        while self.is_not_over():
            self.skip_empty()
            if not self.is_not_over():
                break

            current_char = self.peek()

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
                            self.tokens.append(Token(TokenType.C_BLOCK, ''.join(code), self.line, self.col))
                            break
                        code.append(self.advance())
                    else:
                        code.append(self.advance())
                continue

            if current_char == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, ';', self.line, self.col))
                self.advance()
                continue

            if current_char.isalpha() or current_char == '_':
                start_position = self.index
                while self.is_not_over() and (self.peek().isalpha() or self.peek() == '_'):
                    self.advance()
                read_word = self.source[start_position:self.index]
                read_token_type = KEYWORDS.get(read_word, TokenType.IDENTIFIER)
                self.tokens.append(Token(read_token_type, read_word, self.line, self.col))
                continue

            raise LexerException(f"unexpected character at {self.line}:{self.col}")

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens

class ParserException(Exception):
    def __init__(self, parser: Parser, message: str):
        super().__init__(f"{parser.peek().line}:{parser.peek().col}: {message}")

class ComponentNode:
    def __init__(self, name: str, struct: str):
        self.name = name
        self.struct = struct

    def code_gen(self) -> str:
        return f"""
            typedef struct mici_component_{self.name}_t {{{self.struct}}} mici_component_{self.name}_t;
        """.strip()
    
class SystemNode:
    def __init__(self, name: str, struct: str, uses: list[str], init: str, destroy: str, update: str, c_blocks: list[str]):
        self.name = name
        self.struct = struct
        self.uses = uses
        self.init = init
        self.destroy = destroy
        self.update = update
        self.c_blocks = c_blocks

    def code_gen(self) -> str:
        return f"""
            typedef struct mici_system_{self.name}_t {{{self.struct}}} mici_system_{self.name}_t;
        """.strip()

class Parser():
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.tokens_len = len(tokens)
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
        component_struct = self.expect(TokenType.C_BLOCK).value
        self.expect(TokenType.SEMICOLON)

        while self.is_not_over():
            token = self.peek()
            raise ParserException(self, f"unexpected token {token.type.name} ({token.value})")

        self.expect(TokenType.EOF)
        return ComponentNode(component_name, component_struct)

    def parse_system(self) -> SystemNode:
        self.expect(TokenType.KW_SYSTEM)
        system_name = self.expect(TokenType.IDENTIFIER).value
        system_struct = self.expect(TokenType.C_BLOCK).value
        self.expect(TokenType.SEMICOLON)

        system_uses: list[str] = []
        system_init: str = None
        system_destroy: str = None
        system_update: str = None
        system_c_blocks: list[str] = []

        while self.is_not_over():
            token = self.peek()

            if token.type == TokenType.KW_USE:
                self.advance()
                system_uses.append(self.expect(TokenType.IDENTIFIER).value)
                self.expect(TokenType.SEMICOLON)
                continue

            if token.type == TokenType.KW_INIT:
                if system_init != None:
                    raise ParserException(self, "only one init allowed per system")
                self.advance()
                system_init = self.expect(TokenType.C_BLOCK).value
                continue

            if token.type == TokenType.KW_DESTROY:
                if system_destroy != None:
                    raise ParserException(self, "only one destroy allowed per system")
                self.advance()
                system_destroy = self.expect(TokenType.C_BLOCK).value
                continue
            
            if token.type == TokenType.KW_UPDATE:
                if system_update != None:
                    raise ParserException(self, "only one update allowed per system")
                self.advance()
                system_update = self.expect(TokenType.C_BLOCK).value
                continue

            if token.type == TokenType.C_BLOCK:
                self.advance()
                system_c_blocks.append(token.value)
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

        tokens = Lexer(source).tokenize()
        parser = Parser(tokens)

        if extension == ".mcc":
            node = parser.parse_component()
            print(node.code_gen())

        if extension == '.mcs':
            node = parser.parse_system()
            print(node.code_gen())
