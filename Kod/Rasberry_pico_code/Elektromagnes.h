#pragma once
#include "pico/stdlib.h"

void elektromagnes_init(void);
void elektromagnes_set_power(uint8_t percent);
void elektromagnes_off(void);