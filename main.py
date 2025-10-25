import math
from io import BytesIO
from PIL import Image
from pillow_heif import register_heif_opener
from sys import exit
from os import (listdir,
                path,
                makedirs)
from subprocess import (call,
                        check_output)
from multiprocessing import (Pool,
                             cpu_count)
from shutil import copyfile

VALID_EXTENSIONS = {
    'picture': ('.jpg', '.jpeg', '.png', '.heic'),
    'video': ('.mp4', '.avi', '.webm', '.mkv'),
    'audio': ('.mp3', '.m4a')
}

# ########################################################################
# #################### Additional PREREQUISITES ##########################
# ########################################################################
register_heif_opener()

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
        target_bytes = picture_target_mb * 1024 * 1024

        try:
            input_path = path.join(input_dir, input_entry)
            output_path = path.join(output_dir, input_entry.rsplit('.', 1)[0] + '.webp')

            original_size = path.getsize(input_path)
            if original_size <= target_bytes and input_path.lower().endswith('.webp'):
                copyfile(input_path, output_path)
                return f"Already under target: {input_entry}"

            with Image.open(input_path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')

                original_width, original_height = img.size

                # Strategy: Prefer quality reduction over resolution reduction
                # Try full resolution with decreasing quality first
                best_approach = None
                best_data = None
                best_size = 0
                best_metadata = ""
                best_quality_value = 0  # Track quality as numeric value for scoring

                # Approach 1: Maximum quality at full resolution
                for quality in range(95, 49, -5):  # 95 down to 50
                    buffer = BytesIO()
                    img.save(buffer, format='WEBP', quality=quality, method=4)
                    current_size = buffer.tell()

                    if current_size <= target_bytes:
                        utilization = current_size / target_bytes

                        # If we're using a good portion of the budget, take it
                        if utilization > 0.7 or quality == 50:  # Or we've hit minimum acceptable quality
                            best_approach = "full_res"
                            best_data = buffer.getvalue()
                            best_size = current_size
                            best_metadata = f"Q{quality}"
                            best_quality_value = quality
                            break

                # Approach 2: If full resolution doesn't work well, try minimal resizing with high quality
                if best_data is None or best_size < target_bytes * 0.5:
                    # We have lots of space or full res didn't work, try smart resizing
                    test_scenarios = [
                        (0.95, 90), (0.9, 85), (0.85, 85), (0.8, 80),
                        (0.75, 80), (0.7, 75), (0.6, 75), (0.5, 70)
                    ]

                    for ratio, quality in test_scenarios:
                        new_width = max(100, int(original_width * ratio))
                        new_height = max(100, int(original_height * ratio))

                        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        buffer = BytesIO()
                        resized.save(buffer, format='WEBP', quality=quality, method=4)
                        current_size = buffer.tell()

                        if current_size <= target_bytes:
                            utilization = current_size / target_bytes
                            current_score = utilization * quality  # Simple quality-score metric

                            # Calculate best_score using the stored quality value
                            best_utilization = best_size / target_bytes if best_size > 0 else 0
                            best_score = best_utilization * best_quality_value

                            # Prefer this if it's significantly better or we have no solution
                            if current_score > best_score * 1.1 or best_data is None:
                                best_approach = "resized"
                                best_data = buffer.getvalue()
                                best_size = current_size
                                best_metadata = f"Q{quality}@{ratio:.0%}"
                                best_quality_value = quality

                                if utilization > 0.85:  # Good budget utilization
                                    break

                # Save the best result
                if best_data:
                    with open(output_path, 'wb') as f:
                        f.write(best_data)
                    size_mb = best_size / 1024 / 1024
                    utilization_pct = (best_size / target_bytes) * 100
                    return f"WebP ({best_approach}): {input_entry} ({size_mb:.2f}MB, {best_metadata}, {utilization_pct:.1f}% budget)"
                else:
                    # Ultimate fallback - prioritize resolution
                    new_width = max(800, int(original_width * 0.7))
                    new_height = max(600, int(original_height * 0.7))
                    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    resized.save(output_path, format='WEBP', quality=80, method=4)
                    return f"WebP fallback: {input_entry}"

        except Exception as e:
            return f"Error processing {input_entry}: {e}"

    def on_success(self, message):
        # Called as each job finishes
        print(message)

    def do(self):
        entries = [
            entry for entry in listdir(self.input_dir)
            if entry != 'delete-me' and entry.lower().endswith(VALID_EXTENSIONS['picture'])
        ]

        args = [
            (entry, self.picture_target_mb, self.input_dir, self.output_dir)
            for entry in entries
        ]

        # Use fewer processes for memory efficiency with WebP
        num_processes = max(2, cpu_count() - 1)

        with Pool(processes=num_processes) as pool:
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
        # Ask user for mode
        mode = input("Choose mode: Default [D], Portrait [P], Landscape [L]: ").strip().upper()

        for input_entry in listdir('input'):
            if input_entry != 'delete-me':
                # Set HandBrake arguments based on choice
                if mode == 'P':
                    max_width, max_height = 720, 1280
                elif mode == 'L':
                    max_width, max_height = 1280, 720
                else:  # Default
                    max_width, max_height = 1280, 720  # or any default you prefer

                print(f"Converting video: {input_entry} ... (mode={mode})")

                call([
                    'HandBrakeCLI.exe',
                    '-i', path.abspath(path.join('input', input_entry)),
                    '-o', path.join('converted', f"{input_entry.rsplit('.', 1)[0]}.mp4"),
                    '-e', 'nvenc_h265',  # Use NVIDIA H.265 encoder
                    '--encoder-preset', 'p4',  # Quality preset (p1-p7, p4=default)
                    '--encoder-tune', 'hq',  # High quality tuning
                    '--quality', '23',  # Lower number = higher quality (18-32 typical)
                    f'--maxWidth={max_width}',
                    f'--maxHeight={max_height}',
                    '--keep-display-aspect'
                ], shell=True)

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