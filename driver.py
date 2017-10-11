from scenario import Scenario
from station import Station
from packet import Packet
from spectrum import Spectrum
import matplotlib.pyplot as plt 

data_frame_size = 1500 																						# bytes
slot_duration = 20																							# micro seconds
SIFS_duration = 1 																							# slot
backoff_range = 4																							# slots
lambda_vals = [[50, 50], [100, 100], [200, 200], [300, 300], [100, 50], [200, 100], [400, 200], [600, 300]] # frames/sec
ACK_RTS_CTS_size = 30																						# bytes
DIFS_duration = 2																							# slots
transmission_rate = 6																						# Mbps
max_backoff_range = 1024																					# slots
simulation_time = 10 																						# sec
total_slots = (simulation_time * (10**6)) / slot_duration													# slots
data_slots = data_frame_size * 8 / (transmission_rate) / slot_duration										# slots
ACK_RTS_CTS_slots = ACK_RTS_CTS_size * 8 / (transmission_rate) / slot_duration								# slots


# This function will prepare all of the stations that just recieved a packet from the
# application stack. It does this by setting the difs_counter equal to the difs_duration,
# which will force the node to check the channel for that many slots to see if it is busy.
def prepare_transmitting_stations(t_stations, slot):
	for t_station in t_stations:
		if (len(t_station.time_slots) > 0 and slot >= t_station.time_slots[0] and t_station.status is 'free'):
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
def check_backoff_counters(stations, spectrum, vcs):
	sendingList = []
	corrupt_data_ack_or_sifs = False
	station_sending = False
	for t_station in stations:
		if t_station.backoff == 0:
			t_station.backoff = -1
			station_sending = True
			sendingList.append(t_station)
	for t_station in stations:
		if (t_station.ack_counter != -1 or t_station.sifs_counter != -1) and station_sending and not vcs: # EDDIE CHANGED THIS
			corrupt_data_ack_or_sifs = True

	if (len(sendingList) is 1 and not corrupt_data_ack_or_sifs):
		spectrum.status = 'busy'
		# print 'SENDING LIST IS 1'
		if vcs:
			sendingList[0].rts_counter = ACK_RTS_CTS_slots
		else:	
			sendingList[0].data_counter = data_slots	
		spectrum.sending_station = sendingList

	elif (len(sendingList) > 1 or corrupt_data_ack_or_sifs):
		# print 'SENDING LIST IS MORE THAN ONE. corrupt_data_ack_or_sifs: {}'.format(corrupt_data_ack_or_sifs)
		spectrum.status = 'collision'
		if vcs:
			for p_station in sendingList:
				p_station.rts_counter = ACK_RTS_CTS_slots
		else:
			for p_station in sendingList:
				p_station.data_counter = data_slots
		spectrum.sending_station = sendingList


# This funciton will check if the spectrum is sending data. If it has finished sending the data then it
# it will call for the sifs counter to start going. 
def check_data_counters(spectrum, sending_stations):
	for t_station in sending_stations:
		if (t_station.data_counter == 0):
			if (spectrum.status is 'busy'):
				t_station.data_counter = -1
				#spectrum.sending_station[0].sifs_counter = SIFS_duration # EDDIE CHANGED THIS
				t_station.sifs_counter = SIFS_duration
				spectrum.sending_station = []
				spectrum.receiving_station = -1
				t_station.action_before_sifs = 'data'
			elif (spectrum.status is 'collision'):
				t_station.data_counter = -1
				t_station.action_before_sifs = 'data'
				t_station.sifs_counter = SIFS_duration
				#for p_station in spectrum.sending_station:
				#	p_station.sifs_counter = SIFS_duration


