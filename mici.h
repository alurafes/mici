#ifndef MICI_H_
#define MICI_H_

#include <stdlib.h>
#include <string.h>
#include <assert.h>

void mici_array_ensure_capacity(void **data, size_t *capacity, size_t elem_size, size_t needed);
void mici_array_swap_remove(void *data, size_t elem_size, size_t index, size_t last);
size_t mici_array_push_unintialized(void **data, size_t *capacity, size_t *count, size_t item_size);

#endif // #define MICI_H_