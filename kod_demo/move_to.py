# Zakładamy: 1 mm = 80 mikrokroków, w finalnej wersji trzeba będzie zaimplementować do tego stałą zmienną 
STEPS_PER_MM = 80

def move_to(x_target: float, y_target: float, motor_x, motor_y):
    """Move working member to position (x,y)"""

    #zmienne pozycji które będą widoczne dla wszystkich plików
    global x_pos, y_pos

    # Obliczenie dystansu w mm
    distance_x = x_target - x_pos
    distance_y = y_target - y_pos

    # Obliczenie kroków
    steps_x = int(distance_x * STEPS_PER_MM)
    steps_y = int(distance_y * STEPS_PER_MM)

    # Kierunek (True = przód, False = tył)
    dir_x = steps_x >= 0
    dir_y = steps_y >= 0

    # Ustawiamy kierunek
    motor_x.set_direction_reg(dir_x)
    motor_y.set_direction_reg(dir_y)

    # Uruchom ruch (absolutny)
    motor_x.run_to_position_steps(abs(steps_x))
    motor_y.run_to_position_steps(abs(steps_y))

    # Aktualizuj pozycję
    x_pos = x_target
    y_pos = y_target