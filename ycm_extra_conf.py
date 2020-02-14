import subprocess
import re
import json
import os

"""
Work in progress to try use Vim's YouCompleteMe plugin .ymc_extra_conf.py file
to use compile_commands.json file with Windows paths. Behind the scenes paths
are converted using WSL tool called wslpath on the fly.

NOTE: Not working yet.
"""

COMPILE_COMMANDS_JSON_FILENAME = 'win_compile_commands.json'
SOURCE_EXTENSIONS = ['.cpp', '.cxx', '.cc', '.c', '.m', '.mm']
path_cache = {}

def is_header_file(filename):
    extension = os.path.splitext(filename)[1]
    return extension in ['.h', '.hxx', '.hpp', '.hh']


def find_corresponding_source_file(filename):
    if is_header_file(filename):
        basename = os.path.splitext(filename)[0]
        for extension in SOURCE_EXTENSIONS:
            replacement_file = basename + extension
            if os.path.exists(replacement_file):
                return replacement_file
    return filename


def read_compile_commands(filename):
    database = None
    with open(COMPILE_COMMANDS_JSON_FILENAME, 'r') as compile_commands:
        database = json.loads(compile_commands.read())
    result = {}
    for data in database:
        filename = wsl_path(data['file'])
        result[filename] = data['command']
    return result


def remove_compile_flags(command):
    o_pattern = r'-o\s*[\w\/\.]+'
    c_pattern = r'-c\s*[\w\/\.]+'
    command = re.sub(o_pattern, '', command)
    command = re.sub(c_pattern, '', command)
    return command


def convert_drive_paths(path):
    drive_path = r'(?:(?<=[I| |"])|^)(\w+:[\\\/]+)'
    return re.sub(drive_path, replace_path, path)


def convert_slashes(path):
    slash_pattern = r'(?<=\w)(\\+)(?=\w)'
    return re.sub(slash_pattern, '/', path)


def convert_paths(string):
    string = convert_slashes(string)
    return convert_drive_paths(string)


def replace_path(path):
    return wsl_path(path.group(1))


def wsl_path(windows_path):
    wsl_path = path_cache.get(windows_path)
    if not wsl_path:
        completed_process = subprocess.run(['wslpath', '-a', windows_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        wsl_path = completed_process.stdout.decode('ascii').strip()
        path_cache[windows_path] = wsl_path
    return wsl_path


def Settings(**kwargs):
    filename = kwargs.get('filename', '')
    filename = find_corresponding_source_file(filename)
    if filename in database:
        return {
            'flags': convert_paths(remove_compile_flags(database[filename])).split(' '),
            'override_filename': filename
        }
    print('no flags for {0}'.format(filename))
    return {}


database = read_compile_commands(COMPILE_COMMANDS_JSON_FILENAME)
print('done')

if __name__ == '__main__':
    Settings()
