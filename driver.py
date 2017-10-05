from scenario import Scenario
from station import Station
from packet import Packet
from spectrum import Spectrum
import matplotlib.pyplot as plt 

data_frame_size = 1500 																						# bytes
slot_duration = 20																							# micro seconds
SIFS_duration = 1 																							# slot
backoff_range = 4																							# slots
lambda_vals = [[50, 50], [100, 100], [200, 200], [300, 300], [50, 100], [100, 200], [200, 400], [300, 600]] # frames/sec
ACK_RTS_CTS_size = 30																						# bytes
DIFS_duration = 2																							# slots
transmission_rate = 6																						# Mbps
max_backoff_range = 1024																					# slots
simulation_time = 10 																						# sec
total_slots = (simulation_time * (10**6)) / slot_duration													# slots
data_slots = data_frame_size * 8 / (transmission_rate) / slot_duration										# slots
ACK_RTS_CTS_slots = ACK_RTS_CTS_size * 8 / (transmission_rate) / slot_duration								# slots
scenario_choice = 'a'																						# choosing which scenario to create
constant_a_lambda = 300																						# value to keep lambda_a in graphs
constant_c_lambda = 300																						# value to keep lambda_c in graphs


# This function will prepare all of the stations that just recieved a packet from the
# application stack. It does this by setting the difs_counter equal to the difs_duration,
# which will force the node to check the channel for that many slots to see if it is busy.
def prepare_transmitting_stations(t_stations, slot):
	for t_station in t_stations:
		# TODO if the slot value has gone over a value while transmiting something from another sender
		# then it will skip that slot since they will not be the same.
		if (len(t_station.time_slots) > 0 and slot >= t_station.time_slots[0] and t_station.status is 'free'):
			# print 'Station {} is ready to transmit on slot {}'.format(t_station.name, slot)
			t_station.difs_counter = DIFS_duration
			t_station.status = 'busy'


# This function will check the difs counter of all sending stations. It checks them to see if their
# difs counter is equal to zero. If so, that means they have watched the channel for difs duration
# and the channel was always free. It will then initialize the backoff value for when it will send
# the packet.
def check_difs_counters(stations):
	for t_station in stations:
		if t_station.difs_counter == 0:
			t_station.difs_counter = -1
			t_station.set_rand_backoff()
			# print 'Station {} difs counter is up, setting backoff of {}'.format(t_station.name, t_station.backoff)


# This function is similar to "check_difs_counters", but instead it checks to see if the backoff counter
# is complete. If so, the station will send the packet. This should create a packet object which will
# put the channel in a busy state.
def check_backoff_counters(stations, spectrum):
	sendingList = []
	for t_station in stations:
		if t_station.backoff == 0:
			t_station.backoff = -1
			sendingList.append(t_station)
	if (len(sendingList) is 1):
		spectrum.status = 'busy'
		spectrum.data_counter = data_slots
		spectrum.sending_station = sendingList[0]
	elif (len(sendingList) > 1):
		spectrum.status = 'collision'
		spectrum.data_counter = data_slots
		spectrum.sending_station = sendingList


# This funciton will check if the spectrum is sending data. If it has finished sending the data then it
# it will call for the sifs counter to start going. 
def check_data_counters(spectrum):
	if (spectrum.data_counter == 0):
		if (spectrum.status is 'busy'):
			spectrum.data_counter = -1
			spectrum.sending_station.sifs_counter = SIFS_duration
			spectrum.sending_station = -1
			spectrum.receiving_station = -1
		elif (spectrum.status is 'collision'):
			spectrum.data_counter = -1
			for t_station in spectrum.sending_station:
				t_station.sifs_counter = SIFS_duration


# This function will check the sifs counter of all sending stations. It checks them to see if their
# sifs counter is equal to zero. If so, that means they have watched the channel for sdifs duration
# and the channel was always free. It will then free up the medium to allow for another packet to be sent. 
def check_sifs_counters(stations, spectrum):
	for t_station in stations:
		if (t_station.sifs_counter == 0):
			t_station.sifs_counter = -1
			spectrum.ack_counter = ACK_RTS_CTS_slots
			if (spectrum.status is 'busy'):
				spectrum.set_sending_receiving_station(t_station, t_station.station_sending_to)


