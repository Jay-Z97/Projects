import sys
import datetime as dt
from urllib.request import urlopen
import numpy as np
from skyfield.api import Loader, EarthSatellite, load, wgs84
import argparse
  
CATNR = [46497, 46496, 47510, 47506, 47507, 48918, 48914, 48916, 48917, 44390, 51070, 51008, 43800, 52762, 52749, 52758, 52759, 52755]
# satellites' NORAD IDs

def satcatnr(x):
    #mapping the satellite name to the right NORAD ID
    return {
        'x6':CATNR[0],
        'x7':CATNR[1],
        'x8':CATNR[2],
        'x9':CATNR[3],
        'XR1':CATNR[4],
        'x11':CATNR[5],
        'x12': CATNR[6],
        'x13': CATNR[7],
        'x15': CATNR[8],
        'x4': CATNR[9],
        'x14': CATNR[10],
        'x16': CATNR[11],
        'x2': CATNR[12],
        'x17': CATNR[13],
        'x18': CATNR[14],
        'x19': CATNR[15],
        'x20': CATNR[16],
        'x24': CATNR[17],
    }[x]

def getTLE(satname):
    #gets the most recent TLEs for given satellite from celestrak
    TLEurl="https://celestrak.com/NORAD/elements/gp.php?CATNR="+str(satcatnr(satname))
    TLEraw=urlopen(TLEurl)
    TLEsplitLines=TLEraw.read().splitlines()
    TLEdecodedLines=[i.decode("utf-8") for i in TLEsplitLines]
    print(*TLEdecodedLines,sep='\n')
    return TLEdecodedLines #TLE[0] - satellite name, TLE[1] - line 1, TLE[2] - line 2


def createSatObject(TLE):
    #creates timescale and satellite object for desired TLEs
    time_scale = load.timescale()
    satellite=EarthSatellite(TLE[1],TLE[2],TLE[0],time_scale)
    #print(satellite)
    return time_scale, satellite

#Getting arguments
parser = argparse.ArgumentParser()
parser.add_argument('satellite', help='satellite [x2, x4, x6, x7, x8, x9, xr1, x11, x12, x13, x14, x15, x16]')
parser.add_argument('-d', help='Number of hours for program to check the radiation areas flyovers', type=int, default=6)
args = parser.parse_args()
now = dt.datetime.utcnow()

#Creating sat object from TLE
TLE = getTLE(args.satellite)
ts, sat=createSatObject(TLE)

#Creating timeline from now to now+args.d hours (default = +6h)
t0 = ts.utc(now.year, now.month, now.day, now.hour, now.minute)
t1 = ts.utc(now.year, now.month, now.day, now.hour+args.d, now.minute)

print(t0.utc_strftime('%d-%m-%Y %H:%M:%S'))

#Create list of flyover times over radiation areas
flyover_list_future = []

### Old way of calculating SAA flyovers (circle around -23.5, -54 coordinates)
#SAA flyovers
#SAA = wgs84.latlon(-23.5, -54)
#t, events = sat.find_events(SAA, t0, t1, altitude_degrees=0.0)
#for ti, event in zip(t, events):
#    name = ('Entering SAA', 'culminate', 'Exiting SAA')[event]
#    if(event!=1):
        #print(ti.utc_strftime('%d-%m-%Y %H:%M:%S'), name)
#        flyover_list_future.append([ti.utc_strftime('%d-%m-%Y %H:%M:%S'),event])

in_SAA = 0 #parameter used to determine if during previous minute sat was in SAA
i = 0 # time parameter to iterate through
t=t0

while i<args.d*60:
    t =  ts.utc(now.year, now.month, now.day, now.hour, now.minute+i)
    lat, lon = wgs84.latlon_of(sat.at(t))
    lat = lat.degrees
    lon = lon.degrees
    if((lon*2/7 + 150/7) > lat) & ((lon*(-5/8) - 15)>lat) & ((lon/10 - 44) < lat) & ((lon*(-4/5) - 98) < lat):
        if(in_SAA == 0):
            in_SAA = 1
            flyover_list_future.append([t.utc_strftime('%d-%m-%Y %H:%M:%S'),0])
            #print(t.utc_strftime('%d-%m-%Y %H:%M:%S'))
            #print("Entering SAA")
    elif(in_SAA == 1):
       in_SAA = 0
       flyover_list_future.append([t.utc_strftime('%d-%m-%Y %H:%M:%S'),2])
       #print(t.utc_strftime('%d-%m-%Y %H:%M:%S'))
       #print("Exiting SAA")

    i = i+1

