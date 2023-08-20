# directory service
import os
import csv      #To work with csv file
from socket import *
from xmlrpc.server import SimpleXMLRPCServer


server = SimpleXMLRPCServer(("localhost", 9000))

def check_mappings(client_msg, list_files):

	filename = client_msg.split('|')[0]
	RW = client_msg.split('|')[1]

	with open("file_mappings.csv",'rt') as infile:        # open the .csv file storing the mappings
		d_reader = csv.DictReader(infile, delimiter=',')    # read file as a csv file, taking values after commas
		header = d_reader.fieldnames    	# skip header of csv file
		file_row = ""
		for row in d_reader:
			if list_files == False:
				# use the dictionary reader to read the values of the cells at the current row
				user_filename = row['user_filename']
				primary_copy = row['primary']

				if user_filename == filename and RW == 'w':		# check if file inputted by the user exists	(eg. file123)
					print("WRITING")
					actual_filename = row['actual_filename']	# get actual filename (eg. file123.txt)
					server_addr = row['server_addr']			# get the file's file server IP address
					server_port = row['server_port']			# get the file's file server PORT number

					print("actual_filename: " + actual_filename)
					print("server_addr: " + server_addr)
					print("server_port: " + server_port)

					return actual_filename + "|" + server_addr + "|" + server_port	# return string with the information on the file

				elif user_filename == filename and RW == 'r' and primary_copy == 'yes': #if read req
					print("READING")
					actual_filename = row['actual_filename']	# get actual filename (eg. file123.txt)
					server_addr = row['server_addr']			# get the file's file server IP address
					server_port = row['server_port']			# get the file's file server PORT number

					print("actual_filename: " + actual_filename)
					print("server_addr: " + server_addr)
					print("server_port: " + server_port)

					return actual_filename + "|" + server_addr + "|" + server_port	# return string with the information on the file

			else:
				user_filename = row['user_filename']
				file_row = file_row + user_filename +  "\n"		# append filename to return string
		if list_files == True:
			return file_row		
	return None 	# if file does not exist return None

server.register_function(check_mappings , "check_mappings_rpc")

print ('DIRECTORY SERVICE is ready to receive...')
server.serve_forever()
