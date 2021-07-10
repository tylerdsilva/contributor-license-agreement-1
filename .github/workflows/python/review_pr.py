import os
import sys
import json
import subprocess

print("current working directory is: ", os.getcwd())


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
    f = open("./.tmp/comment", "w")
    f.write(comment)
    f.close()


def validate_is_pull_request(pr_details):
    github_details = pr_details['github']
    if github_details["event_name"] != "pull_request" :
        print("Error! This operation is valid on github pull requests. Exiting. Event received: ", github_details["event_name"])
        sys.exit(1)


def validate_has_only_a_single_commit(pr_details):
    num_commits = pr_details['num_commits_in_pr']
    if num_commits != 1 :
        message = 'The pull request should have only a single commit. Please squash all your commits and update this pull request.'
        print(message)
        write_comment(message)
        sys.exit(1)


def review_pr():
    print('Reviewing PR')
    pr_details = collect_pr_details()
    validate_is_pull_request(pr_details)
    validate_has_only_a_single_commit(pr_details)


review_pr()
