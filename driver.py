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
	for t_station in stations:
		if t_station.backoff == 0:
			t_station.backoff = -1
			sendingList.append(t_station)
	if (len(sendingList) is 1):
		spectrum.status = 'busy'
		if vcs:
			sendingList[0].rts_counter = ACK_RTS_CTS_slots
		else:	
			sendingList[0].data_counter = data_slots	
		spectrum.sending_station = sendingList

	elif (len(sendingList) > 1):
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
				spectrum.sending_station[0].sifs_counter = SIFS_duration
				spectrum.sending_station = []
				spectrum.receiving_station = -1
				t_station.action_before_sifs = 'data'
			elif (spectrum.status is 'collision'):
				t_station.data_counter = -1
				t_station.action_before_sifs = 'data'
				print 'Sending station:'
				print spectrum.sending_station
				t_station.sifs_counter = SIFS_duration
				#for p_station in spectrum.sending_station:
				#	p_station.sifs_counter = SIFS_duration


# This function will check the sifs counter of all sending stations. It checks them to see if their
# sifs counter is equal to zero. If so, that means they have watched the channel for sifs duration
# and the channel was always free. It will then free up the medium to allow for another packet to be sent. 
def check_sifs_counters(stations, spectrum):
	for t_station in stations:
		if (t_station.sifs_counter == 0):
			t_station.sifs_counter = -1
			if t_station.action_before_sifs == 'rts':
				t_station.cts_counter = ACK_RTS_CTS_slots
			elif t_station.action_before_sifs == 'cts':
				t_station.data_counter = data_slots
			elif t_station.action_before_sifs == 'data':
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
				if (len(spectrum.sending_station[0].time_slots) > 0):
					spectrum.sending_station[0].time_slots = spectrum.sending_station[0].time_slots[1:]
				spectrum.status = 'free'
				spectrum.sending_station[0].status = 'free'
				#print 'Success on slot {} from station {}'.format(slot_num, spectrum.sending_station.name)	
				spectrum.sending_station[0].num_data_transmit += 12  # All packets are 1,500 B which is 12 Kb
				spectrum.sending_station = []
				spectrum.receiving_station = -1	
				spectrum.status = 'free'
			elif (spectrum.status is 'collision'):
				#for p_station in spectrum.sending_station:
				t_station.num_collisions += 1 # every sending station has been apart of a collision, so increment by one
				print 'Setting {} to free'.format(t_station.name)
				t_station.status = 'free'
				if (t_station.max_backoff < max_backoff_range):
					t_station.max_backoff *= 2
				print 'Collision in ack on slot'
				if (len(spectrum.sending_station) > 0 and spectrum.sending_station[0].status == 'free'):
					print '||||'
					print spectrum.sending_station[0].name
					print '||||'
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
				spectrum.sending_station[0].sifs_counter = SIFS_duration
				spectrum.sending_station = []
				spectrum.receiving_station = -1
				t_station.action_before_sifs = 'cts'
			elif (spectrum.status is 'collision'):
				t_station.cts_counter = -1
				t_station.action_before_sifs = ''
				for p_station in spectrum.sending_station:
					p_station.num_collisions += 1 # every sending station has been apart of a collision, so increment by one
					p_station.status = 'free'
					if (p_station.max_backoff < max_backoff_range):
						p_station.max_backoff *= 2
				print 'Collision in CTS'
				spectrum.sending_station = []
				spectrum.receiving_station = -1	
				spectrum.status = 'free'