#North Pole Flyovers
NP = wgs84.latlon(90, 0)
t, events = sat.find_events(NP, t0, t1, altitude_degrees=-10.0)
for ti, event in zip(t, events):
    name = ('Entering NP', 'culminate', 'Exiting NP')[event]
    if(event!=1):
        #print(ti.utc_strftime('%d-%m-%Y %H:%M:%S'), name)
        flyover_list_future.append([ti.utc_strftime('%d-%m-%Y %H:%M:%S'),event])
        

#South Pole Flyovers
SP = wgs84.latlon(-90, 0)
t, events = sat.find_events(SP, t0, t1, altitude_degrees=-10.0)
for ti, event in zip(t, events):
    name = ('Entering SP', 'culminate', 'Exiting SP')[event]
    if(event!=1):
        #print(ti.utc_strftime('%d-%m-%Y %H:%M:%S'), name)
        flyover_list_future.append([ti.utc_strftime('%d-%m-%Y %H:%M:%S'),event])

#Sorts the list of flyover times
flyover_list_future.sort()

print(" \nYou can schedule radiation sensitive activities during these periods: ")
#print(flyover_list_future)

#Prints every other time from flyover_list_future, which gives the periods in which radiation sensitive activities can be scheduled
if(flyover_list_future[0][1]==2):
    for counter in range(len(flyover_list_future)-1):
        if(counter % 2==0):
            #Prints periods
            print(flyover_list_future[counter][0][:10] + " From " + flyover_list_future[counter][0][11:] + " to " + flyover_list_future[counter+1][0][11:])
            #Checks if period is longer than 7 minutes and if it is it prints sched.py command
            d1 = dt.datetime.strptime(flyover_list_future[counter][0], '%d-%m-%Y %H:%M:%S')
            d2 = dt.datetime.strptime(flyover_list_future[counter+1][0], '%d-%m-%Y %H:%M:%S')
            difference = d2-d1
            if(difference > dt.timedelta(minutes=7)):
                d1 = d1 +dt.timedelta(minutes=3)
                a = d1.strftime('%d-%m-%Y %H:%M:%S')
                print("    jobList.append(job('" +a[:17]+"35', ' '))")
            print(" ")
else:
    for counter in range(len(flyover_list_future)-2):
        if(counter % 2==0):
            #Prints periods
            print(flyover_list_future[counter+1][0][:10] + " From " + flyover_list_future[counter+1][0][11:] + " to " + flyover_list_future[counter+2][0][11:])
            #Checks if period is longer than 7 minutes and if it is it prints sched.py command
            d1 = dt.datetime.strptime(flyover_list_future[counter+1][0], '%d-%m-%Y %H:%M:%S')
            d2 = dt.datetime.strptime(flyover_list_future[counter+2][0], '%d-%m-%Y %H:%M:%S')
            difference = d2-d1
            if(difference > dt.timedelta(minutes=7)):
                d1 = d1 +dt.timedelta(minutes=3)
                a = d1.strftime('%d-%m-%Y %H:%M:%S')
                print("    jobList.append(job('" +a[:17]+"35', ' '))"+"\n")
            print(" ")



#Creating timeline from now to now-args.d hours (default = -6h)
t0 = ts.utc(now.year, now.month, now.day, now.hour - args.d, now.minute)
t1 = ts.utc(now.year, now.month, now.day, now.hour, now.minute)

#Create list of flyover times over radiation areas
flyover_list_past = []

print(" \nTimes of dangerous radiation area flyovers in the last " + str(args.d) + " hours:")

#SAA flyovers - old way of calculating SAA
#SAA = wgs84.latlon(-23.5, -54)
#t, events = sat.find_events(SAA, t0, t1, altitude_degrees=0.0)
#for ti, event in zip(t, events):
#    name = ('Entering SAA', 'culminate', 'Exiting SAA')[event]
#    if(event!=1):
        #print(ti.utc_strftime('%d-%m-%Y %H:%M:%S'), name)
