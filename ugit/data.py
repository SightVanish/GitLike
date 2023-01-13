import os

GIT_DIR = '.ugit'

def init():
    os.makedirs(GIT_DIR)
    print('Initialized empty ugit repository in %s' % os.path.join(os.getcwd(), GIT_DIR))