# This function checks if the ack counter in the spectrum is set to -1. If it is then it clears the 
# sending station, resets the counter to -1, and sets the status to free. 
def check_ack_counters(spectrum, slot_num):
	if (spectrum.ack_counter == 0):
		spectrum.ack_counter = -1
		if (spectrum.status is 'busy'):
			if (len(spectrum.sending_station.time_slots) > 0):
				spectrum.sending_station.time_slots = spectrum.sending_station.time_slots[1:]
			spectrum.status = 'free'
			spectrum.sending_station.status = 'free'
			# print 'Succesful transmission {}\n'.format(spectrum.sending_station.name)
			# print 'Success on slot {} from station {}'.format(slot_num, spectrum.sending_station.name)	
			spectrum.sending_station.num_data_transmit += 12  # All packets are 1,500 B which is 12 Kb
			spectrum.sending_station = -1
			spectrum.receiving_station = -1	
			spectrum.status = 'free'
		elif (spectrum.status is 'collision'):
			for t_station in spectrum.sending_station:
				t_station.num_collisions += 1 # every sending station has been apart of a collision, so increment by one
				t_station.status = 'free'
				if (t_station.max_backoff < max_backoff_range):
					t_station.max_backoff *= 2
			print 'Collision on slot {}'.format(slot_num)
			spectrum.sending_station = -1
			spectrum.receiving_station = -1	
			spectrum.status = 'free'


# This function will decrement all of the counters occuring in the simulation. This will include
# counters in every station, such as their internal difs, sifs, and backoff counter. It will also
# include the spectrum to count down how long it will be busy with a packet or ack.
def end_of_slot(s):
	if s.spectrum.status.lower() != 'busy':
		for t_station in s.sending_stations:
			if t_station.difs_counter > 0:
				t_station.difs_counter -= 1
				# print '{} DIFS now: {}'.format(t_station.name, t_station.difs_counter)
			if t_station.backoff > 0:
				t_station.backoff -= 1
				# print '{} Backoff now: {}'.format(t_station.name, t_station.backoff)
			
		# TODO: Push back elements in time_slots if it is already processing one packet
	for t_station in s.sending_stations:
		if t_station.status == 'busy':
			t_station.slots_transmitting += 1
		if t_station.sifs_counter > 0:
			t_station.sifs_counter -= 1
			# print '{} SIFS now: {}'.format(t_station.name, t_station.sifs_counter)
	if s.spectrum.data_counter > 0:
		s.spectrum.data_counter -= 1
		# print 'Decreasing Data Counter: {}'.format(s.spectrum.data_counter)
	if s.spectrum.ack_counter > 0:
		s.spectrum.ack_counter -= 1
		# print 'Decreasing ACK Counter: {}'.format(s.spectrum.ack_counter)		


