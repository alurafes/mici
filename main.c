#include <stdio.h>

#include <stdint.h>
#include <stdlib.h>

#define MICI_MAX_ENTITIES 1000

typedef enum {
    MICI_RESULT_OK,
    MICI_RESULT_INVALID_PARAMETER,
    MICI_RESULT_ALLOCATION_ERROR,
} mici_result_t;

typedef struct {
    uint32_t id;
} mici_entity_t;

typedef struct {
    mici_entity_t entities[MICI_MAX_ENTITIES];
} mici_world_t;

mici_result_t mici_world_create(mici_world_t **world)
{
    if (world == NULL) return MICI_RESULT_INVALID_PARAMETER;
    *world = calloc(1, sizeof(mici_world_t));
    if (*world == NULL) return MICI_RESULT_ALLOCATION_ERROR;
    
    return MICI_RESULT_OK;
}

void mici_world_free(mici_world_t **world)
{
    free(*world);
    *world = NULL;
}

int main()
{
    mici_world_t* world;
    mici_result_t result = mici_world_create(&world);
    if (result != MICI_RESULT_OK) return 1;

    

    mici_world_free(&world);
    return 0;
}