#include <Arduino.h>
#include "openframe_pins.h"

// OpenFrame M1 Rev A engine controller skeleton.
// This firmware is a safe timing skeleton: hazardous outputs default off.
// External hardware gates must still force HV, LED OE, fuser heat, and motors off
// if any interlock opens or the watchdog fails.

enum EngineState {
  STATE_BOOT,
  STATE_IDLE,
  STATE_WARMING_FUSER,
  STATE_PICKUP,
  STATE_REGISTERING,
  STATE_IMAGING,
  STATE_FUSING,
  STATE_EXITING,
  STATE_COMPLETE,
  STATE_FAULT
};

enum FaultCode {
  FAULT_NONE,
  FAULT_COVER_OPEN,
  FAULT_ESTOP_OPEN,
  FAULT_THERMAL_LOOP_OPEN,
  FAULT_PSU,
  FAULT_HV,
  FAULT_NO_PAPER,
  FAULT_JAM_PRE_REG,
  FAULT_JAM_IMAGE_SYNC,
  FAULT_JAM_FUSER_EXIT,
  FAULT_JAM_EXIT,
  FAULT_FUSER_OVERTEMP,
  FAULT_WATCHDOG
};

static EngineState state = STATE_BOOT;
static FaultCode fault = FAULT_NONE;
static uint32_t state_started_ms = 0;
static uint32_t imaging_t0_us = 0;
static uint32_t imaging_lines_fired = 0;

static bool line_ok(int pin) {
  return digitalRead(pin) == HIGH;
}

static bool active_low_sensor_seen(int pin) {
  return digitalRead(pin) == LOW;
}

static bool hard_interlocks_ok() {
  return line_ok(PIN_COVER_CLOSED_LOOP) &&
         line_ok(PIN_ESTOP_LOOP_CLOSED) &&
         line_ok(PIN_THERMOSTAT_LOOP_CLOSED) &&
         line_ok(PIN_THERMAL_FUSE_CLOSED) &&
         line_ok(PIN_PSU_FAULT_N);
}

static void hazardous_outputs_off() {
  digitalWrite(PIN_HV_ENABLE_REQUEST, LOW);
  digitalWrite(PIN_LED_OE_REQUEST, LOW);
  digitalWrite(PIN_LED_SAFE_EN_REQUEST, LOW);
  digitalWrite(PIN_FUSER_HEATER_REQUEST, LOW);
  digitalWrite(PIN_MAIN_MOTOR_ENABLE, LOW);
  digitalWrite(PIN_STEPPER_ENABLE_N, HIGH);
}

static void enter_state(EngineState next) {
  state = next;
  state_started_ms = millis();
}

static void enter_fault(FaultCode code) {
  fault = code;
  hazardous_outputs_off();
  digitalWrite(PIN_FAN_ENABLE, HIGH);
  enter_state(STATE_FAULT);
}

static void check_interlocks_or_fault() {
  if (!line_ok(PIN_COVER_CLOSED_LOOP)) enter_fault(FAULT_COVER_OPEN);
  else if (!line_ok(PIN_ESTOP_LOOP_CLOSED)) enter_fault(FAULT_ESTOP_OPEN);
  else if (!line_ok(PIN_THERMOSTAT_LOOP_CLOSED) || !line_ok(PIN_THERMAL_FUSE_CLOSED)) enter_fault(FAULT_THERMAL_LOOP_OPEN);
  else if (!line_ok(PIN_PSU_FAULT_N)) enter_fault(FAULT_PSU);
  else if (!line_ok(PIN_HV_FAULT_N)) enter_fault(FAULT_HV);
}

static void setup_pins() {
  pinMode(PIN_COVER_CLOSED_LOOP, INPUT_PULLDOWN);
  pinMode(PIN_ESTOP_LOOP_CLOSED, INPUT_PULLDOWN);
  pinMode(PIN_THERMOSTAT_LOOP_CLOSED, INPUT_PULLDOWN);
  pinMode(PIN_THERMAL_FUSE_CLOSED, INPUT_PULLDOWN);
  pinMode(PIN_PSU_FAULT_N, INPUT_PULLUP);
  pinMode(PIN_HV_FAULT_N, INPUT_PULLUP);

  pinMode(PIN_PRE_REG_SENSOR_N, INPUT_PULLUP);
  pinMode(PIN_IMAGE_SYNC_SENSOR_N, INPUT_PULLUP);
  pinMode(PIN_FUSER_EXIT_SENSOR_N, INPUT_PULLUP);
  pinMode(PIN_EXIT_SENSOR_N, INPUT_PULLUP);
  pinMode(PIN_TRAY_PRESENT_N, INPUT_PULLUP);
  pinMode(PIN_PAPER_PRESENT_N, INPUT_PULLUP);

  pinMode(PIN_MAIN_MOTOR_ENABLE, OUTPUT);
  pinMode(PIN_STEPPER_ENABLE_N, OUTPUT);
  pinMode(PIN_PICKUP_STEP, OUTPUT);
  pinMode(PIN_PICKUP_DIR, OUTPUT);
  pinMode(PIN_REG_STEP, OUTPUT);
  pinMode(PIN_REG_DIR, OUTPUT);
  pinMode(PIN_LED_LINE_STROBE, OUTPUT);
  pinMode(PIN_LED_LATCH, OUTPUT);
  pinMode(PIN_LED_OE_REQUEST, OUTPUT);
  pinMode(PIN_LED_SAFE_EN_REQUEST, OUTPUT);
  pinMode(PIN_HV_ENABLE_REQUEST, OUTPUT);
  pinMode(PIN_FUSER_HEATER_REQUEST, OUTPUT);
  pinMode(PIN_FAN_ENABLE, OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);

  hazardous_outputs_off();
  digitalWrite(PIN_FAN_ENABLE, LOW);
  digitalWrite(PIN_STATUS_LED, LOW);
}

