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
DIFS_duration = 40											# microseconds
transmission_rate = 6										# Mbps
max_backoff_range = 1024									# slots
simulation_time = 10 										# sec
total_slots = (simulation_time * (10**6)) / slot_duration	# slots

scenario_choice = 'a'	# choosing which scenario to create

def main():
	if scenario_choice == 'a':
		station_a = Station('A', lambda_a, 'Sender', backoff_range, max_backoff_range)
		station_b = Station('B', 0, 'Reciever', backoff_range, max_backoff_range)
		station_c = Station('C', lambda_c, 'Sender', backoff_range, max_backoff_range)
		station_d = Station('D', 0, 'Reciever', 0, 0)
		station_a.set_collision_domain([station_b, station_c, station_d])
		station_b.set_collision_domain([station_a, station_c, station_d])
		station_c.set_collision_domain([station_a, station_b, station_d])
		station_d.set_collision_domain([station_a, station_b, station_c])
		spectrum = Spectrum()
		scenario = Scenario([station_a, station_b, station_c, station_d], spectrum)

	print scenario
	for i in range(0, total_slots):
		print 'will be used to iterate through every slot'
		break	




if __name__ == '__main__':
	main()