def main():

	sim_data = []
	for lambda_a, lambda_c in lambda_vals:
		
		# Initializing scenario A
		if scenario_choice == 'a':
			station_a = Station('A', lambda_a, 'Sender', backoff_range, total_slots, slot_duration)
			station_b = Station('B', 0, 'Receiver', backoff_range, total_slots, slot_duration)
			station_c = Station('C', lambda_c, 'Sender', backoff_range, total_slots, slot_duration)
			station_d = Station('D', 0, 'Receiver', backoff_range, total_slots, slot_duration) 
			station_a.set_station_communicating(station_b)
			station_b.set_station_communicating(station_a)
			station_c.set_station_communicating(station_d)
			station_d.set_station_communicating(station_c)
			station_a.set_collision_domain([station_b, station_c, station_d])
			station_b.set_collision_domain([station_a, station_c, station_d])
			station_c.set_collision_domain([station_a, station_b, station_d])
			station_d.set_collision_domain([station_a, station_b, station_c])
			spectrum = Spectrum()
			scenario = Scenario([station_a, station_b, station_c, station_d], spectrum)
		
		for slot_num in range(0, total_slots):
			scenario.spectrum.prev_status = scenario.spectrum.status
			prepare_transmitting_stations(scenario.sending_stations, slot_num)		# Checking to see if a node is trying to send a packet at a given slot.
			check_difs_counters(scenario.sending_stations)							# Checking to see if the difs counter for any node is 0 to start the backoff.
			check_backoff_counters(scenario.sending_stations, scenario.spectrum)	# Checking to see if the backoff counter for any node is 0 so we can send a packet.
			check_data_counters(scenario.spectrum)									# Checking to see if the data counter is done. 
			check_sifs_counters(scenario.sending_stations, scenario.spectrum)		# Checking to see if the sifs counter for any node is 0 to free the medium.
			check_ack_counters(scenario.spectrum, slot_num)							# Checking to see if the awk counter is done.
			
			end_of_slot(scenario)													# Decreasing all counters in the scenario.

			# DEBUG information
			#try:
			#	print 'On slot {}'.format(slot_num)
			#	print 'A next time slot: {}'.format(station_a.time_slots[0])
			#	print 'A difs counter: {}'.format(station_a.difs_counter)
			#	print 'A backoff counter: {}'.format(station_a.backoff)
			#	print 'A sifs counter: {}'.format(station_a.sifs_counter)
				
			#	print 'C next time slot: {}'.format(station_c.time_slots[0])
			#	print 'C difs counter: {}'.format(station_c.difs_counter)
			#	print 'C backoff counter: {}'.format(station_c.backoff)
			#	print 'C sifs counter: {}'.format(station_c.sifs_counter)

			#	print 'Spectrum status: {}'.format(spectrum.status)
			#	print 'Spectrum Data Counter: {}'.format(spectrum.data_counter)
			#	print 'Spectrum Ack Counter: {}\n'.format(spectrum.ack_counter)
			#except IndexError, e:
			#	print 'No more data to send. Breaking'
			#	break
		print 'Name {}\t{}\nName {}\t{}'.format(station_a.name, station_a.slots_transmitting, station_c.name, station_c.slots_transmitting)
		single_sim_data = {	# using hash table to record all of the information of a single simulation
			'lambda_a': lambda_a,
			'lambda_c': lambda_c,
			'a_collisions': station_a.num_collisions,
			'c_collisions': station_c.num_collisions,
			'a_throughput': station_a.num_data_transmit / simulation_time,
			'c_throughput': station_c.num_data_transmit / simulation_time,
			'a_slots_transmitting': station_a.slots_transmitting,
			'c_slots_transmitting': station_c.slots_transmitting,
			'FI': station_a.slots_transmitting / station_c.slots_transmitting
		}
		sim_data.append(single_sim_data)

	for sim in sim_data:
		print sim

	plt.figure(0)
	plt.plot([ sim['lambda_a'] for sim in sim_data if sim['lambda_c'] == sim['lambda_a'] ], [ sim['a_throughput'] for sim in sim_data if sim['lambda_c'] == sim['lambda_a']], linewidth=2.0, markersize=10)
	plt.ylabel(r'$T$ (Kbps)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title('1.a Node A: Throughput vs rate')
	#plt.savefig('fig1-a.png')

	plt.figure(1)
	plt.plot([ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] ], [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c']], linewidth=2.0, markersize=10)
	plt.ylabel(r'$T$ (Kbps)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title('1.b Node C: Throughput vs rate')
	#plt.savefig('fig1-b.png')

	plt.figure(2)
	plt.plot([ sim['lambda_a'] for sim in sim_data if sim['lambda_c'] == sim['lambda_a'] ], [ sim['a_collisions'] for sim in sim_data if sim['lambda_c'] == sim['lambda_a']], linewidth=2.0, markersize=10)
	plt.ylabel(r'$N$ (Number of collisions)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title('2.a Node A: Number of Collisions vs Rate')
	#plt.savefig('fig2-a.png')

	plt.figure(3)
	plt.plot([ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] ], [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c']], linewidth=2.0, markersize=10)
	plt.ylabel(r'$N$ (Number of collisions)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title('2.b Node C: Number of Collisions vs Rate')
	#plt.savefig('fig2-b.png')

	plt.figure(4)
	plt.plot([ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] ], [ sim['FI'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c']], linewidth=2.0, markersize=10)
	plt.ylabel(r'$FI$ (Fairness Index)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title('3.a Fairness Index')
	#plt.savefig('fig3-a.png')
	plt.show()

if __name__ == '__main__':
	main()
