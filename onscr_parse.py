#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       onscr_parse.py
#       
#       Copyright 2011 Mark Kolloros <uvthenfuv@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#       

from __future__ import division, print_function, unicode_literals

import sys
import codecs

import nscr


class LineReader(object):
    # Nscripter uses commands like "goto" and "skip".
    # Thus, we can't really make the script into trees.
    # So we use a procedural approach.
    
    START_LABEL = b"*define"
    
    def __init__(self, filename):
        self._lines = []
        self._labels = dict()
        self._gosub_stack = []
        
        self._read_file(filename)
        
        self.last_line = len(self._lines)-1
        
        self.goto(self.START_LABEL)
        
        
    def _read_file(self, filename):
        # reads in lines and lists labels
        with codecs.open(filename, 'r', encoding="sjis") as f:
            for line in f:
                line = line.strip().lstrip()
                
                # list labels
                if len(line) > 1 and line[0] == b"*":
                    self._labels[line.lower()] = len(self._lines)
                    
                self._lines.append(line)
                
                
    def _next_line(self):
        self.current_line += 1
        
        return self._lines[self.current_line]
        
        
    def read_next(self):
        return self._next_line()
        
        
    def skip(self, n):
        """Skip N lines of text; execution will continue
        on the Nth line from the current one.
        Negative skipping is also supported."""
        
        self.current_line += n-1
        
        
    def goto(self, label):
        """The label string should include the asterisk at the beginning."""
        
        # We go before it so that the next read will be from the "*label" line
        self.current_line = self._labels[label]-1
        
        
    def gosub(self, label):
        self._gosub_stack.append( self.current_line )
        self.goto(label)
        
        
    def cmd_return(self):
        try:
            self.current_line = self._gosub_stack.pop()
        except IndexError:
            self.error("Tried to return while not gosub'd.")
            
            
    def jumpf(self):
        """The worst form of flow control in history."""
        
        s = ""
        while b"~" not in s:
            s = self._next_line()
            
        # Currently we don't support mid-line skipping with jumpf
        self.current_line -= 1
        
        
    def error(self, msg):
        print("Strange.", msg)
        
        
class CmdReader(LineReader):
    ARG_SEP = b","
    
    def __init__(self, *args, **kwargs):
        super(CmdReader, self).__init__(*args, **kwargs)
        
        # The commands will be popped out, so the
        # first command should be at the last position!
        self._cmds = []
        # for multi-line statements
        self.unfinished = b""
        
        
    def read_next(self):
        while self._cmds == []:
            line = super(CmdReader, self).read_next()
            if line.endswith(self.ARG_SEP) and (not line.startswith(b"`") or self.unfinished != b""):
                self.unfinished += line
                continue
            
            else:    
                if self.unfinished != b"":
                    line = self.unfinished + line
                    self.unfinished = b""
                    
                self._cmds.extend( self.parse_line(line) )
                
        return self._cmds.pop()
        
        
    def parse_line(self, line):
        got = nscr.parse("goal", line)
        
        if got == None: # testing
            print("Return value replaced for:", line)
            return []
            
        else:
            return reversed(got)
            
            
def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: onscr_parse.py FILENAME [SKIP_TO]")
        exit(1)
        
    filename = sys.argv[1]
    
    reader = CmdReader(filename)
    
    if len(sys.argv) == 3:
        cmd_count = int( sys.argv[2] ) - 1
        
    else:
        cmd_count = 0
        
    try:
        for i in xrange(cmd_count):
                reader.read_next()
                
    except IndexError:
        print("Error: Skipping went over bounds!")
        exit(1)
        
        
    print("Successfully initialized.")
    
    try:
        while raw_input("").lower() not in ("q", "quit", "e", "exit"):
            if reader.current_line != reader.last_line:
                cmd_count += 1
                cmd = reader.read_next()
                print( cmd_count, cmd )
                
            else:
                # If the last line contained multiple commands
                # only the first will be displayed and then we enter
                # last line mode. But that's not a very likely
                # circumstance.
                print("That was the last line.")
                
    except EOFError:
        pass
        
        
if __name__ == '__main__':
    main()
    
    
