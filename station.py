from random import randint

class Station:
	

	def __init__(self, name, lambda_val, role, max_backoff):
		self.name = name
		self.lambda_val = lambda_val
		self.role = role
		self.max_backoff = max_backoff
		self.time_slots = self.create_time_slots()  # TODO: replace with poisson distribution
		self.backoff = -1 							# if not in backoff then will be -1
		self.difs_counter = -1 						# if not in DIFS will be -1
		self.sifs_counter = -1 						# if not in SIFS will be -1


	def __str__(self):
		ret_str = 'Station {}:\n\tRole: {}\n\tLambda: {}\n\tBackoff: {}\n\n'.format(self.name, self.role, self.lambda_val, self.backoff)
		return ret_str


	def set_collision_domain(self, collision_domain):
		self.collision_domain = collision_domain


	def create_time_slots(self):
		temp_sum = 0
		ret_list = []

		for i in range(0, 1):  				# Just creating to see if it is working 
			temp_sum += randint(1, 10)
			ret_list.append(temp_sum)

		return ret_list 


	def set_rand_backoff(self, backoff):
		self.backoff = randint(0, backoff)


def main():
	print 'In the main of station.py'


if __name__ == '__main__':
	main()