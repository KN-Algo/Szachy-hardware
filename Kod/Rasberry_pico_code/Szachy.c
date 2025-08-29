#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "Corexy.h"
#include "Multiplexery.h"
#include "Corexy.h"
#include "Elektromagnes.h"
#include "Ledy.h"
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

// Status ostatniej komendy
volatile char last_command = 0;
volatile bool command_completed = false;
volatile bool command_in_progress = false;  // Nowa flaga
volatile uint8_t response_buffer[65]; // Bufor na całą odpowiedź
volatile int response_byte_index = 0;  // Aktualny indeks bajtu do wysłania

//zmienna do przechowywania tego kotry gracz ma teraz ruch
uint8_t current_player = 0; //0 - biały, 1 - czarny

// ============================ I2C INIT ============================

void my_i2c_slave_init() {
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

// Funkcja obsługi żądań odczytu
void handle_read_request() {
    i2c_hw_t *hw = i2c_get_hw(I2C_SLAVE);
    
    printf("🔄 MASTER ŻĄDA ODCZYTU - cmd='%c', completed=%d, in_progress=%d, bajt_idx=%d\n", 
           last_command, command_completed, command_in_progress, response_byte_index);
    
    if (last_command == 'H') {
        if (command_completed) {
            printf("📤 Wysyłam: 'H' (homing zakończony)\n");
            while (!(hw->status & (1u << 1))) {}
            hw->data_cmd = 'H';
        } else if (command_in_progress) {
            printf("📤 Wysyłam: 'W' (homing w trakcie)\n");
            while (!(hw->status & (1u << 1))) {}
            hw->data_cmd = 'W'; // W = Working/Wait
        } else {
            printf("📤 Wysyłam: 'E' (błąd - brak statusu)\n");
            while (!(hw->status & (1u << 1))) {}
            hw->data_cmd = 'E'; // Error
        }
        
    } else if (last_command == 'M') {
        if (command_completed) {
            printf("📤 Wysyłam: 'M' (ruch zakończony)\n");
            while (!(hw->status & (1u << 1))) {}
            hw->data_cmd = 'M';
        } else if (command_in_progress) {
            printf("📤 Wysyłam: 'W' (ruch w trakcie)\n");
            while (!(hw->status & (1u << 1))) {}
            hw->data_cmd = 'W'; // W = Working/Wait
        } else {
            printf("📤 Wysyłam: 'E' (błąd - brak statusu)\n");
            while (!(hw->status & (1u << 1))) {}
            hw->data_cmd = 'E'; // Error
        }
        
    } else if (last_command == 'B' && command_completed) {
        // Dla komendy B, wysyłaj kolejne bajty z bufora
        if (response_byte_index < 65) {
            uint8_t byte_to_send = response_buffer[response_byte_index];
            printf("📤 Wysyłam bajt[%d]: %d ('%c')\n", 
                   response_byte_index, byte_to_send, 
                   (byte_to_send >= 32 && byte_to_send <= 126) ? byte_to_send : '?');
            
            while (!(hw->status & (1u << 1))) {}
            hw->data_cmd = byte_to_send;
            response_byte_index++;
        } else {
            printf("❌ Wszystkie bajty już wysłane, wysyłam 0\n");
            while (!(hw->status & (1u << 1))) {}
            hw->data_cmd = 0;
        }
        
    } else {
        printf("❌ Brak danych (cmd='%c', completed=%d, in_progress=%d)\n", 
               last_command, command_completed, command_in_progress);
        while (!(hw->status & (1u << 1))) {}
        hw->data_cmd = 0;
    }
}

uint8_t new_move_detector(uint8_t board_old[8][8]){
    uint8_t new_move = 0;
    uint8_t board_new[8][8];
    mux_read_8x8(board_new);
    for(int i =0;i<8;i++){
        for(int j=0;j<8;j++){
            if(board_new[i][j] != board_old[i][j]){
                //znaleziono pionek który się ruszył
                new_move = 1;
                break;
            }
        }
    }
    return new_move;
}
// ============================ GŁÓWNY LOOP ============================

int main() {
    stdio_init_all();
    my_i2c_slave_init();
    corexy_init_gpio();
    mux_init();
    elektromagnes_init();
    led_init();

    led_bialy_on();
    led_czarny_off();

    printf("🚀 I2C Slave gotowy na adresie 0x%02X\n", I2C_SLAVE_ADDR);

    while (1) {
        if (new_move_detector(board)) {
            // Wykryto nowy ruch
            if(current_player == 0) {
                // Teraz ruch ma czarny
                current_player = 1;
                led_bialy_off();
                led_czarny_on();
            } else {
                // Teraz ruch ma biały
                current_player = 0;
                led_bialy_on();
                led_czarny_off();
            }
            printf("🔄 Wykryto nowy ruch\n");

            mux_read_8x8(board); // Zaktualizuj planszę
        }

        i2c_hw_t *hw = i2c_get_hw(I2C_SLAVE);
        uint32_t status = hw->intr_stat;
        
        // Sprawdź czy master żąda odczytu
        if (status & (1u << 5)) { // RD_REQ bit
            printf("🔔 ŻĄDANIE ODCZYTU od mastera\n");
            handle_read_request();
            (void)hw->clr_rd_req; // Wyczyść flagę
            printf("✅ Żądanie odczytu obsłużone\n");
        }
        
        // Sprawdź czy są dane do odczytania (nowa komenda)
        int n = i2c_get_read_available(I2C_SLAVE);
        if (n > 0) {
            printf("📨 Otrzymano %d bajtów od mastera\n", n);
            
            command_completed = false; // Nowa komenda rozpoczęta
            response_byte_index = 0;   // Reset indeksu odpowiedzi
            received_cmd.type_of_command = i2c_read_byte_raw(I2C_SLAVE);
            last_command = received_cmd.type_of_command;
            
            printf("📋 Komenda: '%c' (%d)\n", received_cmd.type_of_command, received_cmd.type_of_command);

            switch (received_cmd.type_of_command) {
                case 'H': {
                    printf("🏠 ROZPOCZĘCIE: Homing\n");
                    command_in_progress = true;
                    
                    corexy_home();
                    
                    // Przygotuj odpowiedź
                    response_buffer[0] = 'H';
                    response_byte_index = 0;
                    command_in_progress = false;
                    command_completed = true;
                    printf("✅ ZAKOŃCZENIE: Homing\n");
                } break;

                case 'M': {

                    printf("🎯 ROZPOCZĘCIE: Ruch\n");
                    command_in_progress = true;

                    // Czekamy max 100ms na resztę bajtów
                    printf("   Oczekiwanie na 16 bajtów danych ruchu...\n");
                    absolute_time_t timeout = make_timeout_time_ms(100);
                    while (i2c_get_read_available(I2C_SLAVE) < 16) {
                        if (time_reached(timeout)) {
                            printf("❌ Timeout przy odbiorze danych ruchu\n");
                            command_in_progress = false;
                            break;
                        }
                        tight_loop_contents();
                    }

                    int available = i2c_get_read_available(I2C_SLAVE);
                    printf("   Dostępne bajty: %d\n", available);

                    for (int i = 0; i < 16 && i2c_get_read_available(I2C_SLAVE); i++) {
                        buffer[i] = i2c_read_byte_raw(I2C_SLAVE);
                    }

                    memcpy_reverse(&received_cmd.X_start, &buffer[0], 4);
                    memcpy_reverse(&received_cmd.Y_start, &buffer[4], 4);
                    memcpy_reverse(&received_cmd.X_end,   &buffer[8], 4);
                    memcpy_reverse(&received_cmd.Y_end,   &buffer[12],4);

                    printf("   Ruch: (%.2f,%.2f) -> (%.2f,%.2f)\n", 
                           received_cmd.X_start, received_cmd.Y_start,
                           received_cmd.X_end, received_cmd.Y_end);

                    printf("   Wykonywanie ruchu...\n");
                    corexy_move_to(current_x, current_y, received_cmd.X_start, received_cmd.Y_start, false);
                    corexy_move_to(received_cmd.X_start, received_cmd.Y_start, received_cmd.X_end, received_cmd.Y_end, true);

                    current_x = received_cmd.X_end;
                    current_y = received_cmd.Y_end;
                    
                    // Przygotuj odpowiedź
                    response_buffer[0] = 'M';
                    response_byte_index = 0;
                    command_in_progress = false;
                    command_completed = true;
                    
                    printf("✅ ZAKOŃCZENIE: Ruch\n");

                } break;

                case 'B': {
                    printf("🔍 ROZPOCZĘCIE: Skanowanie planszy\n");
                    mux_read_8x8(board);
                    
                    // Przygotuj bufor odpowiedzi
                    response_buffer[0] = 'R';  // Status byte
                    memcpy((void*)&response_buffer[1], &board[0][0], 64); // 64 bajty planszy
                    response_byte_index = 0;   // Reset indeksu
                    
                    command_completed = true;
                    printf("✅ ZAKOŃCZENIE: Skanowanie planszy\n");
                    
                    // Debug: pokaż fragment planszy
                    printf("   Fragment planszy [0][0-7]: ");
                    for (int i = 0; i < 8; i++) {
                        printf("%d ", board[0][i]);
                    }
                    printf("\n");
                    printf("   Bufor odpowiedzi przygotowany: 'R' + 64 bajty\n");
                } break;

                default:
                    printf("❌ NIEZNANA KOMENDA: '%c' (%d)\n", 
                           received_cmd.type_of_command, received_cmd.type_of_command);
                    last_command = 0;
                    break;
            }
        }

        sleep_ms(1);
    }
}