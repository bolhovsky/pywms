#!/usr/bin/python
# -*- coding=utf-8 -*-

import socket
import threading
import sys
import time
import shlex

#import Image
#
#im = Image.open( "test.jpg" )
#print im
#im = Image.open( "test.png" )
#print im
#im = Image.open( "test.gif" )
#print im

def parse_separated_string( string, delim ):
    splitter = shlex.shlex( string, posix = True )
    splitter.whitespace = delim
    splitter.whitespace_split = True
    return list( splitter )

class SocketLineReader():

    def __init__( self, sock ):
        self.sock = sock

    def __iter__( self ):
        return self

    def next( self ):
        buffer = ""
        while True:
            data = self.sock.recv( 1 )
            if data == "":
                raise StopIteration
            if data != '\n':
                buffer = "%s%s" % ( buffer, data )
            else:
                break
        return buffer

class PacketReader():

    def __init__( self, sock ):
        self.sock = sock
        self.reader = SocketLineReader( sock )

    def __iter__( self ):
        return self

    def next( self ):
        packet = []
        while True:
            line = None
            try:
                line = self.reader.next()
                line = line.strip()
            except StopIteration:
                break
            if line != '':
                packet.append( line )
            else:
                break
        return packet

class StatusThread( threading.Thread ):

    def __init__( self, params, output_lock, params_lock ):
        threading.Thread.__init__( self )
        self.params, self.old_status = params, None
        self.output_lock, self.params_lock = output_lock, params_lock
        self.params_lock.acquire()
        self.is_verbose = self.params[ 'is-verbose' ]
        self.is_finish = self.params[ 'is-finish' ]
        self.params_lock.release()

    def run( self ):
        while not self.is_finish:
            self.params_lock.acquire()
            self.is_finish = self.params[ 'is-finish' ]
            self.params_lock.release()
            time.sleep( 5 )

class ConnectionsThread( threading.Thread ):

    def __init__( self, params, output_lock, params_lock ):
        threading.Thread.__init__( self )
        self.params, self.is_finish = params, False
        self.output_lock, self.params_lock = output_lock, params_lock
        self.params_lock.acquire()
        self.is_verbose = self.params[ 'is-verbose' ]
        self.is_finish = self.params[ 'is-finish' ]
        self.host, self.port = self.params[ 'host' ], self.params[ 'port' ]
        self.params_lock.release()

    def run( self ):
        while not self.is_finish:
            time.sleep( 5 )
            sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            sock.bind( ( self.host, self.port ) )
            sock.listen( 1 )
            client_conn, client_addr = sock.accept()
            self.params_lock.acquire()
            self.params[ 'clients-to-start' ].append( ( client_conn, client_addr ) )
            self.params_lock.release()
            print "connect with %s:%s" % client_addr

class InputThread( threading.Thread ):

    def __init__( self, client_sock, params, output_lock, params_lock ):
        threading.Thread.__init__( self )
        self.client_sock = client_sock
        self.params = params
        self.output_lock, self.params_lock = output_lock, params_lock
        self.params_lock.acquire()
        self.is_verbose = self.params[ 'is-verbose' ]
        self.is_finish = self.params[ 'is-finish' ]
        self.params_lock.release()

    def process_packet( self, packet ):
        p = {}
        header = packet[0]
        header = parse_separated_string( header, ' ' )
        p[ 'type' ] = header[0]
        p[ 'url' ] = header[1]
        p[ 'version' ] = header[2]
        p[ 'flags' ] = {}
        packet = packet[1:]
        for item in packet:
            item = parse_separated_string( item, ': ' )
            p[ 'flags' ][ item[0] ] = item[1]
        return p

    def run( self ):
        reader = PacketReader( self.client_sock )
        while not self.is_finish:
            packet = reader.next()
            if not packet:
                break
            packet = self.process_packet( packet )
            print "Packet: %s" % packet
            self.params_lock.acquire()
            self.params[ 'input-pool' ][  self.client_sock ].append( packet )
            self.is_finish = self.params[ 'is-finish' ]
            self.params_lock.release()

class ProcessingThread( threading.Thread ):

    def __init__( self, params, output_lock, params_lock ):
        threading.Thread.__init__( self )
        self.params = params
        self.output_lock, self.params_lock = output_lock, params_lock
        self.params_lock.acquire()
        self.is_verbose = self.params[ 'is-verbose' ]
        self.is_finish = self.params[ 'is-finish' ]
        self.params_lock.release()

    def run( self ):
        while not self.is_finish:

            time.sleep( 5 )

            self.params_lock.acquire()
            self.is_finish = self.params[ 'is-finish' ]
            self.params_lock.release()

class OutputThread( threading.Thread ):

    def __init__( self, client_sock, params, output_lock, params_lock ):
        threading.Thread.__init__( self )
        self.client_sock = client_sock
        self.params = params
        self.output_lock, self.params_lock = output_lock, params_lock
        self.params_lock.acquire()
        self.is_verbose = self.params[ 'is-verbose' ]
        self.is_finish = self.params[ 'is-finish' ]
        self.params_lock.release()

    def run( self ):
        while not self.is_finish:
            time.sleep( 5 )

            self.params_lock.acquire()
            self.is_finish = self.params[ 'is-finish' ]
            self.params_lock.release()

if __name__ == "__main__":
    import optparse
    from optparse import OptionParser
    options = None
    args = None

    option_list = [
        optparse.make_option( "--host", dest = "host", type = "string", help = "wms host" ),
        optparse.make_option( "--port", dest = "port", type = "string", help = "wms port" ),
        ]
    usage = "usage: %prog [options] arg1 arg2"
    optparser = OptionParser( usage = usage, option_list = option_list )
    ( options, args ) = optparser.parse_args()

    params = {
      'host' : '127.0.0.1',
      'port' : 50007,
      'clients' : {},
      'clients-to-start' : [],
      'input-pool' : {},
      'output-pool' : {},
      'is-verbose' : False,
      'is-finish' : False
    }

    if options.host:
        params[ 'host' ] = options.host
    if options.port:
        params[ 'port' ] = int( options.port )

    output_lock = threading.Lock()
    params_lock = threading.Lock()

    sys.stderr.write( "started\n" )
    status_thread = StatusThread( params, output_lock, params_lock )
    status_thread.setName( "status" )
    status_thread.start()
    status_thread = ConnectionsThread( params, output_lock, params_lock )
    status_thread.setName( "connect" )
    status_thread.start()

    is_finish = False

    while not is_finish:
        client_connection, client_address = None, None
        params_lock.acquire()
        if len( params[ 'clients-to-start' ] ) > 0:
            client_connection, client_address = params[ 'clients-to-start' ].pop()
        params_lock.release()
        if client_connection:
            input_thread = InputThread( client_connection, params, output_lock, params_lock )
            input_thread.setName( "input %s:%s" % client_address )
            input_thread.start()

            process_thread = ProcessingThread( client_connection, params, output_lock, params_lock )
            process_thread.setName( "process %s:%s" % client_address )
            process_thread.start()

            output_thread = OutputThread( client_connection, params, output_lock, params_lock )
            output_thread.setName( "output %s:%s" % client_address )
            output_thread.start()

            params_lock.acquire()
            params[ 'clients' ][ client_address ] = ( client_connection, input_thread, process_thread, output_thread )
            params[ 'sockets' ][ client_connection ] = client_address
            params[ 'input-pool' ][ client_connection ] = []
            params[ 'output-pool' ][ client_connection ] = []
            params_lock.release()

        params_lock.acquire()
        is_finish = params[ 'is-finish' ]
        params_lock.release()

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
