import json
import math
import os
import time
from youtube_transcript_api import YouTubeTranscriptApi
# from googleapiclient.discovery import build
from pytube.cli import on_progress
from pytube import YouTube
from pytube import Channel
from pytube import Playlist
from pytube import exceptions


# YOUTUBE DOCUMENTATION: https://developers.google.com/youtube/v3/docs/captions/list

SEARCH_TERM = ""
MAX_RESULTS = 50
isEfficientSearch = False

def completed(a, b):
    completed = '\nDownload Completed!\n'
    size = f'File Size: {str(a.filesize/1000000)}Mb\n'

    typeLine(f'{completed} {size}')
    print('\n')
    print('-' * 60)
    print('\n')
    time.sleep(5)

def typeLine(text):
    for character in text:
        time.sleep(.003)
        print(character, end='', flush=True)
    print("\n")

def FileExists(directory, name, extension):
    location = f"{directory}/{name}.{extension}"
    return os.path.exists(location)

def FolderExists(directory, name):
    location = f"{directory}/{name}"
    return os.path.exists(location)    

def MakeFolder(directory, name):
    if(not FolderExists(directory, name)):
        location = f"{directory}/{name}"
        os.makedirs(location)

def getChannel(url):
    url = url.replace('@', 'c/')
    channel = Channel(url)
    typeLine(f"Channel found: {channel.channel_name}")
    return channel

def getPlaylist(url):
    playlist = Playlist(url)
    typeLine(f"Playlist Found: {playlist.title}")
    return playlist

def getVideoFromURL(url):
    video = YouTube(url, on_progress_callback=on_progress, on_complete_callback=completed)
    return video

def getVideoFromID(videoId):
    url = f"https://www.youtube.com/watch?v={videoId}"
    return getVideoFromURL(url)

def getVideoIDFromURL(url):
    trimmedURL = url.split("v=")[1]
    return trimmedURL.split("&")[0]

def TranscribePlaylist(playlist):
    input(f"Transcribing playlist '{playlist.title}', contains {len(playlist)} videos - Press Enter to confirm.")
    for url in playlist.video_urls:
        try:
            videoId = getVideoIDFromURL(url)
            MakeFolder(f"Transcripts/{playlist.owner}", playlist.title)
            CreateTranscriptFile(playlist.owner, playlist.title, videoId, GetTranscript(videoId))
            
            if(SEARCH_TERM != ""):
                MakeFolder("Searches", playlist.title)
                ReadTranscript(playlist.owner, playlist.title, videoId)
        except exceptions.PytubeError as e:
            print(f"\n PYTUBE ERROR ON - {videoId}, inside TranscribePlaylist - {e} \n")
            continue
        except Exception as e:
            if("Subtitles are disabled" in str(e)):
                print(f"Unable to Transcribe https://www.youtube.com/watch?v={videoId}. Subtitles are disabled!")
            elif("following languages" in str(e)):
                print(f"Unable to Transcribe https://www.youtube.com/watch?v={videoId}. Subtitles not available in english!")
            else:
                print(f"{videoId} FAILED, here's why: {e}")
            continue

def TranscribeChannel(channel):
    input(f"Transcribing channel '{channel.channel_name}', contains {len(channel)} videos - Press Enter to confirm.")
    for url in channel.video_urls:
        try:
            videoId = getVideoIDFromURL(url)
            MakeFolder(f"Transcripts/{channel.channel_name}", "Videos")
            CreateTranscriptFile(channel.channel_name, "Videos", videoId, GetTranscript(videoId))
            
            if(SEARCH_TERM != ""):
                MakeFolder("Searches", channel.channel_name)
                ReadTranscript(channel.channel_name, "Videos", videoId)
        except exceptions.PytubeError as e:
            print(f"\n PYTUBE ERROR ON - {videoId}, inside TranscribeChannel - {e} \n")
            continue
        except Exception as e:
            if("Subtitles are disabled" in str(e)):
                print(f"Unable to Transcribe https://www.youtube.com/watch?v={videoId}. Subtitles are disabled!")
            else:
                print(f"{videoId} FAILED, here's why: {e}")
            continue

def GetTranscript(videoId):
    return YouTubeTranscriptApi.get_transcript(videoId)

