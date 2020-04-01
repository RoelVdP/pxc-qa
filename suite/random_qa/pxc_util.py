#!/usr/bin/env python3
import os
import sys
import argparse
import time
import subprocess
import itertools
cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from config import *
from util import pxc_startup
from util import db_connection
from util import utility
utility_cmd = utility.Utility()
utility_cmd.check_python_version()

# Read argument
parser = argparse.ArgumentParser(prog='PXC Utility', usage='%(prog)s [options]')
parser.add_argument('-e', '--encryption-run', action='store_true',
                    help='This option will enable encryption options')
parser.add_argument('--start', action='store_true',
                    help='Start PXC nodes')
parser.add_argument('--stop', action='store_true',
                    help='Stop PXC nodes')

args = parser.parse_args()
if args.encryption_run is True:
    encryption = 'YES'
else:
    encryption = 'NO'


class PXCUtil:
    def start_pxc(self):
        # Start PXC cluster
        dbconnection_check = db_connection.DbConnection(USER, WORKDIR + '/node1/mysql.sock')
        server_startup = pxc_startup.StartCluster(parent_dir, WORKDIR, BASEDIR, int(NODE))
        result = server_startup.sanity_check()
        utility_cmd.check_testcase(result, "Startup sanity check")
        if encryption == 'YES':
            result = server_startup.create_config('encryption')
            utility_cmd.check_testcase(result, "Configuration file creation")
        else:
            result = server_startup.create_config('none')
            utility_cmd.check_testcase(result, "Configuration file creation")
        result = server_startup.initialize_cluster()
        utility_cmd.check_testcase(result, "Initializing cluster")
        result = server_startup.start_cluster('--max-connections=1500 ')
        utility_cmd.check_testcase(result, "Cluster startup")
        result = dbconnection_check.connection_check()
        utility_cmd.check_testcase(result, "Database connection")
        query = BASEDIR + "/bin/mysql --user=root --socket=" + \
                WORKDIR + "/node1/mysql.sock -e'drop database if exists test " \
                          "; create database test ;' > /dev/null 2>&1"
        query_status = os.system(query)
        if int(query_status) != 0:
            # return 1
            print("ERROR!: Could not create test database.")
            exit(1)
        utility_cmd.check_testcase(0, "PXC connection string")
        for i in range(1, int(NODE) + 1):
            print('\t' + BASEDIR + '/bin/mysql --user=root --socket=' +
                  WORKDIR + '/node' + str(i) + '/mysql.sock')

    def stop_pxc(self):
        # Stop PXC cluster
        for i in range(int(NODE), 0, -1):
            shutdown_node = BASEDIR + '/bin/mysqladmin --user=root --socket=' + \
                        WORKDIR + '/node' + str(i) + '/mysql.sock shutdown > /dev/null 2>&1'
            result = os.system(shutdown_node)
            utility_cmd.check_testcase(result, "PXC: shutting down cluster node" + str(i))


pxc_util = PXCUtil()
if args.start is True:
    pxc_util.start_pxc()

if args.stop is True:
    pxc_util.stop_pxc()