#!/usr/bin/env python

import json
import requests
from graphqlclient import GraphQLClient
DB_URL = 'https://api.graph.cool/simple/v1/cjrfet7u94als0129de33wha3'
DB_UPLOAD_URL = 'https://api.graph.cool/file/v1/cjrfet7u94als0129de33wha3'

#variables based on the db schema for File
#contentType, createdAt, id, secret, updatedAt established by db?
STT_FILE_NAME = 'archer1.wav' #uniquely pull in from recorder somehow
#size = 0 #filesize brought in from somewhere?
STT_FILE_URL = 'link' #where the actual file is stored, pulled, played from
#text = '' #will get replaced with update from STT-MZDS
#user = '' #relational

client = GraphQLClient(DB_URL)

#STEP 1: this uploads an audio file as a new item in the DB
def saveSpeechFile():
    file = { 'data': open(STT_FILE_NAME, 'rb')}
    r = requests.post(DB_UPLOAD_URL, files=file)
    print('completed')

#STEP 4: this downloads an audio file from the db, after made by TTS presumably
#will also use in STT to create text, actually
#pull these var programmatically for each call
FILE_ID = 'cjs6ziw1s03220160b47wlq2k'
TTS_FILE_NAME = 'outputtest-ben2.wav'
WAV_URL = 'https://files.graph.cool/cjrfet7u94als0129de33wha3/cjs6ziv5k03210160lbwt223x'

def newTextToSpeechReq():
    r = requests.get(WAV_URL, allow_redirects=True)
    open(TTS_FILE_NAME, 'wb').write(r.content)
    print(r.headers.get('content-type'))

#STEP 2-3 maybe part of others, general queries
def gqlQuery():
    #sets any variables to pass to query, packs all the variables into a JSON, to feed to the GQLdb
    variables = {"id": FILE_ID}
    variables = json.dumps(variables)
    variables = str(variables)
    #makes the query call with variables and returns results
    result = client.execute('''
    query ($id: ID!){
        File(id: $id) {
            url
        }
    }
    ''', variables) # , ) do i add variables here, a dictionary/string of them?
    return result

#result = gqlQuery()
#print(result)

#def saveInputSpeechFile(name, url):
#    mutation = client.execute('''
#    mutation createFile($name: String!, $url: String!) {
#        createFile(name: $name, url: $url) {
#            id
#            name
#            createdAt
#            contentType
#            url
#        }
#    }
#    ''')
#    return mutation

#updates DB with STT text field
def gqlMutateText(fid, txt):
    #sets any variables to pass to query, packs all the variables into a JSON, to feed to the GQLdb
    variables = {"id": fid, "text": txt}
    variables = json.dumps(variables)
    variables = str(variables)
    #makes the query call with variables and returns results
    result = client.execute('''
    mutation ($id: ID!, $text: String) {
        updateFile(
            id: $id
            text: $text
        ) {
            id
            text
        }
    }
    ''', variables) # , ) do i add variables here, a dictionary/string of them?
    print("added text to DB")
    #print(result)
    return result

#gqlMutateText("", "you\'re pretty and delightful and people enjoy your company")

#connects two files in DB, STT & TTS
def gqlSetRelations(FILE2_ID, FILE_ID):
    variables = {"id": FILE2_ID, "file2FileId": FILE2_ID, "file1FileId": FILE_ID} #file is the relation it's associated with, NOT the actual link to the file to upload
    variables = json.dumps(variables)
    variables = str(variables)
    result = client.execute('''
    mutation ($file2FileId: ID!, $file1FileId: ID!) {
        setInToOutFiles(
            file2FileId: $file2FileId
            file1FileId: $file1FileId
        ) {
            file1File {
                url
            }
            file2File {
                url
            }
        }
    }
    ''', variables)
    print(result, ' completed relation')
    return result

#def updateInputSpeechToText():

#def saveTextToSpeech():

#def newTextToSpeechReq()

#result = gqlQuery()
#mutation = saveInputSpeechFile(STT_FILE_NAME, STT_FILE_URL)


#mutation = client.execute('''
#mutation ($fileName: String!) {
#    createPost(
#        content: $fileName
#        label: "pythontests"
#        slug: "it does work"
#        title: "test2"
#    ) {
#        id
#        slug
#    }
#}
#''')

#DELETES
def delete(fid):
    #sets any variables to pass to query, packs all the variables into a JSON, to feed to the GQLdb
    variables = {"id": fid}
    variables = json.dumps(variables)
    variables = str(variables)
    #makes the query call with variables and returns results
    result = client.execute('''
    mutation ($id: ID!) {
        deleteFile(
            id: $id
        ) {
            id
            text
        }
    }
    ''', variables) # , ) do i add variables here, a dictionary/string of them?
    #print("added text to DB")
    #print(result)
    return result

