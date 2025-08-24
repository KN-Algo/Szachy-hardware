#include "Elektromagnes.h"
#include "Piny.h"
// Zmienna wewnętrzna do zapamiętania slice/channel
static uint pwm_slice;
static uint pwm_channel;

void elektromagnes_init(void) {
    gpio_set_function(ELEKTROMAGNES_PIN, GPIO_FUNC_PWM);
    pwm_slice   = pwm_gpio_to_slice_num(ELEKTROMAGNES_PIN);
    pwm_channel = pwm_gpio_to_channel(ELEKTROMAGNES_PIN);

    pwm_set_wrap(pwm_slice, 255); // 8-bit PWM
    pwm_set_chan_level(pwm_slice, pwm_channel, 0);
    pwm_set_enabled(pwm_slice, true);
}

void elektromagnes_set_power(uint8_t percent) {
    if (percent > 100) percent = 100;
    uint level = (percent * 255) / 100;
    pwm_set_chan_level(pwm_slice, pwm_channel, level);
}

void elektromagnes_off(void) {
    pwm_set_chan_level(pwm_slice, pwm_channel, 0);
}
