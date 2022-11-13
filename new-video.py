# Create structure for new video idea

from flo.idea import Idea
from flo.videoflo import VideoFlo
from flo.trello import Trello
from flo.mactag import add_tag
import debugpy

def go():
    flo = VideoFlo()
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

debugpy.listen(5678)
print("Press play!")
debugpy.wait_for_client()

go()
