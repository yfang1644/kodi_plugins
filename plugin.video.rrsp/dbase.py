#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import json
import urllib
conn = sqlite3.connect('test.db')

c = conn.cursor()
c.execute('''CREATE TABLE MJINDEX
            (ID INT PRIMARY KEY NOT NULL,
             NAME TEXT  NOT NULL);''')
  
f = open('jss', 'r')
x = f.read()

js = json.loads(x)
for x in js:
    name = x.encode('utf-8')
    cmd = "INSERT INTO MJINDEX (ID, NAME) VALUES ({0}, \"{1}\")".format(js[x], name)
    print cmd
    c.execute(cmd)

conn.commit()
conn.close()
