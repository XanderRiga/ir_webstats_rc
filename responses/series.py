from .car import Car


class Series:
    def __init__(self, dict):
        self.seriesId = dict['seriesid']
        self.name = dict['seriesname']
        self.categoryId = dict['catid']
        self.cars = list(map(lambda x: Car(x), dict['cars']))

    def car_name_list(self):
        return list(map(lambda x: x.name, self.cars))
