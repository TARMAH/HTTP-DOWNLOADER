import socket
import threading
import os
import time
import math
from threading import Lock
import re
import sys

lock=Lock()

START_TIME=time.time()
TOTAL_DOWNLOADED_BYTES=0
TOTAL_SPEED=0

def readCommandLineArguments():
    if len(sys.argv) == 10:
        if sys.argv[1] == '-r':
            resume_status=True

        num_of_connections=int(sys.argv[3])
        time=int(sys.argv[5])
        Host=str(sys.argv[7].split("/", 1)[0])
        Directory="/"+str(sys.argv[7].split("/", 1)[1])
        FilePathToDownloadTo=str(sys.argv[9])
        
        return resume_status,num_of_connections,time,Host,Directory,FilePathToDownloadTo
    
    elif len(sys.argv) == 9:
        resume_status=False
        num_of_connections=int(sys.argv[2])
        time=int(sys.argv[4])
        Host=str(sys.argv[6].split("/", 1)[0])
        Directory="/"+str(sys.argv[6].split("/", 1)[1])
        FilePathToDownloadTo=str(sys.argv[8])

        return resume_status,num_of_connections,time,Host,Directory,FilePathToDownloadTo

    else:
        print("Command line arguments not right")
        sys.exit(0)

def getContentLength(Host,directory):
    
    socketHeader=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    requestHeader="HEAD "+directory+" HTTP/1.1\r\nHost:"+Host+":80\r\n\r\n"

    socketHeader.connect((Host,80))
    
    socketHeader.send(requestHeader.encode('utf-8'))

    data = socketHeader.recv(100000)

    text = data.decode()

    contentLength = re.split('Content-Length:',text)[-1]
    
    contentLength=int(contentLength.splitlines()[0])
    
    socketHeader.close()
    
    return contentLength

def combineData(NUMBER_OF_THREADS,RESUMING_STATUS,FILE_LOCATION):

    print("\n\nFile is downloaded only writing\n\n")
    
    arrayOfFiles=[]
    
    for i in range(NUMBER_OF_THREADS):
        arrayOfFiles.append('C:\\Users\\Tarmah\\Desktop\\cnProject\\test'+str(i+1)+'.txt')
       
    with open(str(FILE_LOCATION)+'\\testAll.txt', 'wb+') as outfile:
        
        if RESUMING_STATUS==False:
            outfile.truncate(0)
            
        for fname in arrayOfFiles:
            with open(fname) as infile:
                outfile.write(infile.read().encode('utf-8'))

    print("WRITTEN")
    
class threadForDownloading(threading.Thread):
    
   def __init__(self, startingByte, endingByte,threadNumber,HOST,Directory,TimeToReportAfter,resume):
      threading.Thread.__init__(self)
      self.startingByte=startingByte
      self.endingByte=endingByte
      self.threadNumber=threadNumber
      self.HOST=HOST
      self.Directory=Directory
      self.TimeToReportAfter=TimeToReportAfter
      self.resume=resume
      
   def run(self):

      print("\n\nENDING BYTES OF THREAD"+str(self.threadNumber)+" = "+str(self.endingByte))
      print("\n\n")

      bytesDownloaded=0

      exists = os.path.isfile('C:\\Users\\Tarmah\\Desktop\\cnProject\\PRACTICE_NO_OF_BYTES_WRITTEN by THREAD '+str(self.threadNumber)+'.txt')

      if exists:
          
          f=open("C:\\Users\\Tarmah\\Desktop\\cnProject\\PRACTICE_NO_OF_BYTES_WRITTEN by THREAD"+str(self.threadNumber)+".txt","r+")
          
          if self.resume==False:
              bytesDownloaded=0
              f.truncate(0)
          else:
              f.seek(0)
              bytesDownloaded=int(f.read())

      else:
          
          f=open("C:\\Users\\Tarmah\\Desktop\\cnProject\\PRACTICE_NO_OF_BYTES_WRITTEN by THREAD"+str(self.threadNumber)+".txt","w+")
           
          f.seek(0)
          f.write('0')
          bytesDownloaded=0
          print(bytesDownloaded)

      global TOTAL_DOWNLOADED_BYTES
      
      lock.acquire()
      TOTAL_DOWNLOADED_BYTES += bytesDownloaded
      lock.release()

      time.sleep(2)
      
      global TOTAL_SPEED
      
      print("\nStarting Thread\n")

      filenameToDownloadTo="C:\\Users\\Tarmah\\Desktop\\cnProject\\test"+str(self.threadNumber)+".txt"

      self.startingByte += bytesDownloaded

      r2="GET "+self.Directory+" HTTP/1.1\r\nHost:"+self.HOST+":80\r\nRange: bytes="+str(self.startingByte)+"-"+str(self.endingByte)+"\r\n\r\n\r\n"

      print(r2)
      print("\n\n")
      
      socket1=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      socket1.connect((self.HOST,80))    
      socket1.send(r2.encode('utf-8'))

      ignore_HTTP_header_response=True

      TIME_TRACKER=time.time()

      with open(filenameToDownloadTo, 'a+') as file_to_write:

          if self.resume==True:
              
              file_to_write.seek(int(bytesDownloaded))
              
          else:
               file_to_write.truncate(0)
               
          print('\nFILE OPENED\n')
          
          while True:

              start=time.time()
              data = socket1.recv(1000000)
              end=time.time()

              lock.acquire()
              TOTAL_DOWNLOADED_BYTES+=len(data)
              lock.release()
              
              if ignore_HTTP_header_response==True:
                  ignore_HTTP_header_response=False
                  data= data.decode('utf-8').split('\r\n\r\n')[1]
                  file_to_write.write(str(data))
                  bytesDownloaded+=len(data)
                  f.seek(0)
                  f.write(str(bytesDownloaded))
                  print("Bytes downloaded by thread "+str(self.threadNumber)+" =  "+str(bytesDownloaded))
                  
              else:
                  if not data:
                      print("NO MORE DATA FOR THREAD "+str(self.threadNumber))
                      break
                    
                  file_to_write.write(str(data.decode('utf-8')))
                  bytesDownloaded+=len(data)
                  f.seek(0)
                  f.write(str(bytesDownloaded))
                  #print("SLEEPING")
                  time.sleep(1)

              if time.time()-TIME_TRACKER >= self.TimeToReportAfter:
                  if end-start==0:
                      continue
                  else:
                      speed=(((len(data))/(end-start))/(1024)) 
                      print("\n"+str(self.threadNumber)+" Thread : has DOwnloaded bytes  = "+str(bytesDownloaded)+" / "+str(self.endingByte-self.startingByte+1)+" and has  Download speed in kb/s = "+ str(speed))
                      TIME_TRACKER=time.time()
                      TOTAL_SPEED+=speed
                            
          print("CLOSING FILE")
          file_to_write.close()
          
      socket1.close()
      print("SOCKET CLOSED")


