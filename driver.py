from scenario import Scenario
from station import Station
from packet import Packet
from spectrum import Spectrum


data_frame_size = 1500 										# bytes
slot_duration = 20											# micro seconds
SIFS_duration = 10 											# micro seconds
backoff_range = 4											# slots
lambda_a = 50												# frames/sec
lambda_c = 50												# frames/sec
ACK_RTS_CTS_size = 30										# bytes
DIFS_duration = 2											# slots
transmission_rate = 6										# Mbps
max_backoff_range = 1024									# slots
simulation_time = 10 										# sec
total_slots = (simulation_time * (10**6)) / slot_duration	# slots
scenario_choice = 'a'										# choosing which scenario to create


# This function will prepare all of the stations that just recieved a packet from the
# application stack. It does this by setting the difs_counter equal to the difs_duration,
# which will force the node to check the channel for that many slots to see if it is busy.
def prepare_transmitting_stations(t_stations, slot):
	for t_station in t_stations:
		if slot in t_station.time_slots:
			print 'Station {} is ready to transmit on slot {}'.format(t_station.name, slot)
			t_station.difs_counter = DIFS_duration


# This function will check the difs counter of all sending stations. It checks them to see if their
# diff counter is equal to zero. If so, that means they have watched the channel for difs duration
# and the channel was always free. It will then initialize the backoff value for when it will send
# the packet.
def check_difs_counters(stations):
	for t_station in stations:
		if t_station.difs_counter == 0:
			t_station.difs_counter = -1
			t_station.set_rand_backoff(backoff_range)
			print 'Station {} difs counter is up, setting backoff of {}'.format(t_station.name, t_station.backoff)


# This function is similar to "check_difs_counters", but instead it checks to see if the backoff counter
# is complete. If so, the station will send the packet. This should create a packet object which will
# put the channel in a busy state.
def check_backoff_counters(stations):
	for t_station in stations:
		if t_station.backoff == 0:
			t_station.backoff = -1
			print 'Station {} is sending a packet'.format(t_station.name)
			# TODO: CREATE PACKET AND PUT ON THE SPECTRUM

# This function will decrement all of the counters occuring in the simulation. This will include
# counters in every station, such as their internal difs, sifs, and backoff counter. It will also
# include the  spectrum to count down how long it will be busy with a packet or ack.
def end_of_slot(s):
	if s.spectrum.status.lower() != 'busy':
		for t_station in s.sending_stations:
			if t_station.difs_counter > 0:
				t_station.difs_counter -= 1
			if t_station.sifs_counter > 0:
				t_station.sifs_counter -= 1
			if t_station.backoff > 0:
				t_station.backoff -= 1
		# TODO: Push back elements in time_slots if it is already processing one packet

	if s.spectrum.data_counter > 0:
		s.spectrum.data_counter -= 1

	if s.spectrum.ack_counter > 0:
		s.spectrum.ack_counter -= 1


def main():

	# Initializing scenario A
	# TODO: Establish the sender-receiver relationship between A -> B and C -> D.
	if scenario_choice == 'a':
		station_a = Station('A', lambda_a, 'Sender', max_backoff_range)
		station_b = Station('B', 0, 'Receiver', max_backoff_range)
		station_c = Station('C', lambda_c, 'Sender', max_backoff_range)
		station_d = Station('D', 0, 'Receiver', 0)
		station_a.set_collision_domain([station_b, station_c, station_d])
		station_b.set_collision_domain([station_a, station_c, station_d])
		station_c.set_collision_domain([station_a, station_b, station_d])
		station_d.set_collision_domain([station_a, station_b, station_c])
		spectrum = Spectrum()
		scenario = Scenario([station_a, station_b, station_c, station_d], spectrum)

	print scenario

	print '**** STARTING SIMULATION ****\n'
	for slot_num in range(0, total_slots):
		
		# DEBUG information
		if slot_num < 25:
			print 'On slot {}'.format(slot_num)
			print 'A difs counter: {}'.format(station_a.difs_counter)
			print 'A backoff counter: {}'.format(station_a.backoff)
			print 'C difs counter: {}'.format(station_c.difs_counter)
			print 'C backoff counter: {}'.format(station_c.backoff)
		
		prepare_transmitting_stations(scenario.sending_stations, slot_num)	# Checking to see if a node is trying to send a packet at a given slot.
		check_difs_counters(scenario.sending_stations)						# Checking to see if the difs counter for any node is 0 to start the backoff
		check_backoff_counters(scenario.sending_stations)					# Checking to see if the backoff counter ofr any node is 0 so we can send a packet

		end_of_slot(scenario)												# Decreasing all counters in the scenario


if __name__ == '__main__':
	main()