#pragma once

// --- Piny sterujące CoreXY ---
#define STEP_PIN_X      2
#define DIR_PIN_X       3
#define STEP_PIN_Y      4
#define DIR_PIN_Y       5
#define ENDSTOP_X_PIN   6
#define ENDSTOP_Y_PIN   7

// Piny adresowe (wspólne dla wszystkich multiplexerów)
#define MUX_S0 14
#define MUX_S1 15
#define MUX_S2 16
#define MUX_S3 17

// Piny EN dla każdego multiplexerów
#define MUX1_EN 18
#define MUX2_EN 19
#define MUX3_EN 20
#define MUX4_EN 21

// Pin SIG dla każdego multiplexerów
#define MUX_SIG 8


// Pin do sterowanie PWM eletromagensem:
#define ELEKTROMAGNES_PIN 26

// Piny do sterowania ledami 
#define LED_BIALE 22
#define LED_CZARNE 9
