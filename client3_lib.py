from socket import *
import sys
import os
import time
import os.path
import xmlrpc.client

curr_path = os.path.dirname(os.path.realpath(sys.argv[0]))      # get path of current program (client.py)


def send_write(fileserverIP_DS, fileserverPORT_DS, filename , RW, file_version_map, msg):
    if filename not in file_version_map:
        file_version_map[filename] = 0

    elif RW != "r":
        file_version_map[filename] = file_version_map[filename] + 1

    send_msg = filename + "|" + RW + "|" + msg 

    print("Sending version: " + str(file_version_map[filename]))
    
    proxy = xmlrpc.client.ServerProxy("http://"+fileserverIP_DS+":"+str(fileserverPORT_DS)+"/",allow_none=True)
    reply=proxy.notcheckversion_rpc(RW,filename,msg)

    return reply

def send_read(fileserverIP_DS, fileserverPORT_DS, filename , RW, file_version_map, msg, filename_DS, client_id):
    if filename not in file_version_map:
        file_version_map[filename] = 0
        print("REQUESTING FILE FROM FILE SERVER - FILE NOT IN CACHE")
        send_msg = filename + "|" + RW + "|" + msg    
        proxy = xmlrpc.client.ServerProxy("http://"+fileserverIP_DS+":"+str(fileserverPORT_DS)+"/")
        reply=proxy.notcheckversion_rpc(RW,filename,msg)
        return "False"+"|"+reply[0]+"|"+str(reply[1])

    cache_file = curr_path + "\\client_cache" + client_id + "\\" + filename_DS  
    if os.path.exists(cache_file) == True:
        send_msg = "CHECK_VERSION|" + filename
        # client_socket1 = create_socket()
        proxy = xmlrpc.client.ServerProxy("http://"+fileserverIP_DS+":"+str(fileserverPORT_DS)+"/")
        version_FS=proxy.checkversion_rpc(RW,filename,msg)

        print ("Checking version...")


    if version_FS != str(file_version_map[filename]):
        print("Versions do not match...")
        print("REQUESTING FILE FROM FILE SERVER...")
        file_version_map[filename] = int(version_FS) 
        send_msg = filename + "|" + RW + "|" + msg    

        proxy = xmlrpc.client.ServerProxy("http://"+fileserverIP_DS+":"+str(fileserverPORT_DS)+"/")
        reply=proxy.notcheckversion_rpc(RW,filename,msg)

        return "False"+"|"+reply[0]+"|"+str(reply[1])   # didn't go to cache - new version
    else:
        # read from cache
        print("Versions match, reading from cache...")
        cache(filename_DS, "READ", "r", client_id)

    return "True"+"|"+""     # went to cache




def lock_unlock_file(client_id, filename, lock_or_unlock):

    serverName = 'localhost'
    serverPort = 4040   # port of directory service
  
    

    if lock_or_unlock == "lock":
        msg = client_id + "_1_:" + filename  # 1 = lock the file
        proxy = xmlrpc.client.ServerProxy("http://localhost:4040/")
        reply=proxy.forone_rpc(client_id,filename)


    elif lock_or_unlock == "unlock":
        msg = client_id + "_2_:" + filename   # 2 = unlock the file
        proxy = xmlrpc.client.ServerProxy("http://localhost:4040/")
        reply=proxy.fortwo_rpc(client_id,filename)

    return reply

