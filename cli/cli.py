import argparse


## commands
# init it's intialize with a user and permissions and a fiele system root
# filesystem:
#	read
# 	write
# 	list

# OPS
# mkdir 
# cat
# create file
# create nested dir and files

## without any params it s shows the file system

class Cli:
	def __init__(self):
		self.parser = argparse.ArgumentParser()
	
	def parse(self,):
		self.parser.parse_args()


if __name__ == "__main__":
	cli = Cli()
	cli.parse()