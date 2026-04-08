#ifndef MICI_SYSTEM_TEST_H_
#define MICI_SYSTEM_TEST_H_

#include <mici.h>



typedef struct mici_system_test_t {

} mici_system_test_t;
void mici_system_initialize_test(mici_system_test_t *self);
void mici_system_destroy_test(mici_system_test_t *self);
void mici_system_pre_update_test(mici_system_test_t *self);
void mici_system_update_test(mici_system_test_t *self);
void mici_system_post_update_test(mici_system_test_t *self);

#endif // #define MICI_SYSTEM_TEST_H_