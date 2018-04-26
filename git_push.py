import sys
from subprocess import *

""" Adds changes, commits them and finally pushes to the remote repo at GitHub. """
# sequence for staging, committing and pushing to remote repo:
# git add . 							--> stage changes
# git commit -m 'Change Description'	--> commit changes
# git push origin master				--> push to repo

# returns a list of separated lines from git status output
git_out = check_output('git status -s', shell=True).splitlines()
# filter out items starting with '??' and remove ' M' prefix (standing for tracked modifications)
git_filtered = [x.lstrip(' M') for x in git_out if not x.startswith('??')]

if len(git_filtered) == 0:
	print "No tracked files were modified! Exiting ..."
	sys.exit()

print "Following file(s) were modified and NOT pushed:"
for n,f in enumerate(git_filtered):
	if not f.startswith('??'):
		print n + 1, f

permission = raw_input("Push these file(s) to GitHub (y/n)? ")
permission.lower()

if permission == "y":
	for f in git_filtered:
		print "\nStaging changes in {} ...".format(f)
		call("git add {0}".format(f), shell=True)

	print "\nCommitting changes ..."
	call("git commit -m 'via git_push'", shell=True)
	
	print "\nPushing to GitHub ..."
	call("git push origin master", shell=True)
	print "Pushed sucessfully to GitHub!"
elif permission == "n":
	sys.exit()