def check_RTS_counter(spectrum, sending_stations):
	for t_station in sending_stations:
		if t_station.rts_counter == 0:
			if (spectrum.status is 'busy'):
				t_station.rts_counter = -1
				spectrum.sending_station[0].sifs_counter = SIFS_duration
				spectrum.sending_station = []
				spectrum.receiving_station = -1
				t_station.action_before_sifs = 'rts'
			elif (spectrum.status is 'collision'):
				t_station.rts_counter = -1
				t_station.action_before_sifs = 'rts'
				for p_station in spectrum.sending_station:
					p_station.sifs_counter = SIFS_duration


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
		if t_station.backoff == 0 or t_station.data_counter > 0:
			sendingList.append(t_station)
	if (len(sendingList) > 1):
		s.spectrum.status = 'collision'

	if (s.spectrum.status != 'collision'):
		freeze_data(s)

	# for t_station in s.sending_stations:
	# 	if t_station.backoff == 0:
	# 		t_station.backoff = -1

	for t_station in s.sending_stations:
		if (t_station.wait_time > 0):
			t_station.wait_time -= 1
		elif (t_station.wait_time == 0):
			t_station.wait_time = -1

def freeze_data(scenario):
	for t_station in scenario.sending_stations:
		# Sending Stations (RTS)
		print 'Station {}'.format(t_station.name)
		if (t_station.backoff == 0 and scenario.vcs):
			for p_station in t_station.collision_domain:
				print 'Freeze 1'
				p_station.wait_time = ACK_RTS_CTS_slots + SIFS_duration + ACK_RTS_CTS_slots + SIFS_duration + data_slots + SIFS_duration + ACK_RTS_CTS_slots
		print 'Backoff {} and scenario {}'.format(t_station.backoff, scenario.vcs)
		if (t_station.backoff == 0 and (not scenario.vcs)):
			for p_station in t_station.collision_domain:
				print 'Freeze 2 {}'.format(p_station.name)
				p_station.wait_time = data_slots + SIFS_duration + ACK_RTS_CTS_slots + 1
		
		# Receiving Stations (CTS)
		if (t_station.sifs_counter == 0 and t_station.action_before_sifs != 'rts' and scenario.vcs):
			for p_station in t_station.station_sending_to.collision_domain:
				if (p_station != t_station):
					print 'Freeze 3'
					p_station.wait_time = SIFS_duration + data_slots + SIFS_duration + ACK_RTS_CTS_slots


def main():

	sim_data = []

	for scenario_choice in ['b']: 					# TODO: incorporate scenario B and place that in the loop
		for vcs in [True]:					# TODO: incorporate both VCS on and off and place in loop
			for lambda_a, lambda_c in [[10, 10]]:	# TODO: incorporate all lambda values
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
					scenario = Scenario([station_a, station_b, station_c, station_d], spectrum, vcs)
				
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
					scenario = Scenario([station_a, station_b, station_c], spectrum, vcs)


				for slot_num in range(0, 3000):
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
					try:
						print 'On slot {}'.format(slot_num)
						print 'A next time slot: {}'.format(station_a.time_slots[0])
						print 'A difs counter: {}'.format(station_a.difs_counter)
						print 'A backoff counter: {}'.format(station_a.backoff)
						print 'A data counter: {}'.format(station_a.data_counter)
						print 'A sifs counter: {}'.format(station_a.sifs_counter)
						print 'A ack counter: {}'.format(station_a.ack_counter)
						print 'A rts counter: {}'.format(station_a.rts_counter)
						print 'A cts counter: {}'.format(station_a.cts_counter)
						print 'A wait times: {}'.format(station_a.wait_time)

						print 'C next time slot: {}'.format(station_c.time_slots[0])
						print 'C difs counter: {}'.format(station_c.difs_counter)
						print 'C backoff counter: {}'.format(station_c.backoff)
						print 'C data counter: {}'.format(station_c.data_counter)
						print 'C sifs counter: {}'.format(station_c.sifs_counter)
						print 'C ack counter: {}'.format(station_c.ack_counter)
						print 'C rts counter: {}'.format(station_c.rts_counter)
						print 'C cts counter: {}'.format(station_c.cts_counter)
						print 'C wait times: {}'.format(station_c.wait_time)

						print 'Spectrum status: {}\n'.format(spectrum.status)
					except IndexError, e:
						print 'No more data to send. Breaking'
						break

				single_sim_data = {	# using hash table to record all of the information of a single simulation
					'lambda_a': lambda_a,
					'lambda_c': lambda_c,
					'a_collisions': station_a.num_collisions,
					'c_collisions': station_c.num_collisions,
					'a_throughput': station_a.num_data_transmit / simulation_time,
					'c_throughput': station_c.num_data_transmit / simulation_time,
					'a_slots_transmitting': station_a.slots_transmitting,
					'c_slots_transmitting': station_c.slots_transmitting,
					'FI': station_a.slots_transmitting / float(station_c.slots_transmitting),
					'vcs': vcs,
					'scenario': scenario_choice
				}
				sim_data.append(single_sim_data)

	for sim in sim_data:
		print sim

	print '\nDONE\n'

