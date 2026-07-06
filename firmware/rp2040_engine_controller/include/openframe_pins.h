#pragma once

// OpenFrame M1 Rev A RP2040 pin contract.
// All hazardous outputs are active only through external hardware gates.

#define PIN_COVER_CLOSED_LOOP       2
#define PIN_ESTOP_LOOP_CLOSED       3
#define PIN_THERMOSTAT_LOOP_CLOSED  4
#define PIN_THERMAL_FUSE_CLOSED     5
#define PIN_PSU_FAULT_N             6
#define PIN_HV_FAULT_N              7

#define PIN_PRE_REG_SENSOR_N        8
#define PIN_IMAGE_SYNC_SENSOR_N     9
#define PIN_FUSER_EXIT_SENSOR_N     10
#define PIN_EXIT_SENSOR_N           11
#define PIN_TRAY_PRESENT_N          12
#define PIN_PAPER_PRESENT_N         13

#define PIN_MAIN_MOTOR_ENABLE       14
#define PIN_STEPPER_ENABLE_N        15
#define PIN_PICKUP_STEP             16
#define PIN_PICKUP_DIR              17
#define PIN_REG_STEP                18
#define PIN_REG_DIR                 19

#define PIN_LED_LINE_STROBE         20
#define PIN_LED_LATCH               21
#define PIN_LED_OE_REQUEST          22
#define PIN_LED_SAFE_EN_REQUEST     23

#define PIN_HV_ENABLE_REQUEST       24
#define PIN_FUSER_HEATER_REQUEST    25
#define PIN_FAN_ENABLE              26
#define PIN_STATUS_LED              27

// RP2040 ADC pins are GPIO26-GPIO29 on many boards. This skeleton names the
// logical ADC channels instead of binding to every board variant.
#define ADC_PCR_MON                 0
#define ADC_DEV_MON                 1
#define ADC_XFER_MON                2
#define ADC_FUSER_THERMISTOR        3

#define OPENFRAME_DPI               600
#define OPENFRAME_LED_PIXELS        5120
#define OPENFRAME_LINE_BYTES        640
#define OPENFRAME_LETTER_LINES      6600
#define OPENFRAME_LINE_PERIOD_NS    682796
#define OPENFRAME_REGISTRATION_HOLD_MS 120
