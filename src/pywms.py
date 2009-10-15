#!/usr/bin/python
# -*- coding=utf-8 -*-

import socket
import threading
import sys
import time

#import Image
#
#im = Image.open( "test.jpg" )
#print im
#im = Image.open( "test.png" )
#print im
#im = Image.open( "test.gif" )
#print im

class StatusMonitoringThread( threading.Thread ):

    def __init__( self, params, output_lock, params_lock ):
        threading.Thread.__init__( self )
        self.params, self.is_finish, self.old_status = params, False, None
        self.output_lock, self.params_lock = output_lock, params_lock
        self.params_lock.acquire()
        self.is_verbose = self.params[ 'is-verbose' ]
        self.params_lock.release()

    def run( self ):
        while not self.is_finish:
            time.sleep( 5 )
            self.params_lock.acquire()
            self.is_finish = self.params[ 'is-finish' ]
            self.params_lock.release()

class ConnectionsThread( threading.Thread ):

    def __init__( self, params, output_lock, params_lock ):
        threading.Thread.__init__( self )
        self.params, self.is_finish = params, False
        self.output_lock, self.params_lock = output_lock, params_lock
        self.params_lock.acquire()
        self.is_verbose = self.params[ 'is-verbose' ]
        self.host, self.port = self.params[ 'host' ], self.params[ 'port' ]
        self.params_lock.release()

    def run( self ):
        while self.is_verbose:
            time.sleep( 5 )
            s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            s.bind( ( self.host, self.port ) )
            s.listen( 1 )
            conn, addr = s.accept()
            print 'Connected by', addr

            while 1:
                data = conn.recv( 1024 )
                if not data:
                    break
                print data
            #    conn.send(data)

            conn.close()

class RequestProcessingThread( threading.Thread ):

    old_status = None

    def __init__( self, params, output_lock, params_lock ):
        threading.Thread.__init__( self )
        self.params = params
        self.output_lock, self.params_lock = output_lock, params_lock
        self.params_lock.acquire()
        self.is_verbose = self.params[ 'is-verbose' ]
        self.params_lock.release()
        self.old_status = None

    def run( self ):
        while self.is_verbose:
            time.sleep( 5 )

class ResponsePrepareThread( threading.Thread ):

    old_status = None

    def __init__( self, params, output_lock, params_lock ):
        threading.Thread.__init__( self )
        self.params = params
        self.output_lock, self.params_lock = output_lock, params_lock
        self.params_lock.acquire()
        self.is_verbose = self.params[ 'is-verbose' ]
        self.params_lock.release()
        self.old_status = None

    def run( self ):
        while self.is_verbose:
            time.sleep( 5 )

class ResponseProcessingThread( threading.Thread ):

    old_status = None

    def __init__( self, params, output_lock, params_lock ):
        threading.Thread.__init__( self )
        self.params = params
        self.output_lock, self.params_lock = output_lock, params_lock
        self.params_lock.acquire()
        self.is_verbose = self.params[ 'is-verbose' ]
        self.params_lock.release()
        self.old_status = None

    def run( self ):
        while self.is_verbose:
            time.sleep( 5 )

if __name__ == "__main__":
    import optparse
    from optparse import OptionParser
    options = None
    args = None

    option_list = [
        optparse.make_option( "--host", dest = "host", type = "string", help = "wms host" ),
        optparse.make_option( "--host", dest = "port", type = "string", help = "wms port" ),
        ]
    usage = "usage: %prog [options] arg1 arg2"
    optparser = OptionParser( usage = usage, option_list = option_list )
    ( options, args ) = optparser.parse_args()

    params = {
      'host' : '127.0.0.1',
      'port' : '50007',
      'requests' : [],
      'connection-pool' : [],
      'is-verbose' : False,
      'is-finish' : False
    }

    if options.host:
        params[ 'host' ] = options.host
    if options.port:
        params[ 'port' ] = options.port

    output_lock = threading.Lock()
    params_lock = threading.Lock()

    sys.stderr.write( "started\n" )
    status_thread = StatusMonitoringThread( params, output_lock, params_lock )
    status_thread.setName( "status" )
    status_thread.start()

    is_finish = False

    while True:
        params_lock.acquire()
        params_lock.release()

#        output_lock.acquire()
#        print is_areas_empty, download_thread_count, is_download_finish, is_start_new_download, is_data_empty, separate_thread_count, is_separate_finish, is_start_new_separate 
#        output_lock.release()

        if is_finish:
            break
        time.sleep( 1 )

    params_lock.acquire()
    params[ 'is-finish' ] = True
    params_lock.release()
    status_thread.join()

# �������� �����������
"""
GET /?request=GetCapabilities HTTP/1.1
Host: localhost
User-Agent: Mozilla/9.876 (X11; U; Linux 2.2.12-20 i686, en) Gecko/25250101 Netscape/5.432b1
"""

# ������ �����
"""
GET /?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=WMS&SRS=EPSG:4326&STYLES=,&FORMAT=image/png&TRANSPARENT=TRUE&WIDTH=256&HEIGHT=256&BBOX=-180.00000000,0.00000000,0.00000000,90.00000000 HTTP/1.1
Host: localhost
User-Agent: Mozilla
"""

#
"""
GET /wms?bbox=27.3962860,53.8619431,27.3999658,53.8641132&srs=EPSG:4326&width=499&height=499 HTTP/1.1
User-Agent: JOSM/1.5 (2083 ru) Java/1.6.0_11
Host: localhost:50007
Accept: text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2
Connection: keep-alive
"""
