class Scenario:
	
	def __init__(self, stations, spectrum, vcs, scenario_choice):
		self.sending_stations = [station for station in stations if station.role.lower() == 'sender']
		self.receiving_stations = [station for station in stations if station.role.lower() == 'receiver']
		self.spectrum = spectrum
		self.vcs = vcs								# Boolean value showing if we use virtual carrier sensing or not
		self.scenario_choice = scenario_choice



	def __str__(self):
		ret_str = 'Station information: \n'
		for i in self.sending_stations + self.receiving_stations:
			ret_str += i.__str__()

		ret_str += '\nSpectrum information: \n'
		ret_str += self.spectrum.__str__()

		return ret_str




def main():
	print 'In the main of scenario.py'


if __name__ == '__main__':
	main()