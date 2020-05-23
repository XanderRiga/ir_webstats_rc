from .car import Car

name_mapping = {
    'iRacing Street Stock Series - R': 'Street Stock - Rookie',
    'DIRTcar Street Stock Series - Fixed': 'Dirt Street Stock - Fixed',
    'Rookie iRacing Rallycross Series': 'Rallycross - Rookie',
    'iRacing Advanced Legends Cup': 'Advanced Legends Cup'
}


class Series:
    def __init__(self, dict):
        self.seriesId = dict['seriesid']
        self.name = self.short_name(dict['seriesname'])
        self.categoryId = dict['catid']
        self.cars = list(map(lambda x: Car(x), dict['cars']))

    def car_name_list(self):
        return list(map(lambda x: x.name, self.cars))

    def short_name(self, name):
        if name not in name_mapping:
            return name

        return name_mapping[name]
