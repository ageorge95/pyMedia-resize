from io import BytesIO
from PIL import Image
from sys import exit
from os import (listdir,
                path,
                makedirs)
from subprocess import (call,
                        check_output)
from multiprocessing import (Pool,
                             cpu_count)

VALID_EXTENSIONS = {
    'picture': ['.jpg', '.jpeg', '.png'],
    'video': ['.mp4', '.avi', '.webm', '.mkv'],
    'audio': ['.mp3', '.m4a']
}


# ########################################################################
# #################### METHODS DEFINITION ################################
# ########################################################################

class pp:
    def __init__(self):
        self.picture_target_mb = float(input('Picture target (MB): '))
        self.input_dir = 'input'
        self.output_dir = 'converted'
        makedirs(self.output_dir, exist_ok=True)

    def process_image(self, args):
        input_entry, picture_target_mb, input_dir, output_dir = args
        image_ratio = 1.1
        try:
            input_path = path.join(input_dir, input_entry)
            original = Image.open(input_path).convert('RGB')

            x_size, y_size = original.size
            current_image = original.resize(
                (int(x_size / image_ratio), int(y_size / image_ratio)),
                Image.Resampling.LANCZOS
            )

            file_bytes = BytesIO()
            current_image.save(file_bytes, optimize=True, quality=95, format='jpeg')
            size_in_bytes = file_bytes.tell()

            if size_in_bytes / 1024 / 1024 <= picture_target_mb:
                output_path = path.join(
                    output_dir,
                    input_entry.rsplit('.', 1)[0] + '.jpeg'
                )
                current_image.save(output_path, optimize=True, quality=95, format='jpeg')
                return f"Picture converted (no resize loop needed): {input_entry}"

            resized = current_image
            while size_in_bytes / 1024 / 1024 > picture_target_mb:
                x_size = int(x_size / image_ratio)
                y_size = int(y_size / image_ratio)
                resized = original.resize((x_size, y_size), Image.Resampling.LANCZOS)
                file_bytes = BytesIO()
                resized.save(file_bytes, optimize=True, quality=95, format='jpeg')
                size_in_bytes = file_bytes.tell()

            output_path = path.join(
                output_dir,
                input_entry.rsplit('.', 1)[0] + '.jpeg'
            )
            resized.save(output_path, optimize=True, quality=95, format='jpeg')
            return f"Picture converted: {input_entry}"

        except Exception as e:
            return f"Error processing {input_entry}: {e}"

    def on_success(self, message):
        # Called as each job finishes
        print(message)

    def do(self):
        entries = [
            entry for entry in listdir(self.input_dir)
            if entry != 'delete-me' and entry.lower().endswith(tuple(VALID_EXTENSIONS['picture']))
        ]

        args = [
            (entry, self.picture_target_mb, self.input_dir, self.output_dir)
            for entry in entries
        ]

        with Pool(processes=cpu_count()) as pool:
            for arg in args:
                pool.apply_async(
                    self.process_image,
                    args=(arg,),
                    callback=self.on_success
                )

            pool.close()
            pool.join()

class vv:
    def do(self):
        for input_entry in listdir('input'):
            if input_entry != 'delete-me':
                print(f"Converting video: {input_entry} ...")
                call(['HandBrakeCLI.exe',
                      '-i' + path.abspath((path.join('input', input_entry))),
                      '-o' + r'converted\\' + str(input_entry.rsplit('.', 1)[0]) + '.mp4',
                      '-w 1280', '-l 720',
                      '-q 23'], shell=True)

class ava:
    def do(self):
        for input_entry in listdir('input'):
            if input_entry != 'delete-me':
                print(f"Converting {input_entry} to mp3 ...")
                call((f"ffmpeg.exe -i \"{path.join('input', input_entry)}\""
                      f" -acodec libmp3lame -q:a 3 -vn \"{path.join('converted', input_entry)}.mp3\""))

class ava_cut:
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

class ava_mux:
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
            for audio_ext in VALID_EXTENSIONS['audio']:
                if f"{input_entry}{audio_ext}" in all_filenames:
                    current_pair['audio'] = f"{input_entry}.{audio_ext}"
                    break
            for video_ext in VALID_EXTENSIONS['video']:
                if f"{input_entry}{video_ext}" in all_filenames:
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

class vv_join:
    def __init__(self):
        pass

    def do(self):

        video_filename_to_join = []
        for input_entry in listdir('input'):
            if input_entry != 'delete-me' and\
                    any([input_entry.lower().endswith(_) for _ in VALID_EXTENSIONS['video']]):
                video_filename_to_join.append(input_entry)

        print(f'Found {len(video_filename_to_join)} valid input files')

        if video_filename_to_join:
            with open('filelist.txt', 'w', encoding='utf-8') as output_file_handle:
                output_file_handle.writelines('\n'.join([f'file \'{path.join('input', _)}\'' for _ in video_filename_to_join]))

            call(['ffmpeg',
                  '-f', 'concat',
                  '-safe', '0',
                  '-i', 'filelist.txt',
                  '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
                  '-c:a', 'aac', '-b:a', '192k',
                  r'converted\output.mp4']
                 )

# ########################################################################
# #################### MAIN SCRIPT #######################################
# ########################################################################

if __name__ == '__main__': #don`t start the method if called from another script

    if not all([check_output('where ffmpeg.exe').decode('utf-8').strip().endswith('.exe'),
                check_output('where HandBrakeCLI.exe').decode('utf-8').strip().endswith('.exe')]):
        exit('Conversion binaries missing (ffmpeg.exe, HandBrakeCLI.exe).')

    # get the required actions
    action = input('What would you like to do?'
                    '\n\tConvert picture -> picture: pp'
                    '\n\tConvert video -> video: vv'
                    '\n\tConvert audio | video -> audio: ava'
                    '\n\tCut audio | video: ava_cut'
                    '\n\tMux audio | video: ava_mux'
                    '\n\tJoin video | video: vv_join'
                    '\n\t_')
    if action not in ['pp',
                      'vv',
                      'ava',
                      'ava_cut',
                      'ava_mux',
                      'vv_join']:
        exit(f"Your action {action} is not in preconfigured list of actions !")

    globals()[action]().do()