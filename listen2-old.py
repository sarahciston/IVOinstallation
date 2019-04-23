#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests
from datetime import datetime
import time
import random
import os
import keyboard

#GraphQL Database
from graphqlclient import GraphQLClient
DB_URL = 'https://api.graph.cool/simple/v1/cjrfet7u94als0129de33wha3'
DB_UPLOAD_URL = 'https://api.graph.cool/file/v1/cjrfet7u94als0129de33wha3'
client = GraphQLClient(DB_URL)

#PyAudio
import pyaudio
import wave
import sys

#Variables
KEYWORD = 'brain'

#also modify file to show that it was accessed
#also add randomizer
#also add sentiment analysis

def gqlGetAll():
    results = client.execute('''
    query {
        allFiles(
            filter: {
                file2: null
            }) {
                id
                name
                url
                text
            }
        }
    ''')
    #print(results)
    #select random from this: result = #or do below in __main__
    #results = random.choice(d.)
    return results

def gqlGetLast():
    results = client.execute('''
    query {
        allFiles(
            last: 1
            skip: 1,
            filter: {
                file2: null
            }) {
                id
                name
                url
                text
            }
        }
    ''')
    return results

#QUERY TO GET FILE2_URL, searches by keyword and looks only for lyrebird converted files (file2null)
def gqlGetKeyword():
    variables = {"text": KEYWORD}
    variables = json.dumps(variables)
    variables = str(variables)
    #makes the query call with variables and returns results
    results = client.execute('''
    query ($text: String){
        allFiles(filter: {
            AND: [{
                text_contains: $text
            }, {
                file2: null
            }]
        }) {
            id
            name
            url
            text
        }
    }
    ''', variables)
    return results

#updates DB with STT text field
def gqlMutateText(fid):
    #sets any variables to pass to query, packs all the variables into a JSON, to feed to the GQLdb
    acc = datetime.now().replace(microsecond=0).isoformat() #.strftime("%m/%d/%Y, %I:%M:%S %p")
    #print(acc)
    variables = {"id": fid, "accessedAt": acc}
    variables = json.dumps(variables)
    variables = str(variables)
    #makes the query call with variables and returns results
    results = client.execute('''
    mutation ($id: ID!, $accessedAt: [DateTime!]) {
        updateFile(
            id: $id
            accessedAt: $accessedAt
        ) {
            id
            name
            accessedAt
            url
        }
    }
    ''', variables) # , ) do i add variables here, a dictionary/string of them?
    #print("added text to DB")
    #print(results)
    return results


#download TTS Lyrebird file
def getFile(furl, fname):
    r = requests.get(furl, allow_redirects=True)
    results = open('Play/' + fname, 'wb').write(r.content) #creates a file from the url downloaded
    return results

#play file
def playFile(fname):
    CHUNK = 1024
    #if len(sys.argv) < 2:
    #    print('plays a wave file. usage: %s filename.wav' % sys.argv[0])
    #wf = wave.open(sys.argv[1], 'rb')
    wf = wave.open('Play/' + fname, 'rb')
    #print("opened wave")
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                #num_frames=wf.getnframes(),
                output=True)
    #print("made stream")
    data = wf.readframes(CHUNK)
    #print("chunks read")
    while len(data) > 0:
        #print("while loop")
        stream.write(data, exception_on_underflow=False)
        #print("stream wrote")
        data = wf.readframes(CHUNK)
        #print("read frames")
        #HERE IS WHERE IT IS GETTING STUCK!!!!!
    #print("finished while data")
    stream.stop_stream()
    #print("stopped stream")
    stream.close()
    #print("closed stream")
    p.terminate()
    #print("terminated")
    #exit()

def main():
    ###CHOOSE HERE WHETHER TO RUN AN ORDERED QUERY OR A KEYWORD QUERY, HOW TO RANDOM QUERY?
    #results = gqlGetLast()
    #results = gqlGetKeyword()
    results = gqlGetAll()
    results = json.loads(results)
    results = results['data']
    results = results['allFiles']
    length = len(results)
    while True:
        try:
            #print("got to while loop")
            #user = input("press ENTER to hear INNERVOICEOVER\n") #waiting for input here, make a specific key?

            #randomizer
            resultPick = random.randint(1,length-1)
            result = results[resultPick]
            FILE2_ID = result['id']
            FILE2_NAME = result['name']
            FILE2_URL = result['url']
            FILE2_TEXT = result['text']

            getFile(FILE2_URL, FILE2_NAME)
            if os.path.getsize('Play/' + FILE2_NAME) < 200: #checks file size
                pass #print('too small')
            else:
                print('stand on the mat to hear inner(voice)over')
                keyboard.wait('space') #for makey
                print(FILE2_TEXT + "\n")
                playFile(FILE2_NAME)
                gqlMutateText(FILE2_ID)
                #time.sleep(1)
        except KeyboardInterrupt:
            break

main()
#exit()
sys.exit()

#exception_on_underflow pyaudio?????
#num_frames = int(len(frames) / (self._channels * width))
