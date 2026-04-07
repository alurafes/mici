#ifndef MICI_ARCHETYPE_PLAYER_H_
#define MICI_ARCHETYPE_PLAYER_H_

#include <mici.h>

#include "../components/mici_component_position.h"
#include "../components/mici_component_rotation.h"

typedef struct mici_archetype_player_t {
	mici_component_position_t *position;
	mici_component_rotation_t *rotation;
	size_t count; size_t capacity;
} mici_archetype_player_t;

#endif // #define MICI_ARCHETYPE_PLAYER_H_