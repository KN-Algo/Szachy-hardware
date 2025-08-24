#ifndef COREXY_H
#define COREXY_H

#include <stdint.h>
#include <stdbool.h>
#include "Piny.h"

// --- Parametry ruchu ---
extern const uint32_t ACCEL_STEPS;
extern const uint32_t DECEL_STEPS;
extern const uint32_t MAX_SPEED_US;
extern const uint32_t MIN_SPEED_US;

#define STEPS_PER_REV   200
#define MICROSTEPS      16
#define PULLEY_TEETH    20
#define PITCH           2.0f

extern const float steps_per_mm;

// --- Globalna pozycja aktualna ---
extern float current_x;
extern float current_y;

// --- Prototypy funkcji CoreXY ---
void corexy_init_gpio(void);
void corexy_step(bool dir_a, bool dir_b, uint32_t step_delay_us);
void corexy_move_ramp(int x_steps, int y_steps);
void corexy_home(void);
void corexy_move_to(float start_x, float start_y, float end_x, float end_y, bool enable_electromagnet);

// --- Prototypy funkcji elektromagnesu ---
void elektromagnes_init(void);
void elektromagnes_set_power(uint8_t percent);
void elektromagnes_off(void);

#endif // COREXY_H
