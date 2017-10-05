class Spectrum:
	
	def __init__(self):
		self.status = 'free'
		self.data = []
		self.data_counter = -1 			# If -1 that means there is no data
		self.rts_counter = -1			# If -1 that means no RTS
		self.cts_counter = -1			# If -1 that means no CTS
		self.ack_counter = -1			# If -1 that means there is no data
		self.action_before_sifs = ''	# So we know what state we are in before SIFS (could be data, RTS, or CTS)

	def __str__(self):
		ret_str = '\tStatus: {}\n\tData: {}\n'.format(self.status, self.data)
		return ret_str

	def set_sending_receiving_station(self, sending_station, receiving_station):
		self.sending_station = sending_station
		self.receiving_station = receiving_station
		
def main():
	print 'In the main of station.py'


if __name__ == '__main__':
	main()