# This function will check the sifs counter of all sending stations. It checks them to see if their
# sifs counter is equal to zero. If so, that means they have watched the channel for sifs duration
# and the channel was always free. It will then free up the medium to allow for another packet to be sent. 
def check_sifs_counters(stations, spectrum):
	for t_station in stations:
		if (t_station.sifs_counter == 0):
			# print 'In check_sifs_counters with station {} action_before_sifs: {} with data_counter {}'.format(t_station.name, t_station.action_before_sifs, t_station.data_counter)
			t_station.sifs_counter = -1
			if t_station.action_before_sifs == 'rts' and t_station.data_counter == -1:
				t_station.cts_counter = ACK_RTS_CTS_slots
			elif t_station.action_before_sifs == 'cts' and t_station.data_counter == -1:
				t_station.data_counter = data_slots
			elif t_station.action_before_sifs == 'data' and t_station.data_counter == -1:
				t_station.ack_counter = ACK_RTS_CTS_slots

			if (spectrum.status is 'busy'):
				spectrum.set_sending_receiving_station(t_station, t_station.station_sending_to)


# This function checks if the ack counter in the spectrum is set to -1. If it is then it clears the 
# sending station, resets the counter to -1, and sets the status to free. 
def check_ack_counters(spectrum, sending_stations):
	spectrum_collision = False
	for t_station in sending_stations:
		if (t_station.ack_counter == 0):
			t_station.ack_counter = -1
			if (spectrum.status is 'busy'):
				#if (len(spectrum.sending_station[0].time_slots) > 0): # EDDIE CHANGED THIS
					#spectrum.sending_station[0].time_slots = spectrum.sending_station[0].time_slots[1:]
				if(len(t_station.time_slots) > 0):
					t_station.time_slots = t_station.time_slots[1:]
				spectrum.status = 'free'
				t_station.status = 'free'		# Eddie added this
				#spectrum.sending_station[0].status = 'free'
				#spectrum.sending_station[0].num_data_transmit += 12  # All packets are 1,500 B which is 12 Kb
				t_station.num_data_transmit += 12
				t_station.max_backoff = backoff_range
				# print 'Success on slot. Incrementing Station {} num_data_transmit to {}'.format(t_station.name, t_station.num_data_transmit)
				spectrum.sending_station = []
				spectrum.receiving_station = -1	
				spectrum.status = 'free'
			elif (spectrum.status is 'collision'):
				#for p_station in spectrum.sending_station:
				t_station.num_collisions += 1 # every sending station has been apart of a collision, so increment by one
				t_station.status = 'free'
				if (t_station.max_backoff < max_backoff_range):
					t_station.max_backoff *= 2
				# print 'Collision in ACK. Incrementing station {} num_collisions to {}'.format(t_station.name, t_station.num_collisions)
				if (len(spectrum.sending_station) > 0 and spectrum.sending_station[0].status == 'free'):
					spectrum_collision = True

				
	if spectrum_collision:
		spectrum.status = 'free'
		spectrum.sending_station = []
		spectrum.receiving_station = -1	


def check_CTS_counter(spectrum, sending_stations):	
	for t_station in sending_stations:
		if t_station.cts_counter == 0:
			if (spectrum.status is 'busy'):
				t_station.cts_counter = -1
				t_station.sifs_counter = SIFS_duration # EDDIE ADDED THIS
				#spectrum.sending_station[0].sifs_counter = SIFS_duration
				spectrum.sending_station = []
				spectrum.receiving_station = -1
				t_station.action_before_sifs = 'cts'
			elif (spectrum.status is 'collision'):
				t_station.action_before_sifs = ''
				#for p_station in spectrum.sending_station:
				t_station.cts_counter = -1 		# setting every station that was sending cts counter back to -1
				t_station.num_collisions += 1 	# every sending station has been apart of a collision, so increment by one
				t_station.status = 'free'
				if (t_station.max_backoff < max_backoff_range):
					t_station.max_backoff *= 2
				# print 'Collision in CTS. Incrementing station {} num_collisions to {}'.format(t_station.name, t_station.num_collisions)
				spectrum.sending_station.remove(t_station)
				spectrum.receiving_station = -1	
				if (len(spectrum.sending_station) == 0):
					spectrum.status = 'free'
					