def CreateTranscriptFile(author, folder, videoId, transcript):
    if(not FileExists(f"Transcripts/{author}/{folder}", videoId, "json")):
        with open(f"Transcripts/{author}/{folder}/{videoId}.json", 'w') as outFile:
            json.dump(transcript, outFile, indent=4)   # Create a json file with those videos for future use
            print(f"Transcript created: {videoId}.json")

def ReadTranscriptFromJson(filePath, file):
    with open(filePath, 'r') as openFile:
        channelName = filePath.split("/")[1].split("\\")[0]
        transcript = json.load(openFile)
        writeHeader = True
        video = None
        videoId = file.split(".")[0]
        for item in transcript:                                                        
            if(SEARCH_TERM.lower() in item['text'].lower()):
                if(isEfficientSearch):                        
                    PrintWithoutDetails(videoId, channelName, item, writeHeader)
                    writeHeader = False
                else:
                    try:
                        if(video == None):
                            video = getVideoFromID(videoId)

                        PrintWithDetails(video, videoId, item, writeHeader)
                        writeHeader = False
                    except Exception as e:
                        print(f"Failure when getting video: {e}")

def PrintWithoutDetails(videoId, channelName, item, writeHeader):
    print(f"{SEARCH_TERM} FOUND ON VIDEO WITH ID: {videoId}")
    with open(f"Searches/{channelName}/{SEARCH_TERM}.txt", 'a') as file:
        if(writeHeader):
            file.write("\n")
            file.write(f"--------------------")
            file.write("\n")

        file.write(f"> {item['text']} - https://www.youtube.com/watch?v={videoId}&t={math.trunc(item['start'])}s \n")

def PrintWithDetails(video, videoId, item, writeHeader):        
    print(f"{SEARCH_TERM} FOUND IN: {video.title}")
    with open(f"Searches/{video.author}/{SEARCH_TERM}.txt", 'a') as file:
        if(writeHeader):
            file.write("\n")
            file.write(f"----------[{video.publish_date.month}-{video.publish_date.day}-{video.publish_date.year}] [{video.title}]----------")
            file.write("\n")

        file.write(f"> {item['text']} - https://www.youtube.com/watch?v={videoId}&t={math.trunc(item['start'])}s \n")

def ReadTranscript(author, folder, videoId):
    if(FileExists(f"Transcripts/{author}/{folder}", videoId, "json")):
       print("FILE ALREADY EXISTS RETURNING")
       return

    with open(f"Transcripts/{author}/{folder}/{videoId}.json", 'r') as openFile:
        transcript = json.load(openFile)
        writeHeader = True
        video = None
        for item in transcript:                                                        
            if(SEARCH_TERM.lower() in item['text'].lower()):
                if(video == None and not isEfficientSearch):
                    try:
                        video = getVideoFromID(videoId)
                    except Exception as e:
                        print(f"Failure when getting video: {e}")
                        continue
                
                print(f"{SEARCH_TERM} FOUND IN: {video.title}")
                with open(f"Searches/{video.author}/{SEARCH_TERM}.txt", 'a') as file:
                    if(writeHeader):
                        file.write("\n")
                        file.write(f"----------[{video.publish_date.month}-{video.publish_date.day}-{video.publish_date.year}] [{video.title}]----------")
                        file.write("\n")
                        writeHeader = False

                    file.write(f"> {item['text']} - https://www.youtube.com/watch?v={videoId}&t={math.trunc(item['start'])}s \n")

SEARCH_TERM = input("Enter Search Term: ")

if(SEARCH_TERM == ""):
    typeLine("No Search Term Entered, just transcribing.")

url = input("Enter URL: ")

if('@' in url or '/c/' in url):
    channel = getChannel(url)
    TranscribeChannel(channel)
elif(url.__contains__('list=')):
    playlist = getPlaylist(url)
    TranscribePlaylist(playlist)
elif(url.__contains__('v=')):
    # THIS IS CURRENTLY BROKEN
    video = getVideoFromURL(url)
    GetTranscript(video)
elif("all" in url.lower()):
    for root, dirs, files in os.walk("Transcripts/"):
        for file in files:
            if file.endswith(".json"):
                filePath = os.path.join(root, file)
                channelName = filePath.split("/")[1].split("\\")[0]
                MakeFolder("Searches", channelName)
                ReadTranscriptFromJson(filePath, file)
else:
    MakeFolder("Searches", url)
    for root, dirs, files in os.walk(f"Transcripts/{url}/"):
        for file in files:
            if file.endswith(".json"):
                ReadTranscriptFromJson(os.path.join(root, file), file)