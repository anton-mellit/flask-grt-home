import sys
sys.stdout = sys.stderr
print('Starting WSGI')
import os
print('CWD:', os.getcwd())
print('ENV:', os.environ)
import locale
print('ENCODING:', locale.getpreferredencoding())
from run import app as application

