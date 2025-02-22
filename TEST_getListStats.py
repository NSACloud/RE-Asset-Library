#Author: NSA Cloud
import os
DIR = r"H:\VisualStudioProjects\REE.PAK.Tool-main\REE.Unpacker\REE.Unpacker\bin\Debug\Projects"
minLength = 1000
maxLength = 1
maxVerLength = 1
minLine = ""
maxVer = 1
extensionSet = set()
for entry in os.scandir(DIR):
	if entry.is_file():
		filePath = os.path.join(DIR,entry.name)
		with open(filePath,"r") as file:
			for line in file.readlines():
				if "natives" in line:
					if len(line) < minLength:
						minLine = line
						minLength = len(line)	
					if len(line) > maxLength:
						maxLength = len(line)
						maxLine = line
					split = line.split(".")
					ext = "."+split[1]
					#ext = os.path.splitext(os.path.splitext(line)[0])[1]
					version = os.path.splitext(line)[1][1:]
					if version.isdigit() and int(version) > maxVer:
						#maxVerLength = len(version)
						maxVer = int(version)
					extensionSet.add(ext)
print(minLength)
print(minLine)

print(maxLength)
print(maxLine)

print(maxVer)
#print(maxVerLength)

print(sorted(list(extensionSet)))