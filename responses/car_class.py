from .car import Car


class CarClass:
    def __init__(self, dict):
        self.name = dict['name']
        self.cars = list(map(lambda x: Car(x), dict['carclasses']))
