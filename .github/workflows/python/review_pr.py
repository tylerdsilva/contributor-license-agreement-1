import os
import sys
import requests
import json
import subprocess
import re
from diff_parser import get_diff_details

print("current working directory is: ", os.getcwd())
STATUS_FAILED = 'FAILED'
SUCCESS_MESSAGE = 'ok'


def get_github_details():
    github_info_file = open('./.tmp/github.json', 'r') 
    return json.load(github_info_file)


def get_commit_details():
    commit_info_file = open('./.tmp/commitDetails.json', 'r')
    return json.load(commit_info_file)


def process_git_local_details():
    # Check if current dir is git dir
    is_git_dir = subprocess.check_output(
            ['/usr/bin/git', 'rev-parse', '--is-inside-work-tree']).decode('utf-8')
    print("Is git dir: ", is_git_dir)

    # git status
    git_status = subprocess.check_output(
            ['/usr/bin/git', 'status']).decode('utf-8')
    print("Git status: ", git_status)

    # last n commits
    last_10_commit_list = subprocess.check_output(
            ['/usr/bin/git', 'rev-list', '--max-count=10', 'HEAD']).decode('utf-8')
    print("last 10 commit ids are: ", last_10_commit_list)

    return {
        'is_git_dir': is_git_dir,
        'last_10_commit_list': last_10_commit_list
    }