class threadForTotalDownloading(threading.Thread):
    def __init__(self,TimeToReportAfter,TOTAL_BYTES,resume):
        threading.Thread.__init__(self)
        self.TimeToReportAfter=TimeToReportAfter
        self.TOTAL_BYTES=TOTAL_BYTES
        self.resume=resume

    def run(self):        

        TIME_TRACK=time.time()
        
        global TOTAL_SPEED
        global TOTAL_DOWNLOADED_BYTES

        if self.resume==True:
            time.sleep(2)
            print("BEFORE RESUMING TOTAL BYTES DOWNLOADED =  "+str(TOTAL_DOWNLOADED_BYTES))
            print("\n\n")

        while True:

            if TOTAL_DOWNLOADED_BYTES>=self.TOTAL_BYTES:
                break

            if time.time()-TIME_TRACK>= self.TimeToReportAfter:
                print("\nTOTAL :   DOWNLOADED = "+str(TOTAL_DOWNLOADED_BYTES)+" / "+str(self.TOTAL_BYTES)+ " and TOTAL DOWNLOAD SPEED in kb/s= "+str(TOTAL_SPEED)+"\n")
                TIME_TRACK=time.time()
                TOTAL_SPEED=0

def main():

    RESUMING_STATUS,NUMBER_OF_THREADS,TIME,HOST,Directory,FilePathToDownloadTo=readCommandLineArguments()
    
    threads = []
    
    total=getContentLength(HOST,Directory)

    print("TOTAL BYTES TO DOWNLOAD = "+str(total))
    print("\n\n")
    
    division=total/NUMBER_OF_THREADS
    division=math.floor(division)
    
    start=0
    end=start+division-1

    thread = threadForTotalDownloading(TIME,total,RESUMING_STATUS)
    threads+= [thread]
    thread.start()
        
    for i in range(NUMBER_OF_THREADS):
        if((i+1)==NUMBER_OF_THREADS):
            end=total+10000000
        thread = threadForDownloading(start,end,i+1,HOST,Directory,TIME,RESUMING_STATUS) 
        threads += [thread] 
        thread.start()
        start=end+1
        end=start+division-1
        
    for x in threads:
        x.join()       

    combineData(NUMBER_OF_THREADS,RESUMING_STATUS,FilePathToDownloadTo)    
             
main()
print("Out of main")
exit



'''
COMMAND LINE ARGUMENTS TO TRY

python CN_PROJECT_NEAT.py -n 2 -i 1 -f localhost/files/test.txt -o C:\\Users\\Tarmah\\Desktop\\cnProject
python CN_PROJECT_NEAT.py -r -n 2 -i 1 -f localhost/files/test.txt -o C:\\Users\\Tarmah\\Desktop\\cnProject
python CN_PROJECT_NEAT.py -n 2 -i 1 -f www.w3.org/TR/PNG/iso_8859-1.txt -o C:\\Users\\Tarmah\\Desktop\\cnProject

'''
