import os
import sys
import time
import msvcrt
import win32file
import winioctlcon
import contextlib
import subprocess
from elevate import elevate
SECTOR_SIZE = 512
SECTORS_PER_CLUST = 8
MFT_SECTOR = 0
ATTR_NAME = 48
# 0 gaps exist within MFT, how many to
# encounter to quit
STOP_SEARCH = 20
delSecs = []
delNames = []

def main():
    #elevate()
    if len(sys.argv) < 1:
        raise Exception('Enter drive letter')
    else:
        print("sys: "+str(sys.argv[1]))
        drive = open(r'\\.\%s:' % sys.argv[1],"rb+")
        SECTOR_SIZE = getSectorSize(drive)
        SECTORS_PER_CLUST = eHex_to_int(getBytes(drive,0,0x0D,1))
        MFT_SECTOR = (eHex_to_int(getBytes(drive,0,0x30,8))*SECTORS_PER_CLUST)
        print(MFT_SECTOR)

        index = 0
        zeroCount = 0
        while(zeroCount<STOP_SEARCH):
            zeroCount+= scanFiles(drive,MFT_SECTOR,index)
            index+=2
        
        print(delSecs)
        print(delNames)
        if(askRecover()):
            recover(drive)
            subprocess.call("chkdsk "+str(sys.argv[1])+": /f", shell=True)
        freeDrive(drive)


def askRecover():
    print(str(len(delSecs)) +" file(s) found, recover? (y/n)")
    print("File flags will be flipped to active and chkdsk _: /f will run to recover orphaned files.")
    answer = input()
    if(answer == "y"):
        return True
    return False

def scanFiles(drive,sector,nextS):

    sector+=nextS
    attrTypeID = 99
    attribOffset = 0x14

    drive.seek((sector)*SECTOR_SIZE)
    totalAttrs = eHex_to_int(getBytes(drive,sector,0x28,2))-1
    attribOffset = eHex_to_int(getBytes(drive,sector,attribOffset,2))
    flags = eHex_to_int(getBytes(drive,sector,22,2))


    for i in range(0,totalAttrs):
        #Assuming file is declared as a resident, gather info.
        attrTypeID = eHex_to_int(getBytes(drive,sector,attribOffset,0x4))
        attrLength = eHex_to_int(getBytes(drive,sector,attribOffset+0x4,4))
        resident = eHex_to_int(getBytes(drive,sector,attribOffset+0x8,1))
        #TODO: implement better handling
        if(resident > 1):
            break
        contentSize = eHex_to_int(getBytes(drive,sector,attribOffset+0x10,4))
        contentOffset = eHex_to_int(getBytes(drive,sector,attribOffset+0x14,2))
        #Jump to next attribute from current attrib's offset
        if(attrTypeID == ATTR_NAME):
            nameLength = eHex_to_int(getBytes(drive,sector,attribOffset+contentOffset+0x40,1))
            name = getBytes(drive,sector,attribOffset+contentOffset+(0x42),nameLength*2)
            name = name.lower().replace(" ","")
            bytes.fromhex(name).decode('utf-8')
            name = bytes.fromhex(name).decode('utf-8')[::2]
            print(name, sector)
            if(flags<=0):
                delSecs.append(sector)
                delNames.append(name)
                print("Deleted file found.")

        attribOffset = (attribOffset+attrLength)

    if(getBytes(drive,sector,0,4)[0] == "0"):
        return 1

    return 0


def recover(drive):
    hVol = msvcrt.get_osfhandle(drive.fileno())
    win32file.DeviceIoControl(hVol, winioctlcon.FSCTL_LOCK_VOLUME,None, None) 
    index = 0

    for sector in delSecs:
        #Seek to sector, copy 512 bytes of sector
        drive.seek((sector*SECTOR_SIZE))
        data = drive.read(512)
        arr = []
        count = 0

        #Copy all bytes, flip bit at offset 22 (flag)
        for i in data:
            if(count == 22):
                arr.append(1)
            else:
                arr.append(i)
            count+=1

        print("["+str(delNames[index])+"] set for recovery.")
        index+=1

        #Re-seek to beginning, lock+dismount drive for writing
        drive.seek((sector*SECTOR_SIZE))
        drive.write(bytes(arr))
    
def freeDrive(drive):
    try:
        hVol = msvcrt.get_osfhandle(drive.fileno())
        win32file.DeviceIoControl(hVol, winioctlcon.FSCTL_DISMOUNT_VOLUME,None, None)
        win32file.DeviceIoControl(hVol, winioctlcon.FSCTL_UNLOCK_VOLUME,None, None)
    except:
        #no operations performed
        exit

def getSectorSize(drive):
    #Read up to 0x0C
    sizeBytes = drive.read(13)
    #Get Sector size identification bytes (0x0B to 0x0C), little endian to big
    bHex = (convert_hex(sizeBytes))
    littleE = (bHex.split(" "))[::-1]
    size = littleE[0]+littleE[1]
    # conv to hex->int, return
    return (int(size,16))

#Returns bytes at selected sector
def getBytes(drive,sector,offset,size):
    #re-seek to beginning of sector
    drive.seek(sector*SECTOR_SIZE)
    #Read to desired point
    sBytes = drive.read(offset+size)
    strStart = offset*2+offset
    selection = (convert_hex(sBytes))
    #Return bytes (string)
    return selection[strStart:len(selection)]

def eHex_to_int(string):
    #little endian convert
    temp = ""
    littleE = (string.split(" "))[::-1]
    temp = temp.join(littleE).replace(" ","")
    # conv to hex->int, return
    return (int(temp,16))

def convert_hex(string):
    return ' '.join([hex(character)[2:].upper().zfill(2) \
                     for character in string])

if __name__ == '__main__':
    main()