def extract_pull_request_changes(commits):
    # github logins of all committers
    commit_logins = []
    commit_id_list = []
    files_updated = []
    for commit in commits:
        commiter_github_login = commit['committer']['login']
        if commiter_github_login not in commit_logins:
            commit_logins.append(commiter_github_login)
        
        commit_id = commit['sha']
        commit_id_list.append(commit_id)
        try:
            files = subprocess.check_output(
            ['/usr/bin/git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_id]).decode('utf-8').splitlines()
            for file in files:
                if file not in files_updated:
                    files_updated.append(file)
        except subprocess.CalledProcessError as e:
            print("Exception on process, rc=", e.returncode, "output=", e.output)
            sys.exit(1)

    print("All github users who made changes in the pull request: ", commit_logins)
    print("All commit ids in pull request: ", commit_id_list)
    print("All files updated in pull request: ", files_updated)
    
    return {
        'commit_id_list': commit_id_list,
        'commit_logins': commit_logins,
        'files_updated': files_updated
    }



def collect_pr_details(): 
    github = get_github_details()
    commits = get_commit_details()
    git_local = process_git_local_details()
    pr_changes = extract_pull_request_changes(commits)
    return {
        'github': github,
        'commits': commits,
        'num_commits_in_pr': len(commits),
        'event_name': github["event_name"],
        'pr_submitter_github_login': github['event']['pull_request']['user']['login'],
        'github_repo': github['repository'],
        'pr_number' : github['event']['number'],
        'is_git_dir': git_local['is_git_dir'],
        'last_10_commit_list': git_local['last_10_commit_list'],
        'commit_id_list': pr_changes['commit_id_list'],
        'commit_logins': pr_changes['commit_logins'],
        'files_updated': pr_changes['files_updated']
    }


def write_comment(comment):
    print(comment)
    f = open("./.tmp/comment", "a")
    f.write(comment)
    f.write("\n")
    f.close()


def task_failed(comment):
    f = open("./.tmp/failed", "a")
    f.write(comment)
    f.write("\n")
    f.close()
    write_comment(comment)
    return STATUS_FAILED


def validate_is_pull_request(pr_details):
    github_details = pr_details['github']
    if github_details["event_name"] != "pull_request" :
        print("Error! This operation is valid on github pull requests. Exiting. Event received: ", github_details["event_name"])
        sys.exit(1)


def validate_has_only_a_single_commit(pr_details):
    num_commits = pr_details['num_commits_in_pr']
    if num_commits != 1 :
        message = '''## Error: The pull request should have only a single commit. 
        Please squash all your commits and update this pull request.
        more help: https://stackoverflow.com/questions/5189560/squash-my-last-x-commits-together-using-git
        '''
        return task_failed(message)
    print('Pass: Pull request has only a single commit.')


def validate_has_only_a_single_file_change(pr_details):
    files_updated = pr_details['files_updated']
    if len(files_updated) != 1 :
        message = '## Error: The pull request should have exactly one file change signing the CLA. \nBut found the following files changed: '
        for file in files_updated:
            message += '\n   * ' + file
        return task_failed(message)
    print('Pass: Pull request has only a single file change.')


def getChanges(patch_details):
    diff_details = get_diff_details(patch_details)
    line_added = None
    if len(diff_details['linesAdded']) == 1:
        line_added = diff_details['linesAdded'][0]
    return {
        'linesRemoved' : len(diff_details['linesRemoved']),
        'linesAdded': len(diff_details['linesAdded']),
        'textAdded': line_added
    }


def validate_row_formatting(line):
    # Regular expression for validating the line format
    format_re = "\+\|\s*`[A-Za-z]+(\s[A-Za-z]+)*`\s*\|\s*\[[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\]\(https:\/\/github\.com\/[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\)\s*\|\s*[\d]{2}-[a-zA-Z]+-[\d]{4}\s*\|"
    # Regular expression for checking extra spaces at the begining of the line
    extra_spaces_re = "\+\s+\|\s*`[A-Za-z]+(\s[A-Za-z]+)*`\s*\|\s*\[[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\]\(https:\/\/github\.com\/[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\)\s*\|\s*[\d]{2}-[a-zA-Z]+-[\d]{4}\s*\|"
    # Regular expression for checking single qoutes instead of back ticks
    single_qoutes_re = "\+\|\s*'[A-Za-z]+(\s[A-Za-z]+)*'\s*\|\s*\[[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\]\(https:\/\/github\.com\/[a-zA-Z\d](?:[A-Za-z\d]|-(?=[a-zA-Z\d])){0,38}\)\s*\|\s*[\d]{2}-[a-zA-Z]+-[\d]{4}\s*\|"
    if re.match(format_re, line):
        print('Pass: Added line is of the specified format')
    elif re.match(extra_spaces_re, line):
        print(line)
        return task_failed('Error: The expected line should be: | `full name` | [git-username](https://github.com/git-username) | dd-month-yyyy | \n' + 'Please remove extra spaces in the start of the line.')
    elif re.match(single_qoutes_re, line):
        return task_failed("Error: The expected line should be: | `full name` | [naren](https://github.com/naren) | 14-july-2021 | \n" + "please use `full name` instead of 'full name'")
    else:
        return task_failed('Error: The expected line should be: | `full name` | [git-username](https://github.com/git-username) | dd-month-yyyy | \n')


def validate_githubid(pr_raiser_login, change):
    git_username1_re = "\[(.*)\]" # Git username provided in square brackets
    git_username2_re = '\(https:\/\/github.com\/(.*)\)' # Git username provided as a part of git profile url

    username1 = re.findall(git_username1_re, change)[0]
    username2 = re.findall(git_username2_re, change)[0]

    if pr_raiser_login != username1 or pr_raiser_login != username2:
        return task_failed('Error: The expected line should be: | `full name` | [git-username](https://github.com/git-username) | dd-month-yyyy | \n'\
                            + 'Github username should be same as pull request user name'
                        )
    return SUCCESS_MESSAGE
 

# Change line is of the format "+| `full name`| [pr_raiser_login](https://github.com/pr_raiser_login) |12-july-2021|"
def validate_change(pr_raiser_login, change):
    ROW_FORMATTING_VALIDATION = validate_row_formatting(change)
    if ROW_FORMATTING_VALIDATION == STATUS_FAILED:
        print('Line format validations failed. Exiting!')
        return STATUS_FAILED
    
    GITHUBID_VALIDATION = validate_githubid(pr_raiser_login, change)
    if GITHUBID_VALIDATION == STATUS_FAILED:
        print('Git username validation failed!')
        return STATUS_FAILED

    return SUCCESS_MESSAGE


def validate_patch(pr_details):
    github = pr_details['github']
    diffURL = github['event']['pull_request']['diff_url']
    print(diffURL)
    response = requests.get(diffURL)
    if response.status_code != 200:
        task_failed('Could not get pull request details')
        sys.exit(1)
    changes = getChanges(response.text)
    if changes['linesRemoved'] !=0:
        return task_failed('## Error: Some lines were removed. \n    Please re-submit PR containing exactly one change adding your name to the CLA.\n')
    if changes['linesAdded'] !=1:
        return task_failed('## Error: More than 1 line was added. \n   Please re-submit PR containing exactly one change adding your name to the CLA.\n')
    print(changes['textAdded'])

    CHANGE_VALIDATION = validate_change(pr_details['pr_submitter_github_login'], changes['textAdded'])
    return CHANGE_VALIDATION

def review_pr():
    print('Reviewing PR')
    pr_details = collect_pr_details()
    validate_is_pull_request(pr_details)
    COMMIT_VALIDATION = validate_has_only_a_single_commit(pr_details)
    FILE_VALIDATION = validate_has_only_a_single_file_change(pr_details)
    PATCH_VALIDATION = validate_patch(pr_details)
    if COMMIT_VALIDATION == STATUS_FAILED or FILE_VALIDATION == STATUS_FAILED or PATCH_VALIDATION == STATUS_FAILED:
        print('Validations failed. Exiting!')
        return
    
    write_comment( '\n## Welcome \nHello ' + pr_details['pr_submitter_github_login'] + ', \n'\
                  + 'Thank you for being a part of our community and helping build free software for the future. '\
                  + 'On behalf of everyone at core.ai open research, we extend a warm welcome to our community. \n'\
                  + 'If you have not done so already, please [join our discord group](https://discord.gg/GaBDAK7BRM) to interact with our community members. \n'
    )


review_pr()

# Invalid row fomatting
# EXPECTED_ERROR_MESSAGE = STATUS_FAILED
# assert validate_change('naren', "+ `full name`| [naren](https://github.com/naren) |14-july-2021|") == EXPECTED_ERROR_MESSAGE
# assert validate_change('naren', "lols") == EXPECTED_ERROR_MESSAGE
# assert validate_change('naren', "+| `full name` [naren](https://github.com/naren) |14-july-2021|") == EXPECTED_ERROR_MESSAGE
# assert validate_change('naren', "+ `full name`| [nare") == EXPECTED_ERROR_MESSAGE
# assert validate_change('naren', "+       | `full name`|   [naren](https://github.com/naren)  |14-july-2021  |   ") == EXPECTED_ERROR_MESSAGE
# assert validate_change('psdhanesh7', "+| Dhanesh P S| [psdhanesh7](http://github.com/psdhanesh7)| 25-March-2022 |")

# # success case
# EXPECTED_SUCCESS_MESSAGE = "ok"
# assert validate_change('newuser', "+| `full name user` | [newuser](https://github.com/newuser) | 14-july-2021 |") == EXPECTED_SUCCESS_MESSAGE
# assert validate_change('newuser', "+|`full name user`|[newuser](https://github.com/newuser)|14-july-2021|") == EXPECTED_SUCCESS_MESSAGE
# assert validate_change('newuser', "+|  `full name user`   |    [newuser](https://github.com/newuser)   |  14-july-2021  |") == EXPECTED_SUCCESS_MESSAGE

# # user names should be valid
# EXPECTED_ERROR_MESSAGE = STATUS_FAILED
# assert validate_change('naren', "+| `full name`| [some_wrong_user](https://github.com/naren) |14-july-2021|") == EXPECTED_ERROR_MESSAGE 
# assert validate_change('naren', "+| `full name`| [naren](https://github.com/some_wrong_user) |14-july-2021|") == EXPECTED_ERROR_MESSAGE 
# assert validate_change('naren', "+| 'full name'| [naren](https://github.com/some_wrong_user) |14-july-2021|") == EXPECTED_ERROR_MESSAGE