#        flyover_list_past.append([ti.utc_strftime('%d-%m-%Y %H:%M:%S'),event])

in_SAA = 0 #parameter used to determine if during previous minute sat was in SAA
i = 0 # time parameter to iterate through
t=t0

while i<args.d*60:
    t =  ts.utc(now.year, now.month, now.day, now.hour-args.d, now.minute+i)
    lat, lon = wgs84.latlon_of(sat.at(t))
    lat = lat.degrees
    lon = lon.degrees
    if((lon*2/7 + 150/7) > lat) & ((lon*(-5/8) - 15)>lat) & ((lon/10 - 44) < lat) & ((lon*(-4/5) - 98) < lat):
        if(in_SAA == 0):
            in_SAA = 1
            flyover_list_past.append([t.utc_strftime('%d-%m-%Y %H:%M:%S'),0])
            print(t.utc_strftime('%d-%m-%Y %H:%M:%S'))
            print("Entering SAA")
    elif(in_SAA == 1):
       in_SAA = 0
       flyover_list_past.append([t.utc_strftime('%d-%m-%Y %H:%M:%S'),2])
       print(t.utc_strftime('%d-%m-%Y %H:%M:%S'))
       print("Exiting SAA")

    i = i+1

#North Pole Flyovers
NP = wgs84.latlon(90, 0)
t, events = sat.find_events(NP, t0, t1, altitude_degrees=-10.0)
for ti, event in zip(t, events):
    name = ('Entering North Pole', 'culminate', 'Exiting North Pole')[event]
    if(event!=1):
        #print(ti.utc_strftime('%d-%m-%Y %H:%M:%S'), name)
        flyover_list_past.append([ti.utc_strftime('%d-%m-%Y %H:%M:%S'),event+3])

#South Pole Flyovers
SP = wgs84.latlon(-90, 0)
t, events = sat.find_events(SP, t0, t1, altitude_degrees=-10.0)
for ti, event in zip(t, events):
    name = ('Entering South Pole', 'culminate', 'Exiting South Pole')[event]
    if(event!=1):
        #print(ti.utc_strftime('%d-%m-%Y %H:%M:%S'), name)
        flyover_list_past.append([ti.utc_strftime('%d-%m-%Y %H:%M:%S'),event+6])

#Sorts the list of flyover times
flyover_list_past.sort()

#print(flyover_list_past)

#Prints every other time from flyover_list_past, which gives the periods of radiation area flyovers
if(flyover_list_past[0][1]==0 or flyover_list_past[0][1]==3 or flyover_list_past[0][1]==6):
    for counter in range(len(flyover_list_past)-1):
        if(counter % 2==0):
            if(flyover_list_past[counter][1]==0):
                print(flyover_list_past[counter][0][:10] + " From " + flyover_list_past[counter][0][11:] + " to " + flyover_list_past[counter+1][0][11:] + " SAA flyover")
            elif(flyover_list_past[counter][1]==3):
                print(flyover_list_past[counter][0][:10] + " From " + flyover_list_past[counter][0][11:] + " to " + flyover_list_past[counter+1][0][11:]+ " North Pole flyover")
            else:
                print(flyover_list_past[counter][0][:10] + " From " + flyover_list_past[counter][0][11:] + " to " + flyover_list_past[counter+1][0][11:]+ " South Pole flyover")
else:
    for counter in range(len(flyover_list_past)-1):
        if(counter % 2==1):
            if(flyover_list_past[counter][1]==0):
                print(flyover_list_past[counter][0][:10] + " From " + flyover_list_past[counter][0][11:] + " to " + flyover_list_past[counter+1][0][11:] + " SAA flyover")
            elif(flyover_list_past[counter][1]==3):
                print(flyover_list_past[counter][0][:10] + " From " + flyover_list_past[counter][0][11:] + " to " + flyover_list_past[counter+1][0][11:]+ " North Pole flyover")
            elif(flyover_list_past[counter][1]==6):
                print(flyover_list_past[counter][0][:10] + " From " + flyover_list_past[counter][0][11:] + " to " + flyover_list_past[counter+1][0][11:]+ " South Pole flyover")
      
