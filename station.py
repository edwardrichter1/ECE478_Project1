from random import randint
import random
import math
import numpy as np

class Station:
	

	def __init__(self, name, lambda_val, role, max_backoff, total_slots, slot_duration):
		self.name = name
		self.status = 'free'
		self.lambda_val = lambda_val
		self.role = role
		self.max_backoff = max_backoff
		self.time_slots = self.create_time_slots(total_slots, slot_duration, lambda_val, role)
		self.backoff = -1 							# If not in backoff then will be -1
		self.difs_counter = -1 						# If not in DIFS will be -1
		self.sifs_counter = -1 						# If not in SIFS will be -1
		self.num_data_transmit = 0					# amount of data in Kb successfully transmitted
		self.num_collisions = 0						# number of collisions
		self.slots_transmitting = 0					# number of slots the station is using the medium

	def __str__(self):
		ret_str = 'Station {}:\n\tRole: {}\n\tLambda: {}\n\tBackoff: {}\n\n'.format(self.name, self.role, self.lambda_val, self.backoff)
		return ret_str


	def set_collision_domain(self, collision_domain):
		self.collision_domain = collision_domain

	def set_station_communicating(self, station_sending_to):
		self.station_sending_to = station_sending_to

	def create_time_slots(self, total_slots, slot_duration, lambda_val, role):
		temp_sum = 0
		ret_list = []
		if (role is not 'Sender'):
			return []

		max_time = 0
		timeList = []
		while (max_time < total_slots):
			x1 = -1.0 / lambda_val * math.log(1 - random.uniform(0, 1)) 	# Using the formula given in the appendix
			x1 = x1 / (slot_duration * 10**-6) 								# Converting from time to slot
			if (len(timeList) == 0):
				max_time = round(x1)
			else:
				max_time = round(x1) + timeList[-1]
			timeList.append(max_time)
		if (len(timeList) > 0 and timeList[-1] > total_slots):
			del timeList[-1] 												# Last element is too big

		return timeList 


	def set_rand_backoff(self):
		self.backoff = randint(0, self.max_backoff)


def main():
	print 'In the main of station.py'


if __name__ == '__main__':
	main()