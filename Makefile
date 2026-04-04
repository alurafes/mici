CC = gcc
FLAGS = -Wall -Werror
LINKER = 

micis: build build/main.o
	$(CC) -o build/micis $(FLAGS) build/main.o $(LINKER)

build:
	mkdir build

build/main.o: build main.c
	$(CC) -o build/main.o -c main.c $(FLAGS)