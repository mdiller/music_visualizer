import json
from collections import OrderedDict

SCHEMA_FILE = "schema.json"
OUTPUT_PYTHON = "data_classes.py"


with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
	schemas = json.load(f, object_pairs_hook=OrderedDict)


# TODO: cleanup this code a bunch
# - add a class for props and for class probably
# - add a codebuilder class that lets us do things easier
# TODO: support more jsonschema features and verify that the ones we implemented are correct
# TODO: make a jsonschema-driven data entry thing so we can make changes to configs via a gui (or find an implementation of this)
# - a custom one would allow us to do cool stuff like edit gradients in real time for the finished product
# - would also be real nice to have for future projects mebbe
# - if we end up doing this, would make for a great split-off project. could make into a python module/library (python to generate code etc, and to host the server that vue connects to?)


REF_START = "#/"

pylines = []
pylines.append("import json")
pylines.append("from collections import OrderedDict")

pylines.append("")
for schema in schemas:
	classname = schema['title']
	pylines.append(f"class {classname}():")
	args = []
	for propname in schema["properties"]:
		prop = schema["properties"][propname]
		args.append(f"{propname} = None")
	pylines.append(f"\tdef __init__(self, {', '.join(args)}):")
	for propname in schema["properties"]:
		prop = schema["properties"][propname]
		pylines.append(f"\t\tself.{propname} = {propname}")

	pylines.append("")
	
	pylines.append("\tdef toJson(self):")
	pylines.append(f"\t\treturn OrderedDict([")
	for propname in schema["properties"]:
		prop = schema["properties"][propname]
		if prop["type"] == "array" and "$ref" in prop["items"]:
			pylines.append(f"\t\t\t(\"{propname}\", list(map(lambda x: x.toJson(), self.{propname}))),")
		else:
			pylines.append(f"\t\t\t(\"{propname}\", self.{propname}),")
	pylines.append("\t\t])")

	pylines.append("")

	pylines.append("\t@classmethod")
	pylines.append("\tdef fromJson(cls, json: OrderedDict):")
	pylines.append(f"\t\tself = {classname}()")
	for propname in schema["properties"]:
		prop = schema["properties"][propname]
		# pylines.append(f"\t\tself.{propname} = {refname}.fromJson(json.get(\"{propname}\"))")
		if prop["type"] == "array" and "$ref" in prop["items"]:
			refname = prop["items"]["$ref"].replace(REF_START, "") 
			pylines.append(f"\t\tself.{propname} = list(map(lambda x: {refname}.fromJson(x), json.get(\"{propname}\")))")
		else:
			pylines.append(f"\t\tself.{propname} = json.get(\"{propname}\")")
	pylines.append(f"\t\treturn self")

	pylines.append("")

	pylines.append("\t@classmethod")
	pylines.append("\tdef fromFile(cls, filename: str):")
	pylines.append("\t\twith open(filename, \"r\") as f:")
	pylines.append(f"\t\t\treturn {classname}.fromJson(json.loads(f.read()))")

	pylines.append("")


	pylines.append("\tdef writeFile(self, filename: str):")
	pylines.append("\t\twith open(filename, \"w+\") as f:")
	pylines.append(f"\t\t\tf.write(json.dumps(self.toJson(), indent=\"\\t\"))")

	
	pylines.append("")

pytext = "\n".join(pylines)

with open(OUTPUT_PYTHON, "w+") as f:
	f.write(pytext)

print("done!")
	



# class Thing():
# 	def __init__(self):
# 		self.x = None
	
# 	@cls()

# OrderedDict([
# 	("fmin", librosa.midi_to_hz(9)),
# 	("framerate", 30),
# 	("bins_per_octave", 48),
# 	("octaves", 9)
# ])