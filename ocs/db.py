import logging
import os
from sqlite3 import connect

from ocs.about import about, contest_info
from ocs.args import args


# Prepare database
database = os.path.join(args.data_dir, 'ocs.db')
logging.debug(database)
con = connect(database, check_same_thread=False)
cur = con.cursor()
logging.info('Database connected')


# Create user table
cur.execute('CREATE TABLE IF NOT EXISTS users (username text unique, name text, email text unique, password text)')


for contest in about['contest']:
    # Create contest status table
    command = 'CREATE TABLE IF NOT EXISTS "' + contest + '_status" (username text, '
    for problem in contest_info['problems']:
        command += '"' + problem + '" text, '
    cur.execute(command[:-2] + ')')

    # Create contest submissions table
    cur.execute('CREATE TABLE IF NOT EXISTS "' + contest +
                '_submissions" (number real, username text, problem text, code text, verdict real)')
con.commit()
