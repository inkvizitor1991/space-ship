import os
from os import listdir


def read_rocket_frame(frames_folder):
    files_contents = []
    for frame in listdir(frames_folder):
        with open(os.path.join(f'{frames_folder}{frame}')) as rocket_frame:
            files_contents.append(rocket_frame.read())
    return files_contents