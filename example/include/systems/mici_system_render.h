#ifndef MICI_SYSTEM_RENDER_H_
#define MICI_SYSTEM_RENDER_H_

#include <mici.h>

#include "../components/mici_component_position.h"
#include "../components/mici_component_rotation.h"

typedef struct mici_system_render_t {
    size_t count;
} mici_system_render_t;
void mici_system_initialize_render(mici_system_render_t *self);
void mici_system_destroy_render(mici_system_render_t *self);
void mici_system_pre_update_render(mici_system_render_t *self);
void mici_system_update_render(mici_system_render_t *self, mici_component_position_t *position, mici_component_rotation_t *rotation);
void mici_system_post_update_render(mici_system_render_t *self);

#endif // #define MICI_SYSTEM_RENDER_H_