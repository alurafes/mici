#include "mici.h"

void mici_array_ensure_capacity(void **data, size_t *capacity, size_t item_size, size_t needed)
{
    if (*capacity >= needed) return;

    size_t new_capacity = (*capacity == 0) ? 32 : *capacity;
    while (new_capacity < needed) {
        new_capacity *= 2;
    }

    void* new_data = realloc(*data, new_capacity * item_size);
    assert(new_data && "Out of memory");

    *data = new_data;
    *capacity = new_capacity;
}

size_t mici_array_push_unintialized(void **data, size_t *capacity, size_t *count, size_t item_size)
{
    mici_array_ensure_capacity(data, capacity, item_size, *count + 1);
    return (*count)++;
}

void mici_array_swap_remove(void *data, size_t item_size, size_t index, size_t* count)
{
    size_t last = *count - 1;

    if (index != last) {
        char* base = (char*)data;
        memcpy(base + index * item_size, base + last * item_size, item_size);
    }

    (*count)--;
}