CC = gcc
FLAGS = -Wall -Werror
LINKER = 

micis:
	python micic.py -oi=./example/include/ -os=./example/src/ -ib ./example/mici/ example/mici/worlds/game.mcw example/mici/components/position.mcc example/mici/components/rotation.mcc example/mici/archetypes/player.mca example/mici/systems/render.mcs