import os
import logging
from subprocess import run
from shutil import rmtree
from requests import post

from ocs.args import args
from ocs.data import contest_data, problem_data
from ocs.db import con, cur
from ocs.languages import languages


def statement(contest, problem):
    """Get problem statement of local or remote problem"""

    if '@' not in problem:  # Local
        return open(os.path.join(args.contests_dir, contest, problem, 'problem.pdf'), 'rb').read()
    else:  # Remote
        server = problem.split('@')[1]
        return post(server, json={'type': problem, 'contest': contest, 'problem': problem.split('@')[0]}).text


def process(username, contest, problem, language, code):
    """Process a submission"""

    number = int(cur.execute('SELECT Count(*) FROM "' + contest + '_submissions"').fetchone()[0])

    if '@' not in problem:  # Local
        verdict = run_local(contest, problem, language, code, number)
        rmtree(os.path.join('/tmp', str(number)))  # Clean up
    else:  # Remote
        verdict = run_remote(contest, problem, language, code, number)

    logging.info(verdict)

    # Update submissions table
    cur.execute('INSERT INTO "' + contest + '_submissions" VALUES (?, ?, ?, ?, ?)',
                (number, username, problem, code, verdict))

    # Update status table
    if cur.execute('SELECT Count(*) FROM "' + contest + '_status" WHERE username = ?', (username,)).fetchone()[0] == 0:
        cur.execute('INSERT INTO "' + contest + '_status" VALUES ("' + username + '", ' +
                    '0, ' * (len(contest_data[contest]['problems']) - 1) + '0)')
    cur.execute('UPDATE "' + contest + '_status" SET ' + problem +
                ' = ? WHERE username = ?', (str(verdict), username,))
    
    con.commit()

    return verdict


def run_local(contest, problem, language, code, number):
    """Run a program locally"""

    # Save the program
    tmpdir = os.path.join('/tmp', str(number))
    os.mkdir(tmpdir)
    with open(os.path.join(tmpdir, 'main.' + language), 'w') as f:
        f.write(code)

    # Compile the code if needed
    if not languages[language].compile == None:
        ret = run('timeout 10 ' + languages[language].compile,
                  shell=True, cwd=tmpdir)
        if ret:
            return 500

    tcdir = os.path.join(args.contests_dir, contest, problem)
    time_limit = problem_data[contest][problem]['time-limit']
    memory_limit = problem_data[contest][problem]['memory-limit']

    tc = 1
    while os.path.isfile(os.path.join(tcdir, str(tc) + '.in')):
        # Run test case
        # TODO: Strengthen sandbox
        ret = run('firejail --noprofile --net=none --rlimit-cpu={} --rlimit-as={}k {} < {} > out'.format(
                  time_limit, memory_limit, languages[language].run, os.path.join(tcdir, str(tc) + '.in')), shell=True, cwd=tmpdir).returncode
        if not ret == 0:
            return 408  # Runtime error

        # Diff the output with the answer
        # TODO: Support arbitrary diff commands
        ret = run('diff -w ' + os.path.join(tmpdir, 'out') + ' ' + os.path.join(tcdir, str(tc) + '.out'), shell=True).returncode
        os.remove(os.path.join(tmpdir, 'out'))  # Delete output
        if not ret == 0:
            return 406  # Wrong answer
        tc += 1

    return 202  # All correct!


def run_remote(contest, problem, language, code, number):
    """TODO: Run a program remotely"""

    pass
