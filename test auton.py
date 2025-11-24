# main.py
# Converted from PROS C++ to Python
# NOTE: Replace the hardware stubs below with your real VEX/PROS Python API.
# Example: from vex import Motor, Controller, Inertial, DigitalOut, Brain

import time
import random

# --------------------- Hardware stubs (replace these with your real API) ---------------------
class Motor:
    def __init__(self, port, gearing=None, units=None):
        self.port = port
        self.reversed = False
        self.power = 0

    def set_reversed(self, value: bool):
        self.reversed = bool(value)

    def move(self, power: int):
        # power expected -127..127 (matching your original)
        if self.reversed:
            power = -power
        self.power = int(power)
        # Replace with the actual motor command, e.g. motor.spin(DirectionType.FWD, power, VelocityUnits.PCT)
        # For now we print for debugging:
        # print(f"Motor port {self.port} move {self.power}")

class Inertial:
    def __init__(self, port):
        self.port = port

class DigitalOut:
    def __init__(self, port_letter):
        self.port = port_letter
        self.state = False

    def set_value(self, v: bool):
        self.state = bool(v)
        # Replace with actual pneumatics control

class Controller:
    # This stub simulates a controller. Replace with real controller object.
    def __init__(self):
        # analog values: keys 'left_y', 'right_y'
        self._analogs = {'left_y': 0, 'right_y': 0}
        # digital buttons stored as booleans
        self._digital = {}

    # In real API you would call e.g. controller.axis.A.value() or controller.button.X.pressing()
    def get_analog(self, which: str) -> int:
        return int(self._analogs.get(which, 0))

    def get_digital(self, which: str) -> bool:
        return bool(self._digital.get(which, False))

    # Helpers for testing (not used on robot)
    def _set_analog(self, which, value):
        self._analogs[which] = value

    def _set_button(self, which, value):
        self._digital[which] = bool(value)

class LCD:
    def __init__(self):
        self.lines = {}

    def initialize(self):
        pass

    def set_text(self, line, text):
        self.lines[line] = str(text)
        # print for debug
        # print(f"LCD line {line}: {text}")

    def print(self, line, fmt, *args):
        text = fmt % args if args else fmt
        self.set_text(line, text)

# --------------------- Port constants ---------------------
LEFT_TOP_PORT = 2
LEFT_BOTTOM_PORT = 7
RIGHT_TOP_PORT = 15
RIGHT_BOTTOM_PORT = 6
LEFT_BOTTOM_TOP_PORT = 21
RIGHT_BOTTOM_TOP_PORT = 18
BOTTOM_INTAKE_PORT = 1
TOP_INTAKE_PORT = 9
OUTAKE_PORT = 8

# --------------------- Instantiate hardware (replace with real API calls) ---------------------
LeftTopM = Motor(LEFT_TOP_PORT)
LeftBottomM = Motor(LEFT_BOTTOM_PORT)
LeftBottomTop = Motor(LEFT_BOTTOM_TOP_PORT)

RightTopM = Motor(RIGHT_TOP_PORT)
RightBottomM = Motor(RIGHT_BOTTOM_PORT)
RightBottomTop = Motor(RIGHT_BOTTOM_TOP_PORT)

BottomIntake = Motor(BOTTOM_INTAKE_PORT)
TopIntake = Motor(TOP_INTAKE_PORT)

Outake = Motor(OUTAKE_PORT)

Inertial16 = Inertial(16)
DigitalOutADescore = DigitalOut('H')
DigitalOutBScoop = DigitalOut('B')

master = Controller()
lcd = LCD()

# --------------------- Utilities ---------------------
def initialize_random_seed():
    ms = int(time.time() * 1000) & 0x7FFFFFFF
    # No battery API in this generic stub; use time + pid for entropy
    seed = ms + int(time.process_time() * 1000) + random.getrandbits(16)
    random.seed(seed)

# --------------------- Lifecycle functions ---------------------
def initialize():
    lcd.initialize()
    lcd.set_text(1, "System Booting...")

    # Motor reversals (mirror of your C++ code)
    LeftTopM.set_reversed(False)
    LeftBottomM.set_reversed(False)
    LeftBottomTop.set_reversed(True)

    RightTopM.set_reversed(True)
    RightBottomM.set_reversed(True)
    RightBottomTop.set_reversed(False)

    Outake.set_reversed(True)

    initialize_random_seed()

    lcd.set_text(1, "Wsp Boy - Ready")

def disabled():
    # Called when disabled; keep minimal
    pass

def competition_initialize():
    # Called before competition; keep minimal
    pass



#______________________________________________________________________________________________________________________________________________________________________
DRIVETRAIN_MOTORS_LEFT = [LeftBottomM,LeftBottomTop,LeftTopM]
DRIVETRAIN_MOTORS_RIGHT = [RightBottomM,RightBottomTop,RightTopM]

