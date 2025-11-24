// src/main.cpp
#include "main.h" // ALWAYS include this in PROS

// --------------------- Motor Ports ---------------------
constexpr int LEFT_TOP_PORT = 2;
constexpr int LEFT_BOTTOM_PORT = 7;
constexpr int RIGHT_TOP_PORT = 15;
constexpr int RIGHT_BOTTOM_PORT = 6;
constexpr int LEFT_BOTTOM_TOP_PORT = 21;
constexpr int RIGHT_BOTTOM_TOP_PORT = 18;
constexpr int BOTTOM_INTAKE_PORT = 1;
constexpr int TOP_INTAKE_PORT = 9;
constexpr int OUTAKE_PORT = 8;

// --------------------- Motors ---------------------

// Left Drive
pros::Motor LeftTopM(LEFT_TOP_PORT, pros::MotorGears::blue, pros::MotorUnits::degrees);
pros::Motor LeftBottomM(LEFT_BOTTOM_PORT, pros::MotorGears::blue, pros::MotorUnits::degrees);
pros::Motor LeftBottomTop(LEFT_BOTTOM_TOP_PORT, pros::MotorGears::blue, pros::MotorUnits::degrees);

// Right Drive
pros::Motor RightTopM(RIGHT_TOP_PORT, pros::MotorGears::blue, pros::MotorUnits::degrees);
pros::Motor RightBottomM(RIGHT_BOTTOM_PORT, pros::MotorGears::blue, pros::MotorUnits::degrees);
pros::Motor RightBottomTop(RIGHT_BOTTOM_TOP_PORT, pros::MotorGears::blue, pros::MotorUnits::degrees);

// Intakes (Green Cartridge / 200 RPM)
pros::Motor BottomIntake(BOTTOM_INTAKE_PORT, pros::MotorGears::green, pros::MotorUnits::degrees);
pros::Motor TopIntake(TOP_INTAKE_PORT, pros::MotorGears::green, pros::MotorUnits::degrees);

// Outake (Blue Cartridge / 600 RPM)
pros::Motor Outake(OUTAKE_PORT, pros::MotorGears::blue, pros::MotorUnits::degrees);

// --------------------- Sensors ---------------------
// IMU on port 16
pros::Imu Inertial16(16);

// Pneumatics
pros::adi::DigitalOut DigitalOutADescore('H');
pros::adi::DigitalOut DigitalOutBScoop('B');

// --------------------- Controller ---------------------
pros::Controller master(pros::E_CONTROLLER_MASTER);

// --------------------- Utilities ---------------------
static void initializeRandomSeed() {
    uint32_t ms = pros::millis();
    double batteryVoltage = pros::battery::get_voltage();
    double batteryCurrent = pros::battery::get_current();
    int seed = static_cast<int>(ms & 0x7FFFFFFF) + static_cast<int>(batteryVoltage * 100.0) + static_cast<int>(batteryCurrent * 100.0);
    srand(seed);
}

// --------------------- Lifecycle ---------------------
void initialize() {
    // 1. Initialize LCD immediately so we know the code is running
    pros::lcd::initialize();
    pros::lcd::set_text(1, "System Booting...");

    // Right side is usually reversed in tank drive
    LeftTopM.set_reversed(false);
    LeftBottomM.set_reversed(false);
    LeftBottomTop.set_reversed(true);

    RightTopM.set_reversed(true);
    RightBottomM.set_reversed(true);
    RightBottomTop.set_reversed(false);


    // Reverse Outtake
    Outake.set_reversed(true);

    // 3. Random Seed
    initializeRandomSeed();

    pros::lcd::set_text(1, "Wsp Boy - Ready");
}

void disabled() {}

void competition_initialize() {}

void autonomous() {
    /* pros::lcd::set_text(2, "Auton: Driving Forward");

    // Drive power
    int power = 35;

    // Move forward
    LeftTopM.move(power);
    LeftBottomM.move(power);
    LeftBottomTop.move(power);
    RightTopM.move(power);
    RightBottomM.move(power);
    RightBottomTop.move(power);

    pros::delay(500); // Move for 1 second (1000 ms)

    // Stop the motors
    LeftTopM.move(0);
    LeftBottomM.move(0);
    LeftBottomTop.move(0);
    RightTopM.move(0);
    RightBottomM.move(0);
    RightBottomTop.move(0);

    pros::lcd::set_text(2, "Auton Complete"); */
}

