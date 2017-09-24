class Station:
	
	def __init__(self, name, lambda_val, role, backoff, max_backoff):
		self.name = name
		self.lambda_val = lambda_val
		self.role = role
		self.backoff = backoff
		self.max_backoff = max_backoff

	def __str__(self):
		ret_str = 'Station {}:\n\tRole: {}\n\tLambda: {}\n\tBackoff: {}\n\n'.format(self.name, self.role, self.lambda_val, self.backoff)
		return ret_str


	def set_collision_domain(self, collision_domain):
		self.collision_domain = collision_domain

def main():
	print 'In the main of station.py'


if __name__ == '__main__':
	main()