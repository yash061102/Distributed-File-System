# file server
from socket import *
import os
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
server2 = SimpleXMLRPCServer(("localhost", 12002))


file_version_map = {}

#replicate to another server when change done in server b
def replicatetoserver(filename):

	f = open(filename, 'r')
	text = f.read()
	f.close()

	proxy1 = xmlrpc.client.ServerProxy("http://localhost:12001/",allow_none=True)
	reply_from_1=proxy1.replicate_rpca(filename,text,file_version_map[filename])

	proxy2 = xmlrpc.client.ServerProxy("http://localhost:12003/",allow_none=True)
	reply_from_2=proxy2.replicate_rpcc(filename,text,file_version_map[filename])
#for handle read write request

def updated_file(filename):
	file=open(filename,"r")
	text_in_file=file.read()
	return text_in_file
def read_write(filename, RW, text, file_version_map):
	if RW == "r":	# if read request
		try:
			file = open(filename, RW)	
			text_in_file = file.read()		# read the file's text into a string
			if filename not in file_version_map:
				file_version_map[filename] = 0
			print(text_in_file)
			return (text_in_file, file_version_map[filename])			
		except IOError:				# IOError occurs when open(filepath,RW) cannot find the file requested
			print (filename + " does not exist in directory\n")
			return (IOError, -1)
			pass

	elif RW == "a+":	# if write request

		if filename not in file_version_map:
			file_version_map[filename] = 0		# if empty (ie. if its a new file), set the version no. to 0
		else:
			file_version_map[filename] = file_version_map[filename] + 1		# increment version no.
			print("Updated " + filename + " to version " + str(file_version_map[filename]))

		file = open(filename, RW)
		file.write(text)

		
		print("FILE_VERSION: " + str(file_version_map[filename]))
		return ("Success", file_version_map[filename])


def send_client_reply(response, RW):

	if response[0] == "Success":
		reply = "File successfully written to..." + str(response[1])
		print("Sending file version " + str(response[1]))
		return reply

	elif response[0] is not IOError and RW == "r":
		return response

	elif response[0] is IOError: 
		reply = "File does not exist\n"
		return reply

def notcheckversion(RW,filename,msg):
			filename = filename	# file path to perform read/write on
			print ("Filename: " + filename)
			RW = RW		# whether its a read or write
			print ("RW: " + RW)
			text = msg		# the text to be written (this text is "READ" for a read and is ignored)
			print ("TEXT: " + text)

			response = read_write(filename, RW, text, file_version_map)	# perform the read/write and check if successful
			responce_from_reply=send_client_reply(response, RW)		# send back write successful message or send back text for client to read
			if RW == 'a+': #if write req then do replication to another server
				replicatetoserver(filename)
			return responce_from_reply

def checkversion(RW,filename,msg): #check version 
			client_filename = filename		# parse the version number to check
			print("Version check on " + client_filename)
			file_version = str(file_version_map[client_filename])
			return file_version

#function for change in own server
def replicate(filename,text,file_version):
			rep_filename = filename
			rep_text = text
			rep_version = str(file_version)
			file_version_map[rep_filename] = int(rep_version)
			f = open(rep_filename, 'w')
			f.write(rep_text)
			f.close()
			print(rep_filename + " successfully replicated...\n")
			return "replication is successfull at B server"

#for register method

server2.register_function(notcheckversion, "notcheckversion_rpc")
server2.register_function(checkversion,"checkversion_rpc")
server2.register_function(replicate,"replicate_rpcb")
server2.register_function(updated_file,"updated_file_rpc")
print ('SERVER_B SERVICE is ready to receive...')
server2.serve_forever()