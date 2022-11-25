# ########################################################################
# #################### Python Imports ####################################
# ########################################################################

from io import BytesIO
from PIL import Image
from sys import exit
from os import listdir,\
    path
from subprocess import call

# ########################################################################
# #################### METHODS DEFINITION ################################
# ########################################################################

class pp():
    def __init__(self):
        self.picture_target_mb = float(input('picture target (MB):_'))

    def do(self):

        # ratio used in each iteration, the lower this number is,
        # more time will be required for the conversion but the output size will be closer to the target
        image_ratio = 1.1

        for input_entry in listdir('input'):
            if input_entry != 'delete-me' and\
                    any([input_entry.endswith(_) for _ in ['JPG', 'jpg', 'jpeg',
                                                           'PNG', 'png']]):
                foo = Image.open(path.join("input", input_entry))
                size = foo.size
                x_size = size[0]
                y_size = size[1]

                x_size = int(x_size / image_ratio)
                y_size = int(y_size / image_ratio)

                foo = foo.resize((x_size, y_size), Image.Resampling.LANCZOS)
                # convert to RGB because a PNG input file would have an alpha channel and an exception would be thrown when the image was to be saved
                foo = foo.convert("RGB")
                file_bytes = BytesIO()
                foo.save(file_bytes, optimize=True, quality=95, format='jpeg')
                size_in_bites = file_bytes.tell()

                while size_in_bites / 1024 / 1024 > self.picture_target_mb:
                    x_size = int(x_size / image_ratio)
                    y_size = int(y_size / image_ratio)

                    foo = foo.resize((x_size, y_size), Image.Resampling.LANCZOS)
                    file_bytes = BytesIO()
                    foo.save(file_bytes, optimize=True, quality=95, format='jpeg')
                    size_in_bites = file_bytes.tell()

                foo.save(path.join("converted", input_entry.rsplit('.', 1)[0] + '.jpeg'), optimize=True, quality=95, format='jpeg')

                print("Picture converted: ", input_entry)

class vv():
    def do(self):
        for input_entry in listdir('input'):
            if input_entry != 'delete-me':
                print(f"Converting video: {input_entry} ...")
                call(['HandBrakeCLI.exe',
                      '-i' + path.abspath((path.join('input', input_entry))),
                      '-o' + r'converted\\' + str(input_entry.rsplit('.', 1)[0]) + '.mp4',
                      '-w 1280', '-l 720',
                      '-q 23'], shell=True)

class ava():
    def do(self):
        for input_entry in listdir('input'):
            if input_entry != 'delete-me':
                print(f"Converting {input_entry} to mp3 ...")
                call((f"ffmpeg.exe -i \"{path.join('input', input_entry)}\""
                      f" -acodec libmp3lame -q:a 3 -vn \"{path.join('converted', input_entry)}.mp3\""))

class ava_cut():
    def __init__(self):

        self.tasks = {}
        for input_entry in listdir('input'):
            if input_entry != 'delete-me':
                self.tasks[input_entry] = {'start': input('Start of {}:_'.format(input_entry)),
                                           'end': input('End of {}:_'.format(input_entry))}

    def do(self):
        for task, description in self.tasks.items():
            print(f"Converting {task} ...")

            call(f"ffmpeg.exe -ss {description['start']}"
                 f" -i \"{path.join('input', task)}\""
                 f" -c copy -t {description['end']} \"{path.join('converted', task)}\"")

class ava_mux():
    def __init__(self):
        print('Scanning input for relevant video and audio files ...')
        all_filenames_no_ext = set([path.basename(_).rsplit('.', 1)[0] for _ in listdir('input')])
        all_filenames_no_ext.remove('delete-me')

        print_format = '\n'.join(all_filenames_no_ext)
        print(f"Found the following input files:\n{print_format}")

        print(f"Searching for video-audio pairs ...")
        self.all_pairs = []
        all_filenames = listdir('input')
        for input_entry in all_filenames_no_ext:
            current_pair = {'filename_no_ext': input_entry}
            for audio_ext in ['m4a']:
                if f"{input_entry}.{audio_ext}" in all_filenames:
                    current_pair['audio'] = f"{input_entry}.{audio_ext}"
                    break
            for video_ext in ['webm', 'mp4']:
                if f"{input_entry}.{video_ext}" in all_filenames:
                    current_pair['video'] = f"{input_entry}.{video_ext}"
                    break

            if not all(['audio' in current_pair.keys(),
                        'video' in current_pair.keys()])    :
                exit(f"This entry does not have a valid video AND audio input: {input_entry}")

            self.all_pairs.append(current_pair)

        print('Successfully built the list of audio-video pairs.')

    def do(self):
        for pair in self.all_pairs:
            f"asda"" "
            call(f"ffmpeg -i \"{path.join('input', pair['video'])}\""
                 f" -i \"{path.join('input', pair['audio'])}\""
                 f" -c copy \"{path.join('converted', pair['filename_no_ext'])}.mkv\"")

# ########################################################################
# #################### MAIN SCRIPT #######################################
# ########################################################################

if __name__ == '__main__': #don`t start the method if called from another script

    if not all([path.isfile('ffmpeg.exe'),
                path.isfile('HandBrakeCLI.exe')]):
        exit('Conversion binaries missing (ffmpeg.exe, HandBrakeCLI.exe). Download them from here: https://1drv.ms/u/s!AiDIGJzt-XdW8v1jW0sCNvobl8_seg?e=c9h90Y')

    # get the required actions
    action = input('What would you like to do?'
                    '\n\tConvert picture -> picture: pp'
                    '\n\tConvert video -> video: vv'
                    '\n\tConvert audio | video -> audio: ava'
                    '\n\tCut audio | video: ava_cut'
                    '\n\tMux audio | video: ava_mux'
                    '\n\t_')
    if action not in ['pp',
                      'vv',
                      'ava',
                      'ava_cut',
                      'ava_mux']:
        exit(f"Your action {action} is not in preconfigured list of actions !")

    globals()[action]().do()