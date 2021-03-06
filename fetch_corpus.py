import os, tempfile, urllib, zipfile, shutil, json
import subprocess32 as subprocess
from contextlib import contextmanager

WORKING_DIR = os.path.dirname(os.path.realpath(__file__))
CORPUS_INFO = None
with open(os.path.join(WORKING_DIR, 'corpus.json')) as f:
  CORPUS_INFO = json.loads(f.read())
CORPUS_DIR = os.path.join(WORKING_DIR, "corpus")

LOG_FILE = None

def write_log(line):
  global LOG_FILE
  if LOG_FILE:
    LOG_FILE.write(line)
    LOG_FILE.flush()

def run_cmd(cmd):
  stats = {'output': ''}

  write_log("Running command '{}'\n".format(' '.join(cmd)))

  process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  for line in iter(process.stdout.readline, b''):
    stats['output'] = stats['output'] + line
    write_log(line)
  process.stdout.close()
  process.wait()

  if process.returncode != 0:
    print "Error running command '{}', check corpus.log for details.".format(' '.join(cmd))

  write_log("\n\n")

  return stats

@contextmanager
def cd(newdir):
  prevdir = os.getcwd()
  os.chdir(os.path.expanduser(newdir))
  try:
    yield
  finally:
    os.chdir(prevdir)

def git_update(project):
  if project['git-ref'] not in run_cmd(['git', 'rev-parse', 'HEAD'])['output']:
    print "Checking out git ref %s." % project['git-ref']
    run_cmd(['git', 'fetch'])
    run_cmd(['git', 'reset', '--hard'])
    run_cmd(['git', 'checkout', project['git-ref']])

def download_project(project):
  if not os.path.isdir(project['name']):
    if 'git-url' in project:
      print "Downloading %s" % project['name']
      run_cmd(['git', 'clone',
                project['git-url'],
                project['name']])
  else:
    print "Already downloaded %s." % (project['name'])

def update_project(project):
  with cd(project['name']):
    if 'git-url' in project:
      git_update(project)

def fetch_corpus():
  global LOG_FILE
  LOG_FILE = open(os.path.join(WORKING_DIR, 'corpus.log'), 'w')

  with cd(CORPUS_DIR):
    for project in CORPUS_INFO['projects'].values():
      download_project(project)

      if os.path.isdir(project['name']):
        update_project(project)
      else:
        print "{} not available.".format(project['name'])

  LOG_FILE.close()
  LOG_FILE = None

if __name__ == "__main__":
  fetch_corpus()
