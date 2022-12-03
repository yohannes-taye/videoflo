#1. Check inside the new directory to find if there are any mp4 files. 
#2. If there are mp4 files: 
#[x]    a. Create folder with appropriate name.
#[ ]    b. Create .card, note, stage files (some of this might not be important).
#[ ]    c. Move the video from the new folder to the newly created folder.
#[ ]    d. Create the trello card with the appropriate title, description and due date. 
#[ ]    e. Generate a thumbnail for the video based on a specified format. 
#[ ]    f. Move the video to the upload list on trello. 

from flo.idea import Idea
from flo.videoflo import VideoFlo
from flo.trello import Trello
from flo.mactag import add_tag
import debugpy 
import os
import configparser
from flo.const import SETTINGSFILE
from flo.idea import Idea
import datetime
#Get list of files in a directory
def get_new_videos(path):
    files = []
    for file in os.listdir(path):
        if file.endswith(".mp4"):
            files.append(file)
    return files

# This method will sort the files into a dictionary with the date as the key and the videos as the value
def get_vids_shot_on_same_date(files):
    #Create a dictionary to hold the files
    files_dict = {}
    #Loop through the files
    for file in files:
        #Split the file name with '_' to get the date
        date = file.split('_')[1]
        #Check if the date is in the dictionary
        if date in files_dict:
            #If it is, append the file to the list
            files_dict[date].append(file)
        else:
            #If it isn't, create a new list with the file in it
            files_dict[date] = [file]
    #Return the dictionary
    return files_dict

def get_new_file_name(video, multiple=False, part=1):
    date = video.split('_')[1]
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]
    date = datetime.date(int(year), int(month), int(day))
    count_down = (datetime.date(2032, 10, 15) - date)
    
    num = (count_down.days) 
    if multiple:
        new_file_name = f"#{num} {year}—{month}—{day} Part{part}.mp4"
    else: 
        new_file_name = f"#{num} {year}—{month}—{day}.mp4"
    return new_file_name


def fix_name_to_upload_format(videos, new_video_path): 
    for date in videos:
        if len(videos[date]) > 1:
            for video in videos[date]:
                new_file_name = get_new_file_name(video, True, videos[date].index(video) + 1)
                os.rename(os.path.join(new_video_path, video), os.path.join(new_video_path, new_file_name))
                print(f"Renamed {video} to {new_file_name}")
        else:
            new_file_name = get_new_file_name(videos[date][0])
            os.rename(os.path.join(new_video_path, videos[date][0]), os.path.join(new_video_path, new_file_name))
            print(f"Renamed {videos[date][0]} to {new_file_name}")
    

def fix_files_format(new_videos, new_video_path): 

    for video in new_videos:
        modified_timestamp = os.path.getmtime(os.path.join(new_video_path, video))
        created_date = datetime.datetime.fromtimestamp(modified_timestamp)
        day = created_date.day if created_date.day > 9 else f"0{created_date.day}"
        month = created_date.month if created_date.month > 9 else f"0{created_date.month}"
        year = created_date.year 
        try:
            new_format = f"VID_{year}{month}{day}_{int(modified_timestamp)}.mp4"
            os.rename(os.path.join(new_video_path, video), os.path.join(new_video_path, new_format))
        except:
            modified_timestamp = int(modified_timestamp)
            modified_timestamp += 1 
            new_format = f"VID_{year}{month}{day}_{int(modified_timestamp)}.mp4"
            os.rename(os.path.join(new_video_path, video), os.path.join(new_video_path, new_format))

def go():
    
    flo = VideoFlo()
    args = flo.get_idea_arguments()

    if args.debug:
        debugpy.listen(5678)
        print("Press play!")
        debugpy.wait_for_client()

    root_directory = flo.config['main']['root_dir']
    full_project_path = os.path.join(root_directory, flo.config[args.channel]['path'])
    new_video_path = os.path.join(full_project_path, flo.config[args.channel]['new_video_dir'])
    new_videos = get_new_videos(new_video_path)

    #Fix format to #VID_20201015_123456.mp4
    fix_files_format(new_videos, new_video_path)

    videos = get_vids_shot_on_same_date(new_videos)

    #Rename the files to upload format
    fix_name_to_upload_format(videos, new_video_path)


        

        #create a new folder with the name of the video
        # #Remove the .mp4 from the name
        # video = video[:-4]
        # new_video_folder = os.path.join(full_project_path, video)
        # print("Creating new folder: " + new_video_folder)
        # os.mkdir(new_video_folder)
        
        # #Move the video from the new_video_path to the new_video_folder
        # print("Moving video: " + video + " to " + new_video_folder)
        # os.rename(os.path.join(new_video_path, video + ".mp4"), os.path.join(new_video_folder, video + ".mp4"))

        # idea = Idea()
        # idea.from_project(project_name=video, channel=flo.config[args.channel]['name'])

    #join to paths
    
    return 
    idea = Idea()
    idea.read_user_input(flo)
    
    trello = Trello()
    if not idea.offline:
        if not trello.lists_exist(['Script'], idea.channel):
            return
        card_id, board_id = trello.make_card(idea)
        if card_id is None or board_id is None:
            return

        if not trello.add_filename_to_card(card_id, board_id, idea.name):
            trello.delete_card(card_id)
            return

    idea_directory = idea.make_directory()
    if idea_directory is None:
        if not idea.offline:
            trello.delete_card(card_id)
        return

    idea.make_files()
    idea.make_directories()

    if not idea.offline:
        trello.save_card(card_id, idea)

    add_tag('Script', idea.path, do_open=True)


go()
