class Scenario:
	
	def __init__(self, stations, spectrum):
		self.stations = stations
		self.spectrum = spectrum


	def __str__(self):
		ret_str = 'Station information: \n'.format(len(self.stations))
		for i in self.stations:
			ret_str += i.__str__()

		ret_str += '\nSpectrum information: \n'
		ret_str += self.spectrum.__str__()

		return ret_str


def main():
	print 'In the main of scenario.py'


if __name__ == '__main__':
	main()