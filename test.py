from threading import Thread
import time
from duplicity.asyncscheduler import thread

def test1():
    print "test 1"
    thread.start_new_thread(test2,())
    print "test 2"
    
def test2():
    print "test 3"
    time.sleep(5)
    print "test 4"