def _set_drive_power(left_power: int, right_power: int):
    for m in DRIVETRAIN_MOTORS_LEFT:
        m.move(int(left_power))
    for m in DRIVETRAIN_MOTORS_RIGHT:
        m.move(int(right_power))

def stop_drive():
    _set_drive_power(0, 0)

def forward(power: int = 100, ms: int | None = None):
    p = max(-127, min(127, int(power)))
    _set_drive_power(p, p)
    if ms is not None:
        time.sleep(ms / 1000.0)
        stop_drive()

def backward(power: int = 100, ms: int | None = None):
    forward(-abs(int(power)), ms)

def turn_right(power: int = 100, ms: int | None = None):
    p = max(0, min(127, int(abs(power))))
    _set_drive_power(p, -p)
    if ms is not None:
        time.sleep(ms / 1000.0)
        stop_drive()

def turn_left(power: int = 100, ms: int | None = None):
    p = max(0, min(127, int(abs(power))))
    _set_drive_power(-p, p)
    if ms is not None:
        time.sleep(ms / 1000.0)
        stop_drive()

# ----------------- Actuator state + functions -----------------
# Keep module-level state so autonomous can turn things on/off deterministically.
intake_state = 0    # 0 = off, 1 = forward, -1 = reverse
outake_state = 0    # 0 = off, 1 = forward, -1 = reverse (if you support reverse)
scoop_state = False # False = IN, True = OUT (pneumatic)

def intake_set(power: int):
    """Internal: set intake motors to given power (signed)."""
    BottomIntake.move(int(power))
    TopIntake.move(int(power))

def intake_on(power: int = 127):
    global intake_state
    intake_state = 1
    intake_set(max(-127, min(127, int(power))))

def intake_reverse(power: int = -127):
    global intake_state
    intake_state = -1
    intake_set(max(-127, min(127, int(power))))

def intake_off():
    global intake_state
    intake_state = 0
    intake_set(0)

def intake_on_for(ms: int, power: int = 127):
    """Turn intake on for ms milliseconds, then turn off."""
    intake_on(power)
    time.sleep(ms / 1000.0)
    intake_off()

# Outake (single motor)
def outake_set(power: int):
    Outake.move(int(power))

def outake_on(power: int = 127):
    global outake_state
    outake_state = 1
    outake_set(max(-127, min(127, int(power))))

def outake_reverse(power: int = -127):
    global outake_state
    outake_state = -1
    outake_set(max(-127, min(127, int(power))))

def outake_off():
    global outake_state
    outake_state = 0
    outake_set(0)

def outake_on_for(ms: int, power: int = 127):
    outake_on(power)
    time.sleep(ms / 1000.0)
    outake_off()

# Scoop (pneumatic) using your DigitalOutBScoop
def scoop_on():
    global scoop_state
    scoop_state = True
    DigitalOutBScoop.set_value(True)

def scoop_off():
    global scoop_state
    scoop_state = False
    DigitalOutBScoop.set_value(False)

# A convenience that matches your controller toggles: toggle versions
def scoop_toggle():
    global scoop_state
    scoop_state = not scoop_state
    DigitalOutBScoop.set_value(scoop_state)

def intake_toggle_forward():
    """Simulate the R2 toggle: if off -> forward, if forward->off (no reverse here)."""
    if intake_state == 1:
        intake_off()
    else:
        intake_on()

def intake_toggle_reverse():
    """Simulate the R1 toggle: if off -> reverse, if reverse->off."""
    if intake_state == -1:
        intake_off()
    else:
        intake_reverse()

def outake_toggle_forward():
    if outake_state == 1:
        outake_off()
    else:
        outake_on()

def outake_toggle_reverse():
    if outake_state == -1:
        outake_off()
    else:
        outake_reverse()

# ----------------- Autonomous routine (your requested sequence) -----------------
def autonomous_routine():
    """
    Sequence you described:
      1) forward just a bit
      2) turn right
      3) straight
      4) activate scoop
      5) turn right
      6) straight
      7) activate intake for a bit
      8) off intake
      9) go back
      10) activate intake + outake and deactivate scoop
      11) off intake and outake
      12) forward just a bit
      13) turn right and turn on intake
      14) right like 30 degrees (short turn)
      15) off intake
    """

    # 1: forward just a bit
    forward(100, 200) 

    # 2: turn right
    turn_right(90, 300)

    # 3: straight
    forward(100, 600)

    # 4: activate scoop (piston out)
    scoop_on()
    time.sleep(0.3)          # 300ms for piston movement

    # 5: turn right
    turn_right(90, 300)

    # 6: straight
    forward(100, 600)

    # 7: activate intake for a bit
    intake_on_for(400, 120)  # run intake ~400ms at 120 power

    # 8: off intake (intake_on_for already turns it off)
    # intake_off()  # not necessary

    # 9: go back
    backward(100, 700)

    # 10: activate intake + outake and deactivate scoop
    intake_on(127)
    outake_on(127)
    scoop_off()              # retract scoop
    time.sleep(300/1000.0)   # run for 300ms

    # 11: off intake and outake
    intake_off()
    outake_off()

    # 12: forward just a bit
    forward(100, 200)

    # 13: turn right and turn on intake
    intake_on(127)
    turn_right(90, 300)

    # 14: right like 30 degrees (shorter turn)
    # Using a shorter time approximates a smaller angle — tweak ms until ~30°
    turn_right(90, 150)

    # 15: off intake
    intake_off()

    # ensure stop
    stop_drive()#________________________________________________________________________________________________________________________________--

# --------------------- Operator Control ---------------------
def opcontrol():
    # Toggles and state variables
    intakeToggleForward = False
    intakeToggleReverse = False
    R1_lastState = False
    R2_lastState = False
    L1_lastState = False
    L2_lastState = False
    outakeToggleForward = False
    outakeToggleReverse = False

    pistonStateDescore = False
    A_lastStateDescore = False
    pistonStateScoop = False
    B_lastStateScoop = False

    try:
        while True:
            # Tank Drive Control
            left_raw = master.get_analog('left_y')    # map to -127..127 in your real API
            right_raw = master.get_analog('right_y')
            LeftTopM.move(left_raw)
            LeftBottomM.move(left_raw)
            LeftBottomTop.move(left_raw)
            RightTopM.move(right_raw)
            RightBottomM.move(right_raw)
            RightBottomTop.move(right_raw)

            # Intake logic (R1/R2 toggles)
            R1_currentState = master.get_digital('R1')
            R2_currentState = master.get_digital('R2')

            if R1_currentState and not R1_lastState:
                intakeToggleReverse = not intakeToggleReverse
                if intakeToggleReverse:
                    intakeToggleForward = False

            if R2_currentState and not R2_lastState:
                intakeToggleForward = not intakeToggleForward
                if intakeToggleForward:
                    intakeToggleReverse = False

            R1_lastState = R1_currentState
            R2_lastState = R2_currentState

            # Outake logic (L1 forward, L2 reverse)
            L1_currentState = master.get_digital('L1')
            L2_currentState = master.get_digital('L2')

            if L1_currentState and not L1_lastState:
                outakeToggleForward = not outakeToggleForward
                if outakeToggleForward:
                    outakeToggleReverse = False

            if L2_currentState and not L2_lastState:
                outakeToggleReverse = not outakeToggleReverse
                if outakeToggleReverse:
                    outakeToggleForward = False

            L1_lastState = L1_currentState
            L2_lastState = L2_currentState

            # Pneumatics: Descore (Button A)
            A_currentState = master.get_digital('A')
            if A_currentState and not A_lastStateDescore:
                pistonStateDescore = not pistonStateDescore
                DigitalOutADescore.set_value(pistonStateDescore)
            A_lastStateDescore = A_currentState

            # Pneumatics: Scoop (Button B)
            B_currentState = master.get_digital('B')
            if B_currentState and not B_lastStateScoop:
                pistonStateScoop = not pistonStateScoop
                DigitalOutBScoop.set_value(pistonStateScoop)
            B_lastStateScoop = B_currentState

            # Actuate motors
            intakePower = 0
            if intakeToggleForward:
                intakePower = 127
            elif intakeToggleReverse:
                intakePower = -127

            BottomIntake.move(intakePower)
            TopIntake.move(intakePower)

            outakePower = 0
            if outakeToggleForward:
                outakePower = 127
            elif outakeToggleReverse:
                outakePower = -127

            Outake.move(outakePower)

            # LCD feedback
            lcd.print(1, "Intake: %s", "FWD" if intakeToggleForward else "REV" if intakeToggleReverse else "OFF")
            lcd.print(2, "Outake: %s", "FWD" if outakeToggleForward else "REV" if outakeToggleReverse else "OFF")
            lcd.print(3, "Descore (A): %s", "OUT" if pistonStateDescore else "IN")
            lcd.print(4, "Scoop (B): %s", "OUT" if pistonStateScoop else "IN")

            # Loop delay - 20ms
            time.sleep(0.02)
    except KeyboardInterrupt:
        # Allow graceful exit during testing on PC
        pass

# --------------------- Run if this module is main ---------------------
if __name__ == "__main__":
    initialize()
    # Call opcontrol for testing; on competition you would call the appropriate lifecycle
    print("Starting opcontrol (press Ctrl+C to stop)...")
    opcontrol()
