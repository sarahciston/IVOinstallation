#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests
from datetime import datetime

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
KEYWORD = 'perfect'

#also modify file to show that it was accessed
#also add features to play the file once grabbed
#also add randomizer
#also add sentiment analysis

def gqlGetOrdered():
    result = client.execute('''
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
            }
        }
    ''')
    return result

#QUERY TO GET FILE2_URL, searches by keyword and looks only for lyrebird converted files (file2null)
def gqlGetKeyword():
    variables = {"text": KEYWORD}
    variables = json.dumps(variables)
    variables = str(variables)
    #makes the query call with variables and returns results
    result = client.execute('''
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
        }
    }
    ''', variables)
    return result

###CHOOSE HERE WHETHER TO RUN AN ORDERED QUERY OR A KEYWORD QUERY, HOW TO RANDOM QUERY?
result = gqlGetOrdered()
#result = gqlGetKeyword()

result = json.loads(result)
result = result['data']
result = result['allFiles']
result = result[0]
FILE2_ID = result['id']
FILE2_NAME = result['name']
FILE2_URL = result['url']
#FILE2_TEXT = result['text']
#print(FILE2_ID, FILE2_NAME, FILE2_URL)

#updates DB with STT text field
def gqlMutateText(fid):
    #sets any variables to pass to query, packs all the variables into a JSON, to feed to the GQLdb
    acc = datetime.now().replace(microsecond=0).isoformat() #.strftime("%m/%d/%Y, %I:%M:%S %p")
    print(acc)
    variables = {"id": fid, "accessedAt": acc}
    variables = json.dumps(variables)
    variables = str(variables)
    #makes the query call with variables and returns results
    result = client.execute('''
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
    print(result)
    return result

gqlMutateText(FILE2_ID)

#download TTS Lyrebird file
def getFile(furl, fname):
    r = requests.get(furl, allow_redirects=True)
    results = open('Play/' + fname, 'wb').write(r.content) #creates a file from the url downloaded
    return results

getFile(FILE2_URL, FILE2_NAME)

#play file
def playFile(fname):
    CHUNK = 1024
    #if len(sys.argv) < 2:
    #    print('plays a wave file. usage: %s filename.wav' % sys.argv[0])
    #wf = wave.open(sys.argv[1], 'rb')
    wf = wave.open('Play/' + fname, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                #num_frames=wf.getnframes(),
                output=True)
    data = wf.readframes(CHUNK)
    while data != '':
        stream.write(data, exception_on_underflow=False)
        data = wf.readframes(CHUNK)
    stream.stop_stream()
    stream.close()
    p.terminate()

playFile(FILE2_NAME)

#exception_on_underflow pyaudio?????
#num_frames = int(len(frames) / (self._channels * width))
