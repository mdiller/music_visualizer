import hashlib
import json
from collections import OrderedDict
import typing
import os

THIS_FILE = __file__
THIS_DIR = os.path.dirname(os.path.realpath(__file__))
SCHEMA_FILE = os.path.join(THIS_DIR, "schema.json")
OUTPUT_PYTHON = os.path.join(THIS_DIR, "data_classes.py")
OUTPUT_TYPESCRIPT = os.path.join(THIS_DIR, "../src/generated/DataClasses.ts")

REF_START = "#/"

def regenerate_schema():
	print(THIS_FILE)

	def hash_file(filename: str):
		with open(filename, "r") as f:
			return hashlib.sha256(f.read().encode()).hexdigest()[:10]


	VERSION_HASH = f"# VERSION_HASH: {hash_file(THIS_FILE)}_{hash_file(SCHEMA_FILE)}"

	with open(OUTPUT_PYTHON, "r") as f:
		text =  f.read()

	if text.startswith(VERSION_HASH):
		print("No schema changes.")
		return None


	with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
		schemas = json.load(f, object_pairs_hook=OrderedDict)


	class JsonWrapper():
		_data: OrderedDict
		def __init__(self, json_data: OrderedDict):
			self._data = json_data
			for key, value in json_data.items():
				setattr(self, key, value)

		def __getattr__(self, name):
			# This method is called when the attribute is not found in the usual places.
			try:
				return self._data[name]
			except KeyError:
				raise AttributeError(f"'JsonWrapper' object has no attribute '{name}'")

		def __getitem__(self, key):
			# This method allows dictionary-like access.
			return self._data[key]

		def __repr__(self):
			return f"JsonWrapper({self._data})"

	class JsonProperty(JsonWrapper):
		name: str
		type: str
		def __init__(self, name: str, json_data: OrderedDict):
			super().__init__(json_data)
			self.name = name
			self.type = json_data["type"]
		
		@property
		def typescript_type(self):
			if self.type == "array":
				element_type = self["items"]["type"]
				if REF_START in element_type:
					refname = element_type.replace(REF_START, "")
					return f"{refname}[]"
				else:
					raise Exception("NOT IMPLEMENTED")
			elif REF_START in self.type:
				return self.type.replace(REF_START, "")
			else:
				return self.type


	class JsonClass(JsonWrapper):
		props: typing.List[JsonProperty]
		def __init__(self, json_data: OrderedDict):
			super().__init__(json_data)
			self.name = self.title
			self.props = []
			for propname in json_data["properties"]:
				self.props.append(JsonProperty(propname, json_data["properties"][propname]))

	class CodeBuilder():
		indent_level: int
		lines: typing.List[str]
		def __init__(self):
			self.lines = []
			self.indent_level = 0
		
		def block(self, text, text_end = None):
			self.line(text)
			return CodeBlockIndent(self, text_end)
		
		def line(self, text):
			if text == "":
				self.lines.append("")
			else:
				indent = self.indent_level * "\t"
				self.lines.append(f"{indent}{text}")
		
		def dump(self):
			return "\n".join(self.lines)


	class CodeBlockIndent():
		code: CodeBuilder
		text_end: str
		def __init__(self, code: CodeBuilder, text_end = None):
			self.code = code
			self.text_end = text_end

		def __enter__(self):
			self.code.indent_level += 1
			return self

		def __exit__(self, exc_type, exc_value, traceback):
			self.code.indent_level -= 1
			if self.text_end is not None:
				self.code.line(self.text_end)
			return False

	objects: typing.List[JsonClass]
	objects = []
	for schema in schemas:
		objects.append(JsonClass(schema))


	code = CodeBuilder()
	code.line(VERSION_HASH)
	code.line("import json")
	code.line("from collections import OrderedDict")

	code.line("")
	for object in objects:
		props: typing.List[JsonProperty]
		props = object.props

		with code.block(f"class {object.name}():"):
			args = []
			for prop in props:
				args.append(f"{prop.name} = None")
			with code.block(f"def __init__(self, {', '.join(args)}):"):
				for prop in props:
					code.line(f"self.{prop.name} = {prop.name}")

			code.line("")
			
			with code.block("def toJson(self):"):
				with code.block(f"return OrderedDict([", "])"):
					for prop in props:
						if prop.type == "array":
							if REF_START in prop["items"]["type"]:
								code.line(f"(\"{prop.name}\", list(map(lambda x: x if x is None else x.toJson(), self.{prop.name}))),")
							else:
								raise Exception("NOT IMPLEMENTED")
						elif REF_START in prop.type:
							code.line(f"(\"{prop.name}\", self.{prop.name} if self.{prop.name} is None else self.{prop.name}.toJson()),")
						else:
							code.line(f"(\"{prop.name}\", self.{prop.name}),")


			code.line("")
			
			with code.block("def updateFromJson(self, json: OrderedDict):"):
				with code.block("if json is None:"):
					code.line("return")
				for prop in props:
					with code.block(f"if \"{prop.name}\" in json:"):
						if prop.type == "array":
							element_type = prop["items"]["type"]
							if REF_START in element_type:
								element_type = element_type.replace(REF_START, "") 
								code.line(f"self.{prop.name} = list(map(lambda x: {element_type}.fromJson(x), json.get(\"{prop.name}\")))")
							else:
								raise Exception("NOT IMPLEMENTED")
						if REF_START in prop.type:
							prop_type = prop.type.replace(REF_START, "")
							code.line(f"self.{prop.name} = {prop_type}.fromJson(json.get(\"{prop.name}\"))")
						else:
							code.line(f"self.{prop.name} = json.get(\"{prop.name}\")")

			code.line("")

			code.line("@classmethod")
			with code.block("def fromJson(cls, json: OrderedDict):"):
				code.line(f"self = {object.name}()")
				code.line("self.updateFromJson(json)")
				code.line(f"return self")


			code.line("")

			code.line("@classmethod")
			with code.block("def fromFile(cls, filename: str):"):
				with code.block("with open(filename, \"r\") as f:"):
					code.line(f"return {object.name}.fromJson(json.loads(f.read()))")

			code.line("")


			with code.block("def writeFile(self, filename: str):"):
				code.line("text = json.dumps(self.toJson(), indent=\"\\t\")")
				with code.block("with open(filename, \"w+\") as f:"):
					code.line(f"f.write(text)")

		
		code.line("")

	with open(OUTPUT_PYTHON, "w+") as f:
		f.write(code.dump())



	# TYPESCRIPT

	code = CodeBuilder()
	code.line("import npyjs from 'npyjs';")
	code.line("import ndarray from 'ndarray';")
	code.line("import { createSignal, SimpleSignal } from '@motion-canvas/core';")
	code.line("")


	object_names = []
	for object in objects:
		object_names.append(object.name)
		props: typing.List[JsonProperty]
		props = object.props

		with code.block(f"class {object.name} {{", "}"):
			for prop in props:
				code.line(f"{prop.name}: {prop.typescript_type};")
			if object.name == "NumpyData":
				code.line("data: any;")
				code.line("frameSignal: SimpleSignal<number>;")
				code.line("valueSignal: SimpleSignal<number>;")
			code.line("")

			const_args = []
			for prop in props: 
				const_args.append(f"{prop.name}: {prop.typescript_type};")
			with code.block(f"constructor(json: {{ {' '.join(const_args)} }}) {{", "}"):
				for prop in props:
					if prop.type == "array":
						element_type = prop["items"]["type"]
						if REF_START in element_type:
							element_type = element_type.replace(REF_START, "") 
							code.line(f"this.{prop.name} = json.{prop.name}.map(d => new {element_type}(d));")
						else:
							raise Exception("NOT IMPLEMENTED")
					elif REF_START in prop.type:
						prop_type = prop.type.replace(REF_START, "")
						code.line(f"this.{prop.name} = new {prop_type}(json.{prop.name});")
					else:
						code.line(f"this.{prop.name} = json.{prop.name};")
				if object.name == "NumpyData":
					code.line("this.frameSignal = createSignal(0);")
					code.line("this.valueSignal = createSignal(0);")
		
			# add a load() for everything
			if object.name == "StemInfo" or object.name == "PoseInfo":
				code.line("")
				with code.block("getDataProps(): NumpyData[] {", "}"):
					with code.block("return [", "]"):
						for prop in props:
							if prop.type == "#/NumpyData":
								code.line(f"this.{prop.name},")

			if object.name == "NumpyData":
				code.line("")
				with code.block("async load(): Promise<void> {", "}"):
					with code.block("if (this.filename == null) {", "}"):
						code.line("console.error(\"Missing numpy file!\");")
					with code.block("else {", "}"):
						code.line("const n = new npyjs();")
						code.line(f"var response = await n.load(this.filename);")
						code.line(f"this.data = ndarray(response.data, response.shape);")

		
		code.line("")

	code.line(f"export {{ {', '.join(object_names)} }};")


	with open(OUTPUT_TYPESCRIPT, "w+") as f:
		f.write(code.dump())


	print("done!")
	

if __name__ == "__main__":
	regenerate_schema()


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