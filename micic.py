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
    C_BLOCK = auto()
    EOF = auto()

KEYWORDS = {
    'component': TokenType.KW_COMPONENT,
    'system': TokenType.KW_SYSTEM,
    'use': TokenType.KW_SYSTEM,
    'init': TokenType.KW_INIT,
    'destroy': TokenType.KW_DESTROY,
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
        for token in tokens: print(token)