void setup() {
  Serial.begin(115200);
  setup_pins();
  enter_state(STATE_IDLE);
  Serial.println("OpenFrame M1 Rev A controller booted; hazardous outputs default off");
}

static void step_pin_once(int pin) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(4);
  digitalWrite(pin, LOW);
}

static void run_pickup_stepper_burst() {
  digitalWrite(PIN_STEPPER_ENABLE_N, LOW);
  digitalWrite(PIN_PICKUP_DIR, HIGH);
  for (int i = 0; i < 40; i++) {
    step_pin_once(PIN_PICKUP_STEP);
    delayMicroseconds(180);
  }
}

static void run_registration_stepper_burst() {
  digitalWrite(PIN_STEPPER_ENABLE_N, LOW);
  digitalWrite(PIN_REG_DIR, HIGH);
  for (int i = 0; i < 40; i++) {
    step_pin_once(PIN_REG_STEP);
    delayMicroseconds(95);
  }
}

static void fire_one_line_strobe() {
  digitalWrite(PIN_LED_LINE_STROBE, HIGH);
  delayMicroseconds(1);
  digitalWrite(PIN_LED_LINE_STROBE, LOW);
}

void loop() {
  check_interlocks_or_fault();

  switch (state) {
    case STATE_IDLE:
      hazardous_outputs_off();
      digitalWrite(PIN_STATUS_LED, millis() % 1000 < 500 ? HIGH : LOW);
      // Cold-rig behavior: send 'p' over serial to run one paper motion cycle.
      if (Serial.available() && Serial.read() == 'p') {
        if (!hard_interlocks_ok()) enter_fault(FAULT_COVER_OPEN);
        else if (!active_low_sensor_seen(PIN_TRAY_PRESENT_N) || !active_low_sensor_seen(PIN_PAPER_PRESENT_N)) enter_fault(FAULT_NO_PAPER);
        else enter_state(STATE_PICKUP);
      }
      break;

    case STATE_PICKUP:
      digitalWrite(PIN_MAIN_MOTOR_ENABLE, HIGH);
      run_pickup_stepper_burst();
      if (millis() - state_started_ms > 1500 && !active_low_sensor_seen(PIN_PRE_REG_SENSOR_N)) enter_fault(FAULT_JAM_PRE_REG);
      if (active_low_sensor_seen(PIN_PRE_REG_SENSOR_N)) enter_state(STATE_REGISTERING);
      break;

    case STATE_REGISTERING:
      digitalWrite(PIN_MAIN_MOTOR_ENABLE, HIGH);
      if (millis() - state_started_ms > OPENFRAME_REGISTRATION_HOLD_MS) {
        run_registration_stepper_burst();
        imaging_t0_us = micros();
        imaging_lines_fired = 0;
        enter_state(STATE_IMAGING);
      }
      break;

    case STATE_IMAGING:
      // Cold-rig default: only timing strobe is exercised. LED OE and HV remain off.
      while (imaging_lines_fired < OPENFRAME_LETTER_LINES && state == STATE_IMAGING) {
        uint32_t ideal_offset_us = (uint32_t)(((uint64_t)imaging_lines_fired * OPENFRAME_LINE_PERIOD_NS + 500) / 1000);
        if ((uint32_t)(micros() - imaging_t0_us) >= ideal_offset_us) {
          fire_one_line_strobe();
          imaging_lines_fired++;
          if (!hard_interlocks_ok()) enter_fault(FAULT_COVER_OPEN);
        }
      }
      if (state == STATE_IMAGING) enter_state(STATE_FUSING);
      break;

    case STATE_FUSING:
      // Heater remains off in this skeleton. This state exists for timing and sensor validation.
      if (millis() - state_started_ms > 1200) {
        if (!active_low_sensor_seen(PIN_FUSER_EXIT_SENSOR_N)) enter_fault(FAULT_JAM_FUSER_EXIT);
        else enter_state(STATE_EXITING);
      }
      break;

    case STATE_EXITING:
      if (millis() - state_started_ms > 1200) {
        if (!active_low_sensor_seen(PIN_EXIT_SENSOR_N)) enter_fault(FAULT_JAM_EXIT);
        else enter_state(STATE_COMPLETE);
      }
      break;

    case STATE_COMPLETE:
      hazardous_outputs_off();
      Serial.println("cold paper cycle complete");
      enter_state(STATE_IDLE);
      break;

    case STATE_FAULT:
      hazardous_outputs_off();
      digitalWrite(PIN_STATUS_LED, millis() % 200 < 100 ? HIGH : LOW);
      if (Serial.available() && Serial.read() == 'r') {
        fault = FAULT_NONE;
        enter_state(STATE_IDLE);
      }
      break;

    case STATE_BOOT:
    case STATE_WARMING_FUSER:
    default:
      enter_state(STATE_IDLE);
      break;
  }
}
