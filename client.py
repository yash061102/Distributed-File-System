import sys
import client_lib
from datetime import datetime
import xmlrpc.client
from time import gmtime, strftime


#this is client side for making call to client_lib 
#client_lib contains all function which we call from here 

def main():

    print ("\n")
    client_lib.instructions()
    client_id = strftime("%Y%m%d%H%M%S", gmtime())
    file_version_map = {}

    while True:
       
        client_input = sys.stdin.readline()
            
            # function for write
        if "<write>" in client_input:
            while not client_lib.check_valid_input(client_input):       # error check the input
                 client_input = sys.stdin.readline()      #taking input
            
            filename = client_input.split()[1]      # get the filename from the input
            response = client_lib.handle_write(filename, client_id, file_version_map)    # handle the write request
            if response == False:
                print("File unlock polling timeout...")
                print("Try again later...")
            print ("Exiting <write> mode...\n")
            
            #function for read
        if "<read>" in client_input:
            while not client_lib.check_valid_input(client_input):    # error check the input
                 client_input = sys.stdin.readline()   # taking input for filename which we want to read

            filename = client_input.split()[1]   # get file name from the input
            print(filename)
            client_lib.handle_read(filename, file_version_map, client_id)        # handle the read request 
            print("Exiting <read> mode...\n")

        if "<instructions>" in client_input:  #function for printing instruction 
            client_lib.instructions()
      
           
        if "<quit>" in client_input:         #function for quit application
            print("Exiting application...")
            sys.exit()

if __name__ == "__main__":
    main()