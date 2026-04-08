#ifndef MICI_WORLD_GAME_H_
#define MICI_WORLD_GAME_H_

#include <mici.h>

#include "../archetypes/mici_archetype_player.h"

#include "../systems/mici_system_render.h"
#include "../systems/mici_system_test.h"

typedef struct mici_world_game_t {
	mici_archetype_player_t player;
	mici_system_render_t render;
	mici_system_test_t test;
} mici_world_game_t;

void mici_world_initialize_game(mici_world_game_t *self);
void mici_world_update_game(mici_world_game_t *self);
void mici_world_destroy_game(mici_world_game_t *self);

#endif // #define MICI_WORLD_GAME_H_