def check_RTS_counter(spectrum, sending_stations):
	for t_station in sending_stations:
		if t_station.rts_counter == 0:
			if (spectrum.status is 'busy'):
				t_station.rts_counter = -1
				t_station.sifs_counter = SIFS_duration
				#spectrum.sending_station[0].sifs_counter = SIFS_duration
				spectrum.sending_station = []
				spectrum.receiving_station = -1
				t_station.action_before_sifs = 'rts'
			elif (spectrum.status is 'collision'):
				t_station.rts_counter = -1
				t_station.action_before_sifs = 'rts'
				t_station.sifs_counter = SIFS_duration
				#for p_station in spectrum.sending_station:
				#	p_station.sifs_counter = SIFS_duration


# This function will decrement all of the counters occuring in the simulation. This will include
# counters in every station, such as their internal difs, sifs, and backoff counter. It will also
# include the spectrum to count down how long it will be busy with a packet or ack.
def end_of_slot(s):


	for t_station in s.sending_stations:
		if (t_station.wait_time == -1):
			if t_station.difs_counter > 0:
				t_station.difs_counter -= 1
				# print '{} DIFS now: {}'.format(t_station.name, t_station.difs_counter)
			if t_station.backoff >= 0:
				t_station.backoff -= 1
				# print '{} Backoff now: {}'.format(t_station.name, t_station.backoff)
		
	for t_station in s.sending_stations:
		if (t_station.wait_time == -1):
			if t_station.status == 'busy':
				t_station.slots_transmitting += 1
				# print '{} {}'.format(t_station.name, t_station.slots_transmitting)
			if t_station.sifs_counter > 0:
				t_station.sifs_counter -= 1
			if t_station.data_counter > 0:
				t_station.data_counter -= 1
			if t_station.ack_counter > 0:
				t_station.ack_counter -= 1
			if t_station.rts_counter > 0:
				t_station.rts_counter -= 1
			if t_station.cts_counter > 0:
				t_station.cts_counter -= 1

	sendingList = []
	for t_station in s.sending_stations:
		if (t_station.backoff == 0 or t_station.data_counter >= 0 or t_station.rts_counter >= 0 or t_station.cts_counter >= 0 or t_station.ack_counter >= 0) and t_station.wait_time == -1:
			sendingList.append(t_station)
			if t_station not in s.spectrum.sending_station:
				s.spectrum.sending_station.append(t_station)


	if (len(sendingList) > 1):
		s.spectrum.status = 'collision'

	if (s.spectrum.status != 'collision'):
		freeze_data(s)

	for t_station in s.sending_stations:
		if (t_station.wait_time > 0):
			t_station.wait_time -= 1
		elif (t_station.wait_time == 0):
			t_station.wait_time = -1

def freeze_data(scenario):
	for t_station in scenario.sending_stations:
		# Sending Stations (RTS)
		# print 'Station {}'.format(t_station.name)
		if (t_station.backoff == 0 and scenario.vcs):
			for p_station in t_station.collision_domain:
				#print 'Freeze 1 {}'.format(p_station.name)
				p_station.wait_time = ACK_RTS_CTS_slots + SIFS_duration + ACK_RTS_CTS_slots + SIFS_duration + data_slots + SIFS_duration + ACK_RTS_CTS_slots + 1
		
		if (t_station.backoff == 0 and (not scenario.vcs)):
			for p_station in t_station.collision_domain:
				#print 'Freeze 2 {}'.format(p_station.name)
				p_station.wait_time = data_slots + SIFS_duration + ACK_RTS_CTS_slots + 1
		
		# Receiving Stations (CTS)
		if (t_station.sifs_counter == 0 and t_station.action_before_sifs == 'cts' and scenario.vcs and scenario.scenario_choice == 'b'):
			for p_station in t_station.station_sending_to.collision_domain:
				if (p_station != t_station):
					#print 'Freeze 3'
					p_station.wait_time = SIFS_duration + data_slots + SIFS_duration + ACK_RTS_CTS_slots