delete('cjurn16lo0qge0160gez74y24')
delete('cjurn13z20qgb0160cm8gbht9')
delete('cjurn0zdh0qg701606ixe5txj')
delete('cjurn0xan0qg40160u1y7ac4u')
delete('cjurn0sw30qg00160zozh9brc')
delete('cjurn0qlv0qfx0160ljblfktu')
delete('cjurn0lva0qfu0160ljom0jrg')
delete('cjurn0ipz0qfq0160j7a2nrxu')
delete('cjurn08qb0qfm016076eqpghj')
delete('cjurn06fo0qfj0160p7atsj08')
delete('cjurm0vza0qe40160dpjh2kf4')
delete('cjurm0tvc0qe101604zeri2ny')
delete('cjurlwwq00qdp01606buni53r')
delete('cjurlwv7t0qdm01608ir0sj5w')
delete('cjurlwo980qdi0160jjwcdh17')
delete('cjurlwma00qdf01603wx37qj7')
delete('cjurlwdfz0qdb0160u1h3mx3q')
delete('cjurlwbag0qd80160r8z6ws7f')
delete('cjurlvxgw0qd30160nts8lftk')
delete('cjurlvwid0qd00160bdrw32b3')
delete('cjurjwng00qcg01601dfm9bbk')
delete('cjurjwkp10qcd0160kvkdzr8k')

#for testing calls
def gqlQueryPlain():
    result = client.execute('''
    {
        File(id: "cjs6ziw1s03220160b47wlq2k") {
            url
        }
    }
    ''') # , ) do i add variables here, a dictionary/string of them?
    return result




#connects two files in DB, STT & TTS
def gqlSetRelations(FILE2_ID, FILE_ID):
    variables = {"id": FILE2_ID, "file2FileId": FILE2_ID, "file1FileId": FILE_ID} #file is the relation it's associated with, NOT the actual link to the file to upload
    variables = json.dumps(variables)
    variables = str(variables)
    result = client.execute('''
    mutation ($file2FileId: ID!, $file1FileId: ID!) {
        setInToOutFiles(
            file2FileId: $file2FileId
            file1FileId: $file1FileId
        ) {
            file1File {
                url
            }
            file2File {
                url
            }
        }
    }
    ''', variables)
    #print(result, ' completed relation')
    return result
#uploads an audio file as a new item in the DB
def uploadFile(fn):
    file = { 'data': open(fn, 'rb')}
    r = requests.post(DB_UPLOAD_URL, files=file)
    result = json.loads((r.content).decode()) #converts binary object with all fields to json to dict
    fid = result['id'] #pulls item from dict, no query to gql needed
    #print('completed upload' + fid)
    return fid #pass this to other place by running FILE_ID = uploadFile(FILE_NAME)

#updates DB with STT text field
def gqlMutateText(fid, txt):
    #sets any variables to pass to query, packs all the variables into a JSON, to feed to the GQLdb
    variables = {"id": fid, "text": txt}
    variables = json.dumps(variables)
    variables = str(variables)
    #makes the query call with variables and returns results
    result = client.execute('''
    mutation ($id: ID!, $text: String) {
        updateFile(
            id: $id
            text: $text
        ) {
            id
            text
        }
    }
    ''', variables) # , ) do i add variables here, a dictionary/string of them?
    #print("added text to DB")
    #print(result)
    return result

# LyreBirdAPI
import json
import requests
VOICE_URL = "https://avatar.lyrebird.ai/api/v0/generate"

#creates TTS FROM LYREBIRD API
def lyreBird(fid, txt):
    FILE2_NAME = str('TTSaudio/' + fid + 'tts.wav') #lyrebird needs
    lyreText = {'text': txt}
    r = requests.post(VOICE_URL, data=json.dumps(lyreText), headers={"Authorization": "Bearer oauth_1HESAgpzk8pyDd1grTJPNacB6TQ"})

    #print(r.status_code) ##GETTING 400 BAD REQUEST
    if r.status_code is 200 or 201:
        with open(FILE2_NAME, "wb") as f:
            f.write(r.content)
        FILE2_ID = uploadFile(FILE2_NAME) #saveTextToSpeechFile()
        gqlMutateText(FILE2_ID, txt)
        print(FILE2_ID, FILE_ID)
        gqlSetRelations(FILE2_ID, FILE_ID)
    else:
        print("status_code error: " + str(r.status_code))

#lyreBird("cjtj0ptzb0f0c0160irxof3et", "you are beautiful dome")


'''
curl 'https://api.graph.cool/simple/v1/cjsxyhfrq1rbr0176zvw8znks/export'\
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJPbmxpbmUgSldUIEJ1aWxkZXIiLCJpYXQiOjE1MTM1OTQzMTEsImV4cCI6MTU0NTEzMDMxMSwiYXVkIjasd3d3LmV4YW1wbGUuY29tIiwic3ViIjoianJvY2tldEBleGFtcGxlLmNvbSIsIkdpdmVuTmFtZSI6IkpvaG5ueSIsIlN1cm5hbWUiOiJSb2NrZXQiLCJFbWFpbCI6Impyb2NrZXRAZXhhbXBsZS5jb20iLCJSb2xlIjpbIk1hbmFnZXIiLCJQcm9qZWN0IEFkbWluaXN0cmF0b3IiXX0.L7DwH7vIfTSmuwfxBI82D64DlgoLBLXOwR5iMjZ_7nI' \
-d '{"fileType":"nodes","cursor":{"table":0,"row":0,"field":0,"array":0}}' \
-sSv
'''
