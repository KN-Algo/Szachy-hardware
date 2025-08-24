#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "Corexy.h"
#include "Multiplexery.h"

// ============================ KONFIGURACJA ============================
#define I2C_SLAVE i2c0
#define I2C_SLAVE_ADDR 0x42

struct Command {
    char type_of_command;
    float X_start;
    float Y_start;
    float X_end;
    float Y_end;
};

struct Command received_cmd;
uint8_t buffer[18];

// Globalna plansza 8x8
uint8_t board[8][8];

// ============================ I2C INIT ============================

void i2c_slave_init() {
    i2c_init(I2C_SLAVE, 100 * 1000); // 100kHz
    gpio_set_function(0, GPIO_FUNC_I2C); // SDA
    gpio_set_function(1, GPIO_FUNC_I2C); // SCL
    gpio_pull_up(0);
    gpio_pull_up(1);
    i2c_set_slave_mode(I2C_SLAVE, true, I2C_SLAVE_ADDR);
}

// Kopiowanie bajtów (little endian)
void memcpy_reverse(void *dest, uint8_t *src, int len) {
    for (int i = 0; i < len; i++) {
        ((uint8_t*)dest)[i] = src[i];
    }
}

// ============================ GŁÓWNY LOOP ============================

int main() {
    stdio_init_all();
    i2c_slave_init();
    printf("I2C Slave ready\n");

    while (1) {
        int n = i2c_get_read_available(I2C_SLAVE);

        if (n > 0) {
            received_cmd.type_of_command = i2c_read_byte_raw(I2C_SLAVE);

           switch (received_cmd.type_of_command) {
                case 'H': {
                    // Homing
                    corexy_home();
                    // Odpowiedź: "H"
                    uint8_t resp[1] = { 'H' }; // bez adresu
                    i2c_write_blocking(I2C_SLAVE, 0, resp, 1, false); 
                    printf("Odesłano potwierdzenie H\n");
                } break;

                case 'M': {
                    // Odbiór danych: 4B X_start, 4B Y_start, 4B X_end, 4B Y_end
                    while (i2c_get_read_available(I2C_SLAVE) < 16) {
                        tight_loop_contents();
                    }
                    for (int i = 0; i < 16; i++) {
                        buffer[i] = i2c_read_byte_raw(I2C_SLAVE);
                    }

                    memcpy_reverse(&received_cmd.X_start, &buffer[0], 4);
                    memcpy_reverse(&received_cmd.Y_start, &buffer[4], 4);
                    memcpy_reverse(&received_cmd.X_end,   &buffer[8], 4);
                    memcpy_reverse(&received_cmd.Y_end,   &buffer[12],4);

                    // Wywołaj funkcję ruchu
                    corexy_move_to(current_x, current_y, received_cmd.X_start, received_cmd.Y_start, false);
                    corexy_move_to(received_cmd.X_start, received_cmd.Y_start, received_cmd.X_end, received_cmd.Y_end, true);

                    // Aktualizacja pozycji globalnej
                    current_x = received_cmd.X_end;
                    current_y = received_cmd.Y_end;

                    uint8_t resp = 'M'; 
                    i2c_write_blocking(I2C_SLAVE, 0, &resp, 1, false); 
                    printf("Odesłano potwierdzenie M\n");
                } break;

                case 'B': {
                    // Skanowanie planszy
                    mux_read_8x8(board);
                    // Odpowiedź: 64 bajty (tablica 8x8)
                    i2c_write_blocking(I2C_SLAVE, 0, (uint8_t*)board, 64, false);
                    printf("Odesłano tablicę planszy\n");
                } break;

                default:
                    printf("❌ Nieznana komenda: %c\n", received_cmd.type_of_command);
                    break;
            }

            // Czyszczenie bufora wejściowego
            while (i2c_get_read_available(I2C_SLAVE) > 0) {
                (void)i2c_read_byte_raw(I2C_SLAVE);
            }
        }

        sleep_ms(10);
    }
}
