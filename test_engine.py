from engine.path_generator import generate_path_for_employee
import json

print("Testing Nadi Pintara AI Engine...\n")
result = generate_path_for_employee("E003")
print(json.dumps(result, indent=2))