def main():

	
	for run_number in range(0, 10):
		print 'Run number {}'.format(run_number)
		sim_data = []
		for scenario_choice in ['a', 'b']: 
			for vcs in [True, False]:			
				for lambda_a, lambda_c in lambda_vals:
					print 'Starting with scenario {} for vcs {}. Lambda A = {} and Lambda C = {}.'.format(scenario_choice, vcs, lambda_a, lambda_c)
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
						scenario = Scenario([station_a, station_b, station_c, station_d], spectrum, vcs, scenario_choice)
					
					# Initializing scenario B
					if scenario_choice == 'b':
						station_a = Station('A', lambda_a, 'Sender', backoff_range, total_slots, slot_duration)
						station_b = Station('B', 0, 'Receiver', backoff_range, total_slots, slot_duration)
						station_c = Station('C', lambda_c, 'Sender', backoff_range, total_slots, slot_duration)
						station_a.set_station_communicating(station_b)
						station_b.set_station_communicating(station_a)
						station_c.set_station_communicating(station_b)
						station_a.set_collision_domain([station_b])
						station_b.set_collision_domain([station_a, station_c])
						station_c.set_collision_domain([station_b])
						spectrum = Spectrum()
						scenario = Scenario([station_a, station_b, station_c], spectrum, vcs, scenario_choice)


					for slot_num in range(0, total_slots):
						prepare_transmitting_stations(scenario.sending_stations, slot_num)					# Checking to see if a node is trying to send a packet at a given slot.
						check_difs_counters(scenario.sending_stations)										# Checking to see if the difs counter for any node is 0 to start the backoff.
						check_backoff_counters(scenario.sending_stations, scenario.spectrum, scenario.vcs)	# Checking to see if the backoff counter for any node is 0 so we can send a packet.
						if scenario.vcs:
							check_RTS_counter(scenario.spectrum, scenario.sending_stations)					# if we are using VCS, check the RTS counter
							check_CTS_counter(scenario.spectrum, scenario.sending_stations)					# if we are using VCS, check the CTS counter
						check_data_counters(scenario.spectrum, scenario.sending_stations)					# Checking to see if the data counter is done. 
						check_sifs_counters(scenario.sending_stations, scenario.spectrum)					# Checking to see if the sifs counter for any node is 0 to free the medium.
						check_ack_counters(scenario.spectrum, scenario.sending_stations)					# Checking to see if the awk counter is done.
						
						end_of_slot(scenario)																# Decreasing all counters in the scenario.

						# DEBUG information
						
						# try:
						# 	print 'On slot {}'.format(slot_num)
						# 	print 'A next time slot: {}'.format(station_a.time_slots[0])
						# 	print 'A difs counter: {}'.format(station_a.difs_counter)
						# 	print 'A backoff counter: {}'.format(station_a.backoff)
						# 	print 'A data counter: {}'.format(station_a.data_counter)
						# 	print 'A sifs counter: {}'.format(station_a.sifs_counter)
						# 	print 'A ack counter: {}'.format(station_a.ack_counter)
						# 	print 'A rts counter: {}'.format(station_a.rts_counter)
						# 	print 'A cts counter: {}'.format(station_a.cts_counter)
						# 	print 'A wait times: {}'.format(station_a.wait_time)

						# 	print 'C next time slot: {}'.format(station_c.time_slots[0])
						# 	print 'C difs counter: {}'.format(station_c.difs_counter)
						# 	print 'C backoff counter: {}'.format(station_c.backoff)
						# 	print 'C data counter: {}'.format(station_c.data_counter)
						# 	print 'C sifs counter: {}'.format(station_c.sifs_counter)
						# 	print 'C ack counter: {}'.format(station_c.ack_counter)
						# 	print 'C rts counter: {}'.format(station_c.rts_counter)
						# 	print 'C cts counter: {}'.format(station_c.cts_counter)
						# 	print 'C wait times: {}'.format(station_c.wait_time)
						# 	print 'Spectrum List:'
						# 	for a in spectrum.sending_station:
						# 		print a.name
						# 	print 'Spectrum status: {}\n'.format(spectrum.status)
						# except IndexError, e:
						# 	print 'No more data to send. Breaking'
						# 	break
						
					# print 'A {}\nC {}\nDIV: {}\n\n'.format(station_a.slots_transmitting, station_c.slots_transmitting, station_a.slots_transmitting / float(station_c.slots_transmitting))

					single_sim_data = {	# using hash table to record all of the information of a single simulation
						'lambda_a': lambda_a,
						'lambda_c': lambda_c,
						'a_collisions': station_a.num_collisions,
						'c_collisions': station_c.num_collisions,
						'a_throughput': station_a.num_data_transmit / float(simulation_time),
						'c_throughput': station_c.num_data_transmit / float(simulation_time),
						'a_slots_transmitting': station_a.slots_transmitting,
						'c_slots_transmitting': station_c.slots_transmitting,
						'FI': station_a.slots_transmitting / float(station_c.slots_transmitting),
						'vcs': vcs,
						'scenario': scenario_choice
					}
					sim_data.append(single_sim_data)
					# print single_sim_data

		for sim in sim_data:
			print sim

	 	plt.figure(0)
		plt.figure(figsize=(8,8))
		x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'a' ] 
		no_vcs_a_y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs'] and sim['scenario'] == 'a' ]
		vcs_a_y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'a' ]
		no_vcs_b_y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs'] and sim['scenario'] == 'b' ]
		vcs_b_y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'b' ]
		plt.plot(x_vals, no_vcs_a_y_vals, '-bo', linewidth=2.0, markersize=10, label='Scenario A CSMA')
		plt.plot(x_vals, vcs_a_y_vals, '-rs', linewidth=2.0, markersize=10, label='Scenario A CSMA w. Virtual Sensing')
		plt.plot(x_vals, no_vcs_b_y_vals, '-g+', linewidth=2.0, markersize=10, label='Scenario B CSMA')
		plt.plot(x_vals, vcs_b_y_vals, '-kx', linewidth=2.0, markersize=10, label='Scenario B CSMA w. Virtual Sensing')
		plt.legend(loc = 2, markerscale = 0.8, prop={'size': 8})
		plt.xlim((45, 305))
		plt.ylabel(r'$T$ (Kbps)')
		plt.xlabel(r'$\lambda$ (frames/sec)')
		plt.title(r'1.a Node A: Throughput $T$ (Kbps) vs Rate $\lambda$ (frames/sec)')
		plt.savefig('fig1-a' + str(run_number) + '.png')

		plt.figure(1)
		plt.figure(figsize=(8,8))
		x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'a' ]
		no_vcs_a_y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs'] and sim['scenario'] == 'a' ]
		vcs_a_y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'a' ]
		no_vcs_b_y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs'] and sim['scenario'] == 'b' ]
		vcs_b_y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'b' ]
		plt.plot(x_vals, no_vcs_a_y_vals, '-bo', linewidth=2.0, markersize=10, label='Scenario A CSMA')
		plt.plot(x_vals, vcs_a_y_vals, '-rs', linewidth=2.0, markersize=10, label='Scenario A CSMA w. Virtual Sensing')
		plt.plot(x_vals, no_vcs_b_y_vals, '-g+', linewidth=2.0, markersize=10, label='Scenario B CSMA')
		plt.plot(x_vals, vcs_b_y_vals, '-kx', linewidth=2.0, markersize=10, label='Scenario B CSMA w. Virtual Sensing')
		plt.legend(loc = 2, markerscale = 0.8, prop={'size': 8})
		plt.xlim((45, 305))	
		plt.ylabel(r'$T$ (Kbps)')
		plt.xlabel(r'$\lambda$ (frames/sec)')
		plt.title(r'1.b Node C: Throughput $T$ (Kbps) vs Rate $\lambda$ (frames/sec)')
		plt.savefig('fig1-b' + str(run_number) + '.png')

		plt.figure(2)
		plt.figure(figsize=(8,8))
		x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'a' ]
		no_vcs_a_y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs'] and sim['scenario'] == 'a' ]
		vcs_a_y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'a' ]
		no_vcs_b_y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs'] and sim['scenario'] == 'b' ]
		vcs_b_y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'b' ]
		plt.plot(x_vals, no_vcs_a_y_vals, '-bo', linewidth=2.0, markersize=10, label='Scenario A CSMA')
		plt.plot(x_vals, vcs_a_y_vals, '-rs', linewidth=2.0, markersize=10, label='Scenario A CSMA w. Virtual Sensing')
		plt.plot(x_vals, no_vcs_b_y_vals, '-g+', linewidth=2.0, markersize=10, label='Scenario B CSMA')
		plt.plot(x_vals, vcs_b_y_vals, '-kx', linewidth=2.0, markersize=10, label='Scenario B CSMA w. Virtual Sensing')
		plt.legend(loc = 2, markerscale = 0.8, prop={'size': 8})
		plt.xlim((45, 305))
		plt.ylabel(r'$T$ (Kbps)')
		plt.xlabel(r'$\lambda$ (frames/sec)')
		plt.title(r'1.c Node A: Throughput $T$ (Kbps) vs Rate $\lambda$ (frames/sec) when $\lambda$A = 2$\lambda$C')
		plt.savefig('fig1-c' + str(run_number) + '.png')

		plt.figure(3)
		plt.figure(figsize=(8,8))
		x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'a']
		no_vcs_a_y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs'] and sim['scenario'] == 'a' ]
		vcs_a_y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'a' ]
		no_vcs_b_y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs'] and sim['scenario'] == 'b' ]
		vcs_b_y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'b' ]
		plt.plot(x_vals, no_vcs_a_y_vals, '-bo', linewidth=2.0, markersize=10, label='Scenario A CSMA')
		plt.plot(x_vals, vcs_a_y_vals, '-rs', linewidth=2.0, markersize=10, label='Scenario A CSMA w. Virtual Sensing')
		plt.plot(x_vals, no_vcs_b_y_vals, '-g+', linewidth=2.0, markersize=10, label='Scenario B CSMA')
		plt.plot(x_vals, vcs_b_y_vals, '-kx', linewidth=2.0, markersize=10, label='Scenario B CSMA w. Virtual Sensing')
		plt.legend(loc = 2, markerscale = 0.8, prop={'size': 8})
		plt.xlim((45, 305))
		plt.ylabel(r'$T$ (Kbps)')
		plt.xlabel(r'$\lambda$ (frames/sec)')
		plt.title(r'1.d Node C: Throughput $T$ (Kbps) vs Rate $\lambda$ (frames/sec) when $\lambda$A = 2$\lambda$C')
		plt.savefig('fig1-d' + str(run_number) + '.png')	

		plt.figure(4)
		plt.figure(figsize=(8,8))
		x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_c'] == sim['lambda_a'] and sim['vcs'] and sim['scenario'] == 'a']
		no_vcs_a_y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs'] and sim['scenario'] == 'a' ]
		vcs_a_y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'a' ]
		no_vcs_b_y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs'] and sim['scenario'] == 'b' ]
		vcs_b_y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'b' ]
		plt.plot(x_vals, no_vcs_a_y_vals, '-bo', linewidth=2.0, markersize=10, label='Scenario A CSMA')
		plt.plot(x_vals, vcs_a_y_vals, '-rs', linewidth=2.0, markersize=10, label='Scenario A CSMA w. Virtual Sensing')
		plt.plot(x_vals, no_vcs_b_y_vals, '-g+', linewidth=2.0, markersize=10, label='Scenario B CSMA')
		plt.plot(x_vals, vcs_b_y_vals, '-kx', linewidth=2.0, markersize=10, label='Scenario B CSMA w. Virtual Sensing')	
		plt.legend(loc = 2, markerscale = 0.8, prop={'size': 8})
		plt.xlim((45, 305))
		plt.ylabel(r'$N$ (Number of Collisions)')
		plt.xlabel(r'$\lambda$ (frames/sec)')
		plt.title(r'2.a Node A: Number of Collisions $N$ vs Rate $\lambda$ (frames/sec)')
		plt.savefig('fig2-a' + str(run_number) + '.png')

		plt.figure(5)
		plt.figure(figsize=(8,8))
		x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'a']
		no_vcs_a_y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs'] and sim['scenario'] == 'a' ]
		vcs_a_y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'a' ]
		no_vcs_b_y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs'] and sim['scenario'] == 'b' ]
		vcs_b_y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'b' ]
		plt.plot(x_vals, no_vcs_a_y_vals, '-bo', linewidth=2.0, markersize=10, label='Scenario A CSMA')
		plt.plot(x_vals, vcs_a_y_vals, '-rs', linewidth=2.0, markersize=10, label='Scenario A CSMA w. Virtual Sensing')
		plt.plot(x_vals, no_vcs_b_y_vals, '-g+', linewidth=2.0, markersize=10, label='Scenario B CSMA')
		plt.plot(x_vals, vcs_b_y_vals, '-kx', linewidth=2.0, markersize=10, label='Scenario B CSMA w. Virtual Sensing')	
		plt.legend(loc = 2, markerscale = 0.8, prop={'size': 8})
		plt.xlim((45, 305))
		plt.ylabel(r'$N$ (Number of Collisions)')
		plt.xlabel(r'$\lambda$ (frames/sec)')
		plt.title(r'2.b Node C: Number of Collisions $N$ vs Rate $\lambda$ (frames/sec)')
		plt.savefig('fig2-b' + str(run_number) + '.png')

		plt.figure(6)
		plt.figure(figsize=(8,8))
		x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'a']
		no_vcs_a_y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs'] and sim['scenario'] == 'a' ]
		vcs_a_y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'a' ]
		no_vcs_b_y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs'] and sim['scenario'] == 'b' ]
		vcs_b_y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'b' ]
		plt.plot(x_vals, no_vcs_a_y_vals, '-bo', linewidth=2.0, markersize=10, label='Scenario A CSMA')
		plt.plot(x_vals, vcs_a_y_vals, '-rs', linewidth=2.0, markersize=10, label='Scenario A CSMA w. Virtual Sensing')
		plt.plot(x_vals, no_vcs_b_y_vals, '-g+', linewidth=2.0, markersize=10, label='Scenario B CSMA')
		plt.plot(x_vals, vcs_b_y_vals, '-kx', linewidth=2.0, markersize=10, label='Scenario B CSMA w. Virtual Sensing')
		plt.legend(loc = 2, markerscale = 0.8, prop={'size': 8})
		plt.xlim((45, 305))
		plt.ylabel(r'$T$ (Kbps)')
		plt.xlabel(r'$\lambda$ (frames/sec)')
		plt.title(r'2.c Node A: Number of Collisions $N$ vs Rate $\lambda$ (frames/sec) when $\lambda$A = 2$\lambda$C')
		plt.savefig('fig2-c' + str(run_number) + '.png')

		plt.figure(7)
		plt.figure(figsize=(8,8))
		x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'a']
		no_vcs_a_y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs'] and sim['scenario'] == 'a' ]
		vcs_a_y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'a' ]
		no_vcs_b_y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs'] and sim['scenario'] == 'b' ]
		vcs_b_y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'b' ]
		plt.plot(x_vals, no_vcs_a_y_vals, '-bo', linewidth=2.0, markersize=10, label='Scenario A CSMA')
		plt.plot(x_vals, vcs_a_y_vals, '-rs', linewidth=2.0, markersize=10, label='Scenario A CSMA w. Virtual Sensing')
		plt.plot(x_vals, no_vcs_b_y_vals, '-g+', linewidth=2.0, markersize=10, label='Scenario B CSMA')
		plt.plot(x_vals, vcs_b_y_vals, '-kx', linewidth=2.0, markersize=10, label='Scenario B CSMA w. Virtual Sensing')
		plt.legend(loc = 2, markerscale = 0.8, prop={'size': 8})
		plt.xlim((45, 305))
		plt.ylabel(r'$T$ (Kbps)')
		plt.xlabel(r'$\lambda$ (frames/sec)')
		plt.title(r'2.d Node C: Number of Collisions $N$ vs Rate $\lambda$ (frames/sec) when $\lambda$A = 2$\lambda$C')
		plt.savefig('fig2-d' + str(run_number) + '.png')
		
		plt.figure(8)
		plt.figure(figsize=(8,8))
		x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'a']
		y_vals_a = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs'] and sim['scenario'] == 'a']
		y_vals_b = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs'] and sim['scenario'] == 'b']
		vcs_y_vals_a = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'a']
		vcs_y_vals_b = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs'] and sim['scenario'] == 'b']
		plt.plot(x_vals, y_vals_a, '-bo', linewidth=2.0, markersize=10, label='Scenario A CSMA')
		plt.plot(x_vals, vcs_y_vals_a, '-rs', linewidth=2.0, markersize=10, label='Scenario A CSMA w. Virtual Sensing')
		plt.plot(x_vals, y_vals_b, '-g+', linewidth=2.0, markersize=10, label='Scenario B CSMA')
		plt.plot(x_vals, vcs_y_vals_b, '-kx', linewidth=2.0, markersize=10, label='Scenario B CSMA w. Virtual Sensing')
		plt.legend(loc = 2, markerscale = 0.8, prop={'size': 8})
		plt.xlim((45, 305))
		plt.ylabel(r'$FI$ (Fairness Index)')
		plt.xlabel(r'$\lambda$ (frames/sec)')
		plt.title('3.a Fairness Index')
		plt.savefig('fig3-a' + str(run_number) + '.png')

		plt.figure(9)
		plt.figure(figsize=(8,8))
		x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'a']
		y_vals_a = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs'] and sim['scenario'] == 'a']
		y_vals_b = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs'] and sim['scenario'] == 'b']
		vcs_y_vals_a = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'a']
		vcs_y_vals_b = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs'] and sim['scenario'] == 'b']
		plt.plot(x_vals, y_vals_a, '-bo', linewidth=2.0, markersize=10, label='Scenario A CSMA')
		plt.plot(x_vals, vcs_y_vals_a, '-rs', linewidth=2.0, markersize=10, label='Scenario A CSMA w. Virtual Sensing')
		plt.plot(x_vals, y_vals_b, '-g+', linewidth=2.0, markersize=10, label='Scenario B CSMA')
		plt.plot(x_vals, vcs_y_vals_b, '-kx', linewidth=2.0, markersize=10, label='Scenario B CSMA w. Virtual Sensing')
		plt.legend(loc = 2, markerscale = 0.8, prop={'size': 8})
		plt.xlim((45, 305))
		plt.ylabel(r'$T$ (Kbps)')
		plt.xlabel(r'$\lambda$ (frames/sec)')
		plt.title(r'3.b Fairness Index when $\lambda$A = 2$\lambda$C')
		plt.savefig('fig3-b' + str(run_number) + '.png')
		#plt.show()
		plt.close('all')
		print 'DONE\n'
if __name__ == '__main__':
	main()