def handle_write(filename, client_id, file_version_map):
    # ------ INFO FROM DS ------

    reply_DS = send_directory_service(filename, 'w', False)  # request the file info from directory service

    if reply_DS == "FILE_DOES_NOT_EXIST":
        print(filename + " does not exist on a fileserver")
    else:
        filename_DS = reply_DS.split('|')[0]
        fileserverIP_DS = reply_DS.split('|')[1]
        fileserverPORT_DS = reply_DS.split('|')[2]
        print(filename_DS)


        # ------ LOCKING ------

        grant_lock = lock_unlock_file(client_id, filename_DS, "lock")


        while grant_lock != "file_granted":
            print("File not granted, polling again...")

            grant_lock = lock_unlock_file(client_id, filename_DS, "lock")


            if grant_lock == "TIMEOUT":     # if timeout message received from locking service, break
                return False

            time.sleep(0.1)     # wait 0.1 sec if lock not available and request it again

        print("You are granted the file...")

        # ------ ClIENT WRITING TEXT ------
        print ("Write some text...")
        print ("<end> to finish writing")
        print_breaker()
        write_client_input = ""
        while True:
            client_input = sys.stdin.readline()
            if "<end>" in client_input:  # check if user wants to finish writing
                break
            else: 
                write_client_input += client_input
        print_breaker()

        

        # ------ WRITING TO FS ------

        reply_from_sendwrite=send_write(fileserverIP_DS, int(fileserverPORT_DS), filename_DS, "a+", file_version_map, write_client_input) # send text and filename to the fileserver

        print (reply_from_sendwrite.split("...")[0])    # split version num from success message and print message
        version_num = int(reply_from_sendwrite.split("...")[1]) 
        
        if version_num != file_version_map[filename_DS]:
            print("Server version no changed - updating client version no.")
            file_version_map[filename_DS] = version_num


        # ------ CACHING ------
        proxy = xmlrpc.client.ServerProxy("http://"+fileserverIP_DS+":"+str(fileserverPORT_DS)+"/")
        reply=proxy.updated_file_rpc(filename_DS)
        cache(filename_DS,reply,"w",client_id)
        # cache(filename_DS, write_client_input, "a+", client_id)

        # ------ UNLOCKING ------

        reply_unlock = lock_unlock_file(client_id, filename_DS, "unlock")

        print (reply_unlock)

        return True

def cache(filename_DS, write_client_input, RW, client_id):
    cache_file = curr_path + "\\client_cache" + client_id + "\\" + filename_DS       # append the cache folder and filename to the path
    
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)         # create the directory/file

    if RW == "a+" or RW == "w":
        with open(cache_file, RW) as f:        # write to the cached file
            f.write(write_client_input)
    else:
        with open(cache_file, "r") as f:        # read from the cached file
            print_breaker()
            print(f.read())
            print_breaker()


def handle_read(filename, file_version_map, client_id):

    reply_DS = send_directory_service(filename, 'r', False)  # send file name to directory service


    if reply_DS == "FILE_DOES_NOT_EXIST":
        print(filename + " does not exist on a fileserver")
    else:
        # parse info received from the directory service
        filename_DS = reply_DS.split('|')[0]
        fileserverIP_DS = reply_DS.split('|')[1]
        fileserverPORT_DS = reply_DS.split('|')[2]

        read_cache = send_read(fileserverIP_DS, int(fileserverPORT_DS), filename_DS, "r", file_version_map, "READ", filename_DS, client_id) # send filepath and read to file server

        check=read_cache.split("|")[0]

        if (read_cache.split("|")[0]=='False'):
            reply_FS=read_cache.split("|")[1]
            version_file=read_cache.split("|")[2]
  

            if reply_FS != "EMPTY_FILE":
                print_breaker()
                print (reply_FS)
                print(version_file)
                print_breaker()

                cache(filename_DS, reply_FS, "w", client_id)  # update the cached file with the new version from the file server
                print (filename_DS + " successfully cached...")
            else:
                print(filename_DS + " is empty...")
                del file_version_map[filename_DS]

#list files is use for listing file so for read write it is false.
def send_directory_service(filename, RW, list_files):
    serverName = 'localhost'
    serverPort = 9090   # port of directory service


#for reading and writing
    if not list_files:
        msg = filename + '|' + RW
        # send the string requesting file info to directory send_directory_service

        proxy = xmlrpc.client.ServerProxy("http://localhost:9090/")
        reply=proxy.check_mappings_rpc(msg,False)
    
    else:
        msg = "LIST"

        proxy = xmlrpc.client.ServerProxy("http://localhost:9090/")
        reply=proxy.check_mappings_rpc(msg,True)
        print ("Listing files on directory server...")
        print (reply)


    return reply

def instructions():
    # instructions to the user
    print ("------------------- INSTRUCTIONS ----------------------")
    print ("<write> [filename] - write to file mode")
    print ("<end> - finish writing")
    print ("<read> [filename] - read from file mode")
    print ("<instructions> - lets you see the instructions again")
    print ("<quit> - exits the application")
    print ("-------------------------------------------------------\n")

def print_breaker():
    print ("--------------------------------")


#check for valid input or not which we pass as argument
def check_valid_input(input_string):
    # check for correct format for message split
    if len(input_string.split()) < 2:
        print ("Incorrect format")
        instructions()
        return False
    else:
        return True