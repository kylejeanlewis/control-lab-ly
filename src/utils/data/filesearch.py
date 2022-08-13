import os

def get_basedir(suffix=''):
    '''
    Get the root directory of machine
    - suffix: deeper path where the data files and logs can be found (i.e. Teams sync folder)

    Returns: full path of base directory (str)
    '''
    curr_dir = os.getcwd()
    print(curr_dir)
    n = 0
    user_dir = ''
    for s in curr_dir:
        if s == '\\':
            n += 1
        if n == 3:
            break
        user_dir = user_dir + s
    return user_dir + suffix


def locate_path(main, sub, keyword, dir_type='file', file_ext=''):
    '''
    Locate the paths of interest for a particular keyword and extension type
    - main: main directory or folder
    - sub: sub directory or folder
    - keyword: string to be found in path names (i.e. sample IDs)
    - dir_type: file or folder
    - file_ext: file extension

    Returns: {filename: full_path}
    '''
    sub_dir = main + sub
    paths_of_interest = {}
    for dirpath, dirnames, filenames in os.walk(sub_dir):
        # save path to all subdirectories
        if dir_type == 'folder':
            for subdirname in dirnames:
                if keyword in subdirname:
                    paths_of_interest[subdirname] = os.path.join(dirpath, subdirname)

        # save path to all filenames
        if dir_type == 'file':
            for filename in filenames:
                if keyword in filename and file_ext in filename:
                    paths_of_interest[filename] = os.path.join(dirpath, filename)

        for subdirname, path in paths_of_interest.items():
            try:
                dirnames.remove(subdirname)
            except ValueError:
                pass
    return paths_of_interest


def locate_paths(main, sub, keywords, dir_type='file', file_ext=''):
    '''
    Locate the paths of interest for a few keywords and extension type
    - main: main directory or folder
    - sub: sub directory or folder
    - keywords: strings to be found in path names (i.e. sample IDs)
    - dir_type: file or folder
    - file_ext: file extension

    Returns: {keyword: {filename: full_path}}
    '''
    paths_of_interest = {}
    for keyword in keywords:
        paths = locate_path(main, sub, keyword, dir_type, file_ext)
        if len(paths):
            paths_of_interest[keyword] = paths
        else:
            print('{} not found!'.format(keyword))
    return paths_of_interest

