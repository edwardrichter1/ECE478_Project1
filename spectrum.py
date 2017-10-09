class Spectrum:
	
	def __init__(self):
		self.status = 'free'
		self.sending_station = []
	def __str__(self):
		ret_str = '\tStatus: {}\n\tData: {}\n'.format(self.status, self.data)
		return ret_str

	def set_sending_receiving_station(self, sending_station, receiving_station):
		self.sending_station.append(sending_station)
		self.receiving_station = receiving_station
		
def main():
	print 'In the main of station.py'


if __name__ == '__main__':
	main()