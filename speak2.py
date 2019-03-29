#!/usr/bin/env python
# -*- coding: utf-8 -*-
#python mozaudiocapture.py -m models/output_graph.pbmm -a models/alphabet.txt -l models/lm.binary -t models/trie --savewav SAVEWAVS

#Mozilla DeepSpeech & Recording
import time, logging
from datetime import datetime
import threading, collections, queue, os, os.path
import wave
import pyaudio
import webrtcvad
from halo import Halo
import deepspeech
import numpy as np
import keyboard

logging.basicConfig(level=20)

# LyreBirdAPI
import json
import requests
VOICE_URL = "https://avatar.lyrebird.ai/api/v0/generate"

#GraphQL Database
from graphqlclient import GraphQLClient
DB_URL = 'https://api.graph.cool/simple/v1/cjrfet7u94als0129de33wha3'
DB_UPLOAD_URL = 'https://api.graph.cool/file/v1/cjrfet7u94als0129de33wha3'
client = GraphQLClient(DB_URL)

#VariablesTK
FILE_NAME = '' #comes from the recorder
#FILE_ID = '' #will get created by the file being saved to DB
FILE_URL = ''
RECORDING = ''
TEXT = ''
FILE2_ID = ''

#model = deepspeech.Model(MOD, N_FEATURES, N_CONTEXT, ALPHABET, BEAM_WIDTH)

class Audio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

    FORMAT = pyaudio.paInt16
    RATE = 16000
    CHANNELS = 1
    BLOCKS_PER_SECOND = 50
    BLOCK_SIZE = int(RATE / float(BLOCKS_PER_SECOND))

    def __init__(self, callback=None):
        def proxy_callback(in_data, frame_count, time_info, status):
            callback(in_data)
            return (None, pyaudio.paContinue)
        if callback is None: callback = lambda in_data: self.buffer_queue.put(in_data)
        self.buffer_queue = queue.Queue()
        self.sample_rate = self.RATE
        self.block_size = self.BLOCK_SIZE
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=self.FORMAT,
                                   channels=self.CHANNELS,
                                   rate=self.sample_rate,
                                   input=True,
                                   frames_per_buffer=self.block_size,
                                   stream_callback=proxy_callback)
        self.stream.start_stream()

    def read(self):
        """Return a block of audio data, blocking if necessary."""
        return self.buffer_queue.get()

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    frame_duration_ms = property(lambda self: 1000 * self.block_size // self.sample_rate)

    def write_wav(self, filename, data):
        #logging.info("write wav %s", filename)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        # wf.setsampwidth(self.pa.get_sample_size(FORMAT))
        assert self.FORMAT == pyaudio.paInt16
        wf.setsampwidth(2)
        wf.setframerate(self.sample_rate)
        wf.writeframes(data)
        wf.close()

class VADAudio(Audio):
    """Filter & segment audio with voice activity detection."""

    def __init__(self, aggressiveness=3):
        super().__init__()
        self.vad = webrtcvad.Vad(aggressiveness)

    def frame_generator(self):
        """Generator that yields all audio frames from microphone."""
        while True:
            yield self.read()

    def vad_collector(self, padding_ms=300, ratio=0.75, frames=None):
        """Generator that yields series of consecutive audio frames comprising each utterence, separated by yielding a single None.
            Determines voice activity by ratio of frames in padding_ms. Uses a buffer to include padding_ms prior to being triggered.
            Example: (frame, ..., frame, None, frame, ..., frame, None, ...)
                      |---utterence---|        |---utterence---|
        """
        if frames is None: frames = self.frame_generator()
        num_padding_frames = padding_ms // self.frame_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False

        for frame in frames:
            is_speech = self.vad.is_speech(frame, self.sample_rate)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > ratio * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        yield f
                    ring_buffer.clear()

            else:
                yield frame
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > ratio * ring_buffer.maxlen:
                    triggered = False
                    yield None
                    ring_buffer.clear()

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
        #print(FILE2_ID, FILE_ID)
        gqlSetRelations(FILE2_ID, FILE_ID)
    else:
        print("status_code error: " + str(r.status_code))

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

def listen():
    #user = input("press enter to record INNERVOICEOVER") #waiting for input here, make a specific key?
    print('touch sensor or press space to hear INNERVOICEOVER\n')
    keyboard.wait('space') #for makey
    print("Listening...")

    # Start audio with VAD
    vad_audio = VADAudio(aggressiveness=VAD)
    frames = vad_audio.vad_collector()
    spinner = None
    wav_data = bytearray()

    stream_context = model.setupStream()
    # Stream from microphone to DeepSpeech using VAD
    #if not ARGS.nospinner: spinner = Halo(spinner='line')
    for frame in frames:
        if frame is not None:
            if spinner: spinner.start()
            logging.debug("streaming frame")
            model.feedAudioContent(stream_context, np.frombuffer(frame, np.int16))
            wav_data.extend(frame) #if ARGS.savewav: wav_data.extend(frame)
        else:
            if spinner: spinner.stop()
            logging.debug("end utterence")
            #if ARGS.savewav:
            FILE_NAME = os.path.join(SAVEWAV, datetime.now().strftime("savewav_%Y-%m-%d_%H-%M-%S_%f.wav")) #moved this using FILE_NAME from line below
            vad_audio.write_wav(FILE_NAME, wav_data)
            wav_data = bytearray()
            TEXT = model.finishStream(stream_context)
            print("Recognized: %s" % TEXT)
            global FILE_ID
            FILE_ID = uploadFile(FILE_NAME) #added this
            gqlMutateText(FILE_ID, TEXT)
            lyreBird(FILE_ID, TEXT)
            #stream_context = model.setupStream()
            listen()

def main():
    # Load DeepSpeech model
    '''
    if os.path.isdir(MOD):
        model_dir = MOD
        MOD = os.path.join(model_dir, 'output_graph.pb')
        ALPHABET = os.path.join(model_dir, ALPHABET if ALPHABET else 'alphabet.txt')
        LM = os.path.join(model_dir, LM)
        TRIE = os.path.join(model_dir, TRIE)
    '''
    #print('Initializing model...')
    logging.info("model: %s", MOD)
    logging.info("alphabet: %s", ALPHABET)
    global model
    model = deepspeech.Model(MOD, N_FEATURES, N_CONTEXT, ALPHABET, BEAM_WIDTH)
    if LM and TRIE:
        logging.info("LM: %s", LM)
        logging.info("TRIE: %s", TRIE)
        model.enableDecoderWithLM(ALPHABET, LM, TRIE, LM_ALPHA, LM_BETA)
    listen()


if __name__ == '__main__':
    BEAM_WIDTH = 500 #Beam width used in the CTC decoder when building candidate transcriptions. Default: 500
    LM_ALPHA = 0.75 #The alpha hyperparameter of the CTC decoder. Language Model weight. Default: 0.75
    LM_BETA = 1.85 #The beta hyperparameter of the CTC decoder. Word insertion bonus. Default: 1.85
    N_FEATURES = 26 #Number of MFCC features to use. Default: 26
    N_CONTEXT = 9 #Size of the context window used for producing timesteps in the input vector. Default: 9
    MOD = 'models/output_graph.pbmm'
    ALPHABET = 'models/alphabet.txt'
    LM = 'models/lm.binary'
    TRIE = 'models/trie'
    VAD = 3 #int 0-3 higher is more aggressive filters out more non-speech
    SAVEWAV = 'STTaudio' #folder name for files

    if SAVEWAV: os.makedirs(SAVEWAV, exist_ok=True)
    main()
