class Spectrum:
	
	def __init__(self):
		self.status = 'free'
		self.data = []
		self.data_counter = -1 	# if -1 that means there is no data
		self.ack_counter = -1	# if -1 that means there is no data

	def __str__(self):
		ret_str = '\tStatus: {}\n\tData: {}\n'.format(self.status, self.data)
		return ret_str


def main():
	print 'In the main of station.py'


if __name__ == '__main__':
	main()