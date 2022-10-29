from cmath import log
import os
from pathlib import Path
from flo.idea import Idea
from flo.video import Video
from flo.trello import Trello
from flo.channel import Channel
from flo.videoflo import VideoFlo
from flo.mactag import update_tag
from datetime import datetime
import debugpy


#TODO: LALI_LOG made changes to the code here
# get the thumbnail file
# def get_thumbnail(path):
#     img_files = []
#     for ext in ['png', 'jpg', 'jpeg']:
#         img_files.extend(path.glob('[!.]*.' + ext))
#     num_img = len(img_files)
#     if num_img != 1:
#         print('FIX: Found {} thumbnail image files'.format(num_img, path))
#         return None
#     return str(img_files[0])
def get_thumbnail(path, name):
    img_files = []
    for ext in ['png', 'jpg', 'jpeg']:
        img_files.extend(path.glob(f'{name}.' + ext))
    num_img = len(img_files)
    if num_img != 1:
        print('FIX: Found {} thumbnail image files'.format(num_img, path))
        return None
    return str(img_files[0])


#TODO: LALI_LOG made changes to the code here
# get the video file
# def get_video_file(path):
#     mov_files = list(path.glob('[!.]*.mov'))
#     num_mov = len(mov_files)
#     if num_mov != 1:
#         print('FIX: Found {} mov files'.format(num_mov, path))
#         return None
#     video_file = Path(mov_files[0]).name
#     return video_file
# get the video file
def get_video_file(path, name):
    mov_files = list(path.glob(f'{name}.mp4'))
    num_mov = len(mov_files)
    if num_mov != 1:
        print('FIX: Found {} mov files'.format(num_mov, path))
        return None
    video_file = Path(mov_files[0]).name
    return video_file

# loop over directories tagged as ready for upload and check for required files
def get_upload_dict(channel, trello, limit):
    print('Checking videos for {}'.format(channel.name))
    uploadable = trello.get_list('Upload', channel)
    upload_dict = {}

    total_upload_size = 0
    count = 0
    warn = 0
    for item in uploadable:
        metadata = {
            'title': item['name'],
            'description': item['desc'],
            'scheduled': item['due'],
            'tags': trello.get_checklist(item['idChecklists'], 'tags'),
            'hashtags': trello.get_checklist(item['idChecklists'], 'hashtags'),
        }
             
        card_id = item['id']
        #TODO: LALI_LOG made changes to the code here
        # path = channel.find_path_for_id(card_id)
        path = channel.find_path_for_name(item['name'])
        if path is None:
            print('Could not find local path for {}'.format(name))
            continue

        path = Path(path)
        project_name = os.path.basename(path)

        idea = Idea()
        idea.from_project(project_name, channel)
        if not idea.exists():
            print('Directory for {} not found'.format(path))
            return

        print('Checking {}'.format(path))
        count = count + 1

        # video thumbnail
        thumbnail = get_thumbnail(path, item['name'])
        warn = warn + 1 if thumbnail is None else warn

        # video file
        video_file = get_video_file(path, item['name'])
        if video_file is None:
            warn = warn + 1
            continue

        video = Video(path, video_file, channel, metadata, thumbnail, idea)
        warn = warn + 1 if not video.check_title() else warn
        warn = warn + 1 if not video.check_description() else warn
        warn = warn + 1 if not video.check_date() else warn
        warn = warn if not video.check_tags() else warn
        warn = warn if not video.check_hashtags() else warn
        warn = warn + 1 if not video.check_thumbnail() else warn
        video.format_description()

        total_upload_size += video.video_size

        upload_dict[card_id] = video

        if count == limit:
            break


    total_upload_gb = round(total_upload_size / (1024 * 1024 * 1024), 3)
    print('Total size of upload: {} GB'.format(total_upload_gb))

    if warn == 0 and count > 0:
        return upload_dict
    elif count == 0:
        print('No videos ready for upload')
    else:
        print('{} problem(s) found'.format(warn))

    return {}

# prepare uploads
def do_uploads(upload_dict):
    upload_count = 0
    upload_total = len(upload_dict)
    start_time = datetime.now()
    for card_id, video in upload_dict.items():
        file_size_gb = round(video.video_size / 1024 / 1024 / 1024, 2)
        print('Starting upload for {} ({} GB)'.format(video.file, file_size_gb))
        video_id = video.upload()
        if video_id is not None:
            upload_count += 1
            update_tag('Scheduled', video.path)
            #TODO: LALI_LOG fix this
            # trello = Trello()
            # trello.move_card(video.idea, 'Scheduled')
            # trello.attach_links_to_card(card_id, video_id)
    duration = datetime.now() - start_time
    print('Uploaded {}/{} videos in {}'.format(upload_count, upload_total, duration))

def go():
    flo = VideoFlo()
    args = flo.get_upload_arguments()
    channel = Channel(flo.config, args.channel)
    dry_run = args.dry_run
    limit = args.limit if args.limit > 0 else 0

    if limit > 0:
        print("Limiting to {} video upload(s)".format(limit))

    trello = Trello()
    if not trello.lists_exist(['Upload', 'Scheduled'], channel):
        return

    upload_dict = get_upload_dict(channel, trello, limit)
    if not dry_run and len(upload_dict) > 0:
        do_uploads(upload_dict)

debugpy.listen(5678)
print("Press play!")
# debugpy.wait_for_client()
go()
