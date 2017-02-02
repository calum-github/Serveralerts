#!/usr/bin/python

###
# Author:   Calum Hunter                                               
# Date:     20/01/2017                                                 
# Version:  0.1                                                        
# Purpose:  Provide a tool to manage the server alerts (notifications) 
#           on macOS server 5.1 and higher.
###

import sqlite3
import sys
import os
import plistlib
import optparse
from distutils.version import LooseVersion 

# Location of the alertDB
DB_PATH = '/Library/Server/Alerts/alertData.db'
SCRIPT_NAME = sys.argv[0]

def main():
    # Sanity Checks
    if os.getuid() != 0:
        print '[ERROR] - You must run this tool as root.'
        sys.exit(1)
    if LooseVersion(get_serverversion()) >= LooseVersion('5.1.5'):
        pass
    else:
        print "[ERROR] - Server.app version is %s, %s requires server version 5.1.5 or higher." % (get_serverversion(), SCRIPT_NAME)
        sys.exit(1)
    # Handle the options [o for options]
    usage = "Usage: %prog [options] arg1"
    o = optparse.OptionParser(usage=usage)
    o.add_option(
        '--list','-l', help="List all current email recipients.", dest='list', \
        default=False, action='store_true')
    o.add_option(
        '--create','-c', help="Create the alertDB if it does not already exist.", dest='create', \
        default=False, action='store_true')
    o.add_option(
        '--add','-a', help="Add an email address. Pass the new email address as arg1", dest='add', \
        action='store', type='string')
    o.add_option(
        '--remove','-r', help="Remove an email address. Pass the email to remove as arg1", dest='remove', \
        action='store', type='string')
    # Parse our provided options
    (opts, args) = o.parse_args()
    # Do stuff based on our passed arguments
    if len(sys.argv) ==1:
        o.print_help()
        exit(0)
    if opts.create is True:
        create_db(DB_PATH)
    if not os.path.isfile(DB_PATH):
        print "[ERROR] - Alert DB does not exist. You need to create it with the --create flag. Run this command with no arguments for help."
        exit(1)
    if opts.add != None:
        insert_new_email(opts.add)
    if opts.list is True:
        list_emails()
        exit(0)
    if opts.remove != None:
        remove_email(opts.remove)
        exit(0)


def list_emails():
    print "Listing all email addresses currently configured:"
    try:
        open_db()
        c.execute("SELECT ZADDRESS FROM ZADMAILRECIPIENT")
        all_emails = c.fetchall()
        close_db()
    except Exception as err:
        print "[ERROR] - got an error %s" % err
        sys.exit(1)
    for email in all_emails:
            print email[0]


