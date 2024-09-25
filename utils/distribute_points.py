import numpy as np
import random

def approx_points():
    '''функция, которая распределяет очки в дуэли'''
    mean = 120
    stddev = 50

    # специальные комбинации
    weak_combination_chance = 0.05  # 5% на weak комбинацию
    lower_legendary_combination_chance = 0.05  # 5% на lower legendary комбинацию
    upper_legendary_combination_chance = 0.015  # 1.5% на upper legendary комбинацию

    # генерируем
    weak_combination = random.randint(1, 30)
    lower_legendary_combination = random.randint(250, 400)
    upper_legendary_combination = random.randint(400, 800)
    
    # генерация обычных очков по нормальному распределению
    normal_points = max(1, int(np.random.normal(mean, stddev)))

    roll = random.random()

    if roll < weak_combination_chance:
        return weak_combination  # weak
    elif roll < weak_combination_chance + lower_legendary_combination_chance:
        return lower_legendary_combination  # lower legendary
    elif roll < weak_combination_chance + lower_legendary_combination_chance + upper_legendary_combination_chance:
        return upper_legendary_combination  # upper legendary
    else:
        return normal_points  # обычные очки