''' 	plt.figure(0)
	x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs']]
	y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs']]
	vcs_y_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs']]
	plt.plot(x_vals, y_vals, '-bo', linewidth=2.0, markersize=10, label='CSMA')
	plt.plot(x_vals, vcs_y_vals, '-rs', linewidth=2.0, markersize=10, label='CSMA w. Virtual Sensing')
	plt.legend()
	plt.xlim((45, 305))
	plt.ylabel(r'$T$ (Kbps)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title(r'1.a Node A: Throughput $T$ (Kbps) vs Rate $\lambda$ (frames/sec)')
	#plt.savefig('fig1-a.png')

	plt.figure(1)
	x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs']]
	y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs']]
	vcs_y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs']]
	plt.plot(x_vals, y_vals, '-bo', linewidth=2.0, markersize=10, label='CSMA')
	plt.plot(x_vals, vcs_y_vals, '-rs', linewidth=2.0, markersize=10, label='CSMA w. Virtual Sensing')
	plt.legend()
	plt.xlim((45, 305))	
	plt.ylabel(r'$T$ (Kbps)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title(r'1.b Node C: Throughput $T$ (Kbps) vs Rate $\lambda$ (frames/sec)')
	#plt.savefig('fig1-b.png')

	plt.figure(2)
	x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs']]
	y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs']]
	vcs_y_vals = [ sim['a_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs']]
	plt.plot(x_vals, y_vals, '-bo', linewidth=2.0, markersize=10, label='CSMA')
	plt.plot(x_vals, vcs_y_vals, '-rs', linewidth=2.0, markersize=10, label='CSMA w. Virtual Sensing')
	plt.legend()
	plt.xlim((45, 305))
	plt.ylabel(r'$T$ (Kbps)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title(r'1.c Node A: Throughput $T$ (Kbps) vs Rate $\lambda$ (frames/sec) when $\lambda$A = 2$\lambda$C')
	#plt.savefig('fig1-c.png')

	plt.figure(3)
	x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs']]
	y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs']]
	vcs_y_vals = [ sim['c_throughput'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs']]
	plt.plot(x_vals, y_vals, '-bo', linewidth=2.0, markersize=10, label='CSMA')
	plt.plot(x_vals, vcs_y_vals, '-rs', linewidth=2.0, markersize=10, label='CSMA w. Virtual Sensing')
	plt.legend()
	plt.xlim((45, 305))
	plt.ylabel(r'$T$ (Kbps)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title(r'1.d Node C: Throughput $T$ (Kbps) vs Rate $\lambda$ (frames/sec) when $\lambda$A = 2$\lambda$C')
	#plt.savefig('fig1-d.png')	

	plt.figure(4)
	x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_c'] == sim['lambda_a'] and sim['vcs']]
	y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs']]
	vcs_y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs']]
	plt.plot(x_vals, y_vals, '-bo', linewidth=2.0, markersize=10, label='CSMA')
	plt.plot(x_vals, vcs_y_vals, '-rs', linewidth=2.0, markersize=10, label='CSMA w. Virtual Sensing')	
	plt.legend()
	plt.xlim((45, 305))
	plt.ylabel(r'$N$ (Number of Collisions)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title(r'2.a Node A: Number of Collisions $N$ vs Rate $\lambda$ (frames/sec)')
	#plt.savefig('fig2-a.png')

	plt.figure(5)
	x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs']]
	y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs']]
	vcs_y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs']]
	plt.plot(x_vals, y_vals, '-bo', linewidth=2.0, markersize=10, label='CSMA')
	plt.plot(x_vals, vcs_y_vals, '-rs', linewidth=2.0, markersize=10, label='CSMA w. Virtual Sensing')
	plt.legend()
	plt.xlim((45, 305))
	plt.ylabel(r'$N$ (Number of collisions)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title(r'2.b Node C: Number of Collisions $N$ vs Rate $\lambda$ (frames/sec)')
	#plt.savefig('fig2-b.png')

	plt.figure(6)
	x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs']]
	y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs']]
	vcs_y_vals = [ sim['a_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs']]
	plt.plot(x_vals, y_vals, '-bo', linewidth=2.0, markersize=10, label='CSMA')
	plt.plot(x_vals, vcs_y_vals, '-rs', linewidth=2.0, markersize=10, label='CSMA w. Virtual Sensing')
	plt.legend()
	plt.xlim((45, 305))
	plt.ylabel(r'$T$ (Kbps)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title(r'2.c Node A: Number of Collisions $N$ vs Rate $\lambda$ (frames/sec) when $\lambda$A = 2$\lambda$C')
	#plt.savefig('fig1-d.png')

	plt.figure(7)
	x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs']]
	y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs']]
	vcs_y_vals = [ sim['c_collisions'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs']]
	plt.plot(x_vals, y_vals, '-bo', linewidth=2.0, markersize=10, label='CSMA')
	plt.plot(x_vals, vcs_y_vals, '-rs', linewidth=2.0, markersize=10, label='CSMA w. Virtual Sensing')
	plt.legend()
	plt.xlim((45, 305))
	plt.ylabel(r'$T$ (Kbps)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title(r'2.d Node C: Number of Collisions $N$ vs Rate $\lambda$ (frames/sec) when $\lambda$A = 2$\lambda$C')
	#plt.savefig('fig1-d.png')

	plt.figure(8)
	x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs']]
	y_vals = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and not sim['vcs']]
	vcs_y_vals = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == sim['lambda_c'] and sim['vcs']]
	plt.plot(x_vals, y_vals, '-bo', linewidth=2.0, markersize=10, label='CSMA')
	plt.plot(x_vals, vcs_y_vals, '-rs', linewidth=2.0, markersize=10, label='CSMA w. Virtual Sensing')
	plt.legend()
	plt.xlim((45, 305))
	plt.ylabel(r'$FI$ (Fairness Index)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title('3.a Fairness Index')
	#plt.savefig('fig3-a.png')

	plt.figure(9)
	x_vals = [ sim['lambda_c'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs']]
	y_vals = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and not sim['vcs']]
	vcs_y_vals = [ sim['FI'] for sim in sim_data if sim['lambda_a'] == ( 2 * sim['lambda_c']) and sim['vcs']]
	plt.plot(x_vals, y_vals, '-bo', linewidth=2.0, markersize=10, label='CSMA')
	plt.plot(x_vals, vcs_y_vals, '-rs', linewidth=2.0, markersize=10, label='CSMA w. Virtual Sensing')
	plt.legend()
	plt.xlim((45, 305))
	plt.ylabel(r'$T$ (Kbps)')
	plt.xlabel(r'$\lambda$ (frames/sec)')
	plt.title(r'3.b Fairness Index when $\lambda$A = 2$\lambda$C')
	# plt.savefig('fig1-d.png')
	plt.show() '''
	
if __name__ == '__main__':
	main()
