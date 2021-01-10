class Celsius:
    def __init__(self, _temp = 0):
        self._temp = _temp
    def to_far(self):
        return (self._temp * 1.8) + 32
if __name__ == '__main__':
    human = Celsius(40)
    print(human.to_far())
