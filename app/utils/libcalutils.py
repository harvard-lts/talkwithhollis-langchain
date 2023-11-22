import os

class LibCalUtils():
	def __init__(self):
		print('LibcalUtils init')
		filename = "./data/library_hour_cache.json"
		does_json_exist_1 = os.path.exists(filename)
		print(does_json_exist_1)

		if not does_json_exist_1:
			os.makedirs(os.path.dirname(filename), exist_ok=True)
			with open(filename, "w") as f:
				f.write("blah blah blah")

		does_json_exist_2 = os.path.exists(filename)
		print(does_json_exist_2)
		
