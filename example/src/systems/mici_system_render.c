#include "systems/mici_system_render.h"

// example/mici/systems/render.mcs:8:2

    void test()
    {
        printf("test\n");
    }


// example/mici/systems/render.mcs:16:2
void mici_system_initialize_render(mici_system_render_t *self) {

}

// example/mici/systems/render.mcs:21:2
void mici_system_destroy_render(mici_system_render_t *self) {

}

// example/mici/systems/render.mcs:26:2
void mici_system_pre_update_render(mici_system_render_t *self) {
    self->count = 0;
}

// example/mici/systems/render.mcs:31:2
void mici_system_update_render(mici_system_render_t *self, mici_component_position_t *position, mici_component_rotation_t *rotation) {
    self->count += 1;
}

// example/mici/systems/render.mcs:36:2
void mici_system_post_update_render(mici_system_render_t *self) {
    printf("%zu\n", self->count);
}