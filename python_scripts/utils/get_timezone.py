import os
import os.path
import sys 

def main(argv):
  tzname = os.environ.get('TZ')
  if tzname:
    print(tzname)
  elif os.path.exists('/etc/timezone'):
    print(file('/etc/timezone').read())
  else:
    sys.exit(1)

if __name__ == '__main__':
  main(sys.argv)