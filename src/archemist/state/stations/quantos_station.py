from src.archemist.state.station import SolidDispensingStation, Location


class quantosStation(SolidDispensingStation):
    def __init__(self, name: str, id: int, loc: Location):
        super().__init__(name, id, loc)