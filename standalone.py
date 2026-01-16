
import os
from threading import Thread
from time import sleep
import subprocess
import sys

def runserver():
    os.system('py manage.py runserver 0.0.0.0:80')
    # os.system('waitress-serve --host=0.0.0.0 --port=80 inventory.wsgi:application')

def lunchchrome():
    # ensure the django server is up and running
    sleep(2)
    # get ipv4 address
    os.system('start chrome http://192.168.2.10')
t1=Thread(target=runserver)

t2=Thread(target=lunchchrome)

t1.start()
t2.start()
