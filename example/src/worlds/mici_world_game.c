#include mici_world_game.h

void mici_world_initialize_game(mici_world_game_t *self) {
	mici_system_initialize_render(self->render);
}
void mici_world_update_game(mici_world_game_t *self) {
	mici_system_pre_update_render(self->render);
	for (size_t __mici_archetype_instance_index = 0; __mici_archetype_instance_index < self->player.count; ++__mici_archetype_instance_index) {
		mici_system_update_render(self->render, self->player.position[__mici_archetype_instance_index], self->player.rotation[__mici_archetype_instance_index]);
	}
	mici_system_post_update_render(self->render);
}
void mici_world_destroy_game(mici_world_game_t *self) {
	mici_system_destroy_render(self->render);
}