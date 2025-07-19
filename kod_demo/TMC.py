#importujemy biblioteke oraz funkcje których bedziemy używać 
try:
    from src.tmc_driver.tmc_2209 import *
except ModuleNotFoundError:
    from tmc_driver.tmc_2209 import *


from move_to import move_to

#docelowo plik z wartościami parametrów jakie będziemy chcieli aby silniczki przyjmowały
from config_file import *


#tworzymy obiekty reprezentujące nasze silniczki
motor_x = Tmc2209(
    TmcEnableControlPin(19),
    TmcMotionControlStepDir(23, 24),
    TmcComUart("/dev/serial0")
)

motor_y = Tmc2209(
    TmcEnableControlPin(26),
    TmcMotionControlStepDir(25, 8),
    TmcComUart("/dev/serial1")
)

#konfigurujemy ustawienia silniczków
for motor in (motor_x, motor_y):
    motor.set_current(current)
    motor.set_interpolation(True)
    motor.set_microstepping_resolution(ms_resolution)  # 1/16
    motor.set_motor_enabled(True)
    motor.set_acceleration(acceleration)
    motor.set_maxspeed(max_speed)
    motor.set_stallguard_threshold(sg_threshold)
    motor.set_coolstep_threshold(cs_threshold)


#wykonujemy funkcję move to
move_to(x,y,motor_x,motor_y)

#wyłączamy silniki oraz usówamy obiekty
for motor in (motor_x, motor_y):
    motor.set_motor_enabled(False)
    del motor


