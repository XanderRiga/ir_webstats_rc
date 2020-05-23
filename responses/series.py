from .car import Car
from ..constants import series_short_name_mapping


class Series:
    def __init__(self, dict):
        self.seriesId = dict['seriesid']
        self.name = self.short_name(dict['seriesname'])
        self.categoryId = dict['catid']
        self.cars = list(map(lambda x: Car(x), dict['cars']))

    def car_name_list(self):
        return list(map(lambda x: x.name, self.cars))

    def short_name(self, name):
        if name not in series_short_name_mapping:
            return name

        return series_short_name_mapping[name]