def create_db(DB_PATH):
    if os.path.isfile(DB_PATH):
        print "[ERROR] Alert DB already exists! No need to create it."
        sys.exit(1)
    else:
        print " - Creating %s ..." % DB_PATH
        try:
            open_db()
            c.execute("CREATE TABLE ZADALERT ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZCREATIONDATE TIMESTAMP, ZREADDATE TIMESTAMP, ZRESOLVEDDATE TIMESTAMP, ZSENTDATE TIMESTAMP, ZBUNDLE VARCHAR, ZIDENTIFIER VARCHAR, ZTYPE VARCHAR, ZATTRIBUTES BLOB )")
            c.execute("CREATE TABLE ZADALERTBUNDLE ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZENABLED INTEGER, ZMAILENABLED INTEGER, ZPUSHENABLED INTEGER, ZBUNDLE VARCHAR, ZNAME VARCHAR )")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(1,2,2,1,0,0,'CertificateAlerts','Certificate')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(2,2,2,1,1,1,'Caching','Caching')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(3,2,2,1,0,0,'CalendarContactsAlerts','CalendarAndContacts')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(4,2,2,1,0,0,'Firewall','Firewall')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(5,2,2,1,0,0,'Mail','Mail')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(6,2,2,1,0,0,'TimeMachine','Time Machine')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(7,2,1,1,1,1,'Common','Common')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(8,2,2,1,0,0,'SoftwareUpdate','Software Update')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(9,2,2,1,0,0,'NetworkConfiguration','Network Configuration')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(10,2,2,1,0,0,'Xsan','Xsan')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(11,2,2,1,0,0,'XcodeServer','Xcode Server')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(12,2,2,1,0,0,'ProfileManager','Profile Manager')")
            c.execute("INSERT INTO ZADALERTBUNDLE VALUES(13,2,2,1,0,0,'Disk','Disk')")
            c.execute("CREATE TABLE ZADATTRIBUTE ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZNAME VARCHAR, ZVALUE VARCHAR )")
            c.execute("INSERT INTO ZADATTRIBUTE VALUES(1,3,12,'pushEnabled','0')")
            c.execute("CREATE TABLE ZADMAILRECIPIENT ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZENABLED INTEGER, ZADDRESS VARCHAR, ZLOCALIZATION VARCHAR )")
            c.execute("CREATE TABLE ZADPUSHRECIPIENT ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZENABLED INTEGER, ZGUID VARCHAR, ZLOCALIZATION VARCHAR, ZNAME VARCHAR, ZTOKEN BLOB )")
            c.execute("CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER PRIMARY KEY, Z_NAME VARCHAR, Z_SUPER INTEGER, Z_MAX INTEGER)")
            c.execute("INSERT INTO Z_PRIMARYKEY VALUES(1,'ADAlert',0,30)")
            c.execute("INSERT INTO Z_PRIMARYKEY VALUES(2,'ADAlertBundle',0,13)")
            c.execute("INSERT INTO Z_PRIMARYKEY VALUES(3,'ADAttribute',0,1)")
            c.execute("INSERT INTO Z_PRIMARYKEY VALUES(4,'ADMailRecipient',0,2)")
            c.execute("INSERT INTO Z_PRIMARYKEY VALUES(5,'ADPushRecipient',0,0)")
            c.execute("CREATE TABLE Z_METADATA (Z_VERSION INTEGER PRIMARY KEY, Z_UUID VARCHAR(255), Z_PLIST BLOB)")
            c.execute("CREATE TABLE Z_MODELCACHE (Z_CONTENT BLOB)")
            write_changes()
        except Exception as err:
            print "[ERROR] - There was an error inserting tables into the database! Error code: %s" % err
            close_db()
            sys.exit(1)
        close_db()


def insert_new_email(email):
    print " - Inserting email address: %s into Alert Notification DB ..." % email
    try:
        open_db()
        c.execute("INSERT INTO ZADMAILRECIPIENT ('Z_ENT','Z_OPT','ZENABLED','ZADDRESS','ZLOCALIZATION') VALUES ('4','1','1','%s','en')" % email)
        write_changes()
    except Exception as err:
        print "[ERROR] - There was an error inserting email address: %s into Alert Notification DB ..." % email
        print "[ERROR] - Error: %s" % (err)
        close_db()
        sys.exit(1)
    close_db()


def remove_email(email):
    print "- Searching for email address to remove: %s" % email
    try:
        open_db()
        c.execute("SELECT * FROM ZADMAILRECIPIENT WHERE ZADDRESS = '%s'" % email)
        remove_emails = c.fetchone()
    except Exception as err:
        print "[ERROR] - got an error %s" % err
        close_db()
        sys.exit(1)
    if remove_emails != None:
        print "- Removing email address..."
        try:
            c.execute("DELETE FROM ZADMAILRECIPIENT WHERE ZADDRESS = '%s'" % email)
            write_changes()
        except Exception as err:
            print "[ERROR] - Got an error %s" % err
            close_db
            sys.exit(1)
        else:
            close_db
            sys.exit(0)
    else:
        print "[ERROR] - Unable to locate email address: %s" % email
        close_db()
        sys.exit(1) 
    

def open_db():
    global c
    global conn 
    try: 
        print " - Opening Database ..."
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
    except Exception as err:
        print "[ERROR] - Unable to open Database. Error code: %s" % err
        sys.exit(1)


def write_changes():
    try:
        conn.commit()
    except Exception as err:
        print "[ERROR] - There was an error writing changes to the DB. Error code: %s" % err
        sys.exit(1)
    print "[OK] - Changes successfully written to DB."


def close_db():
    try: 
        conn.close()
    except Exception as err:
        print "[ERROR] Unable to close Database. Error code: %s" % err
        sys.exit(1)


def get_serverversion():
    if os.path.isfile('/Applications/Server.app/Contents/version.plist'):    
        try:
            serverversion = '/Applications/Server.app/Contents/version.plist'
            plist = plistlib.readPlist(serverversion)
            return plist['CFBundleShortVersionString']
        except Exception as err:
            print "[ERROR] - Got an error: %s" % err
    else:
        print "[ERROR] Server.app is not installed on this system!"
        sys.exit(1)


if __name__ == '__main__':
    main()

