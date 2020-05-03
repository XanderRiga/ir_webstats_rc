class CareerStats:
    def __init__(self, dict):
        self.wins = dict['wins']
        self.winPercentage = round(dict['winPerc'], 2)
        self.poles = dict['poles']
        self.totalClubPoints = dict['totalclubpoints']
        self.avgStart = round(dict['avgStart'], 2)
        self.avgFinish = round(dict['avgFinish'], 2)
        self.top5Percentage = round(dict['top5Perc'], 2)
        self.totalLaps = dict['totalLaps']
        self.avgIncPerRace = round(dict['avgIncPerRace'], 2)
        self.avgPtsPerRace = round(dict['avgPtsPerRace'], 2)
        self.lapsLed = dict['lapsLed']
        self.top5 = dict['top5']
        self.lapsLedPercentage = round(dict['lapsLedPerc'], 2)
        self.category = dict['category']
        self.starts = dict['starts']