// --------------------- Operator Control ---------------------
void opcontrol() {
    // Toggles and State Variables
    bool intakeToggleForward = false;
    bool intakeToggleReverse = false;
    bool R1_lastState = false;
    bool R2_lastState = false;
    bool L1_lastState = false;
    bool L2_lastState = false;
    bool outakeToggleForward = false;
    bool outakeToggleReverse = false;

    bool pistonStateDescore = false;
    bool A_lastStateDescore = false;
    bool pistonStateScoop = false;
    bool B_lastStateScoop = false;

    while (true) {
        // Tank Drive Control
        int left_raw = master.get_analog(pros::E_CONTROLLER_ANALOG_LEFT_Y);
        int right_raw = master.get_analog(pros::E_CONTROLLER_ANALOG_RIGHT_Y);
        LeftTopM.move(left_raw);
        LeftBottomM.move(left_raw);
        LeftBottomTop.move(left_raw);
        RightTopM.move(right_raw);
        RightBottomM.move(right_raw);
        RightBottomTop.move(right_raw);

        // Intake Logic (R1/R2 Toggles)
        bool R1_currentState = master.get_digital(pros::E_CONTROLLER_DIGITAL_R1);
        bool R2_currentState = master.get_digital(pros::E_CONTROLLER_DIGITAL_R2);

        if (R1_currentState && !R1_lastState) {
            intakeToggleReverse = !intakeToggleReverse;
            if (intakeToggleReverse) intakeToggleForward = false;
        }
        if (R2_currentState && !R2_lastState) {
            intakeToggleForward = !intakeToggleForward;
            if (intakeToggleForward) intakeToggleReverse = false;
        }
        R1_lastState = R1_currentState;
        R2_lastState = R2_currentState;

        // Outake Logic (L1 Forward, L2 Reverse)
        bool L1_currentState = master.get_digital(pros::E_CONTROLLER_DIGITAL_L1);
        bool L2_currentState = master.get_digital(pros::E_CONTROLLER_DIGITAL_L2);

        if (L1_currentState && !L1_lastState) {
            // L1 now toggles FORWARD
            outakeToggleForward = !outakeToggleForward;
            if (outakeToggleForward) outakeToggleReverse = false;
        }

        if (L2_currentState && !L2_lastState) {
            // L2 now toggles REVERSE
            outakeToggleReverse = !outakeToggleReverse;
            if (outakeToggleReverse) outakeToggleForward = false;
        }

        L1_lastState = L1_currentState;
        L2_lastState = L2_currentState;


        // Pneumatics: Descore (Button A) - Uses original DigitalOutAScoop('H')
        bool A_currentState = master.get_digital(pros::E_CONTROLLER_DIGITAL_A);
        if (A_currentState && !A_lastStateDescore) {
            pistonStateDescore = !pistonStateDescore;
            DigitalOutADescore.set_value(pistonStateDescore);
        }
        A_lastStateDescore = A_currentState;

        // Pneumatics: Scoop (Button B) - Uses original DigitalOutBDescore('B')
        bool B_currentState = master.get_digital(pros::E_CONTROLLER_DIGITAL_B);
        if (B_currentState && !B_lastStateScoop) {
            pistonStateScoop = !pistonStateScoop;
            DigitalOutBScoop.set_value(pistonStateScoop);
        }
        B_lastStateScoop = B_currentState;

        // Actuate Motors
        int intakePower = 0;
        if (intakeToggleForward)
            intakePower = 127;
        else if (intakeToggleReverse)
            intakePower = -127;

        BottomIntake.move(intakePower);
        TopIntake.move(intakePower);

        int outakePower = 0;
        if (outakeToggleForward)
            outakePower = 127;
        else if (outakeToggleReverse)
            outakePower = -127;

        Outake.move(outakePower);


        // LCD Feedback
        pros::lcd::print(1, "Intake: %s", intakeToggleForward ? "FWD" : intakeToggleReverse ? "REV" : "OFF");
        pros::lcd::print(2, "Outake: %s",
            outakeToggleForward ? "FWD" :
            outakeToggleReverse ? "REV" :
            "OFF"
        );
        pros::lcd::print(3, "Descore (A): %s", pistonStateDescore ? "OUT" : "IN");
        pros::lcd::print(4, "Scoop (B): %s", pistonStateScoop ? "OUT" : "IN");

        pros::delay(20); // Standard 20ms loop delay
    }
}