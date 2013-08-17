#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       pyonscr_curses.py
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

# onscr_interpreter went through big changes in the meantime
# it might not be compatible

from __future__ import division, print_function, unicode_literals

import sys
import curses

import onscr_interpreter


DEBUG = True



class CursesInterpreter(onscr_interpreter.VarKeeper):
    def __init__(self, stdscr, filename):
        super(CursesInterpreter, self).__init__(filename)
        
        # done by curses.wrapper
        self.stdscr = stdscr
        
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
            
        if DEBUG:
            self.errorlog = []
            
        self.running = False
        self.clearwait = False
        
        
    def run(self):
        self.running = True
        try:
            while self.running:
                super(CursesInterpreter, self).run_until_wait()
                self.user_wait()
                if self.clearwait:
                    self.clear()
                    self.clearwait = False
                    
        finally:
            if DEBUG:
                with open(b"PYONS_DEBUGLOG", b"w") as f:
                    for err in self.errorlog:
                        f.write(err)
                        f.write(b"\n")
                        
                        
    def user_wait(self):
        key = self.stdscr.getch()
        if key == ord('q'):
            self.running = False
            
        self.waiting = False
        
        
    def error(self, s):
        if DEBUG:
            self.errorlog.append(s)
            
            
    def do_text(self, text):
        text = text.replace("|", "...") # Tsukihime "…"
        self.stdscr.addstr(text)
        self.stdscr.refresh()
        
        
    def clear(self):
        self.stdscr.clear()
        self.stdscr.refresh()
        
        
    def do_EOP(self):
        self.waiting = True
        self.clearwait = True
        
        
    def do_end(self):
        self.running = False
        
        
    def do_br(self):
        # print an end-of-line
        self.stdscr.addstr("\n")
        self.stdscr.refresh()
        
        
    def do_select(self, *args):
        self.do_goto( self.selection(args) )
        self.clear()
        
        
    def do_selgosub(self, *args):
        self.do_gosub( self.selection(args) )
        self.clear()
        
        
    def selection(self, args):
        labels = []
        for i in xrange( len(args)//2 ):
            txt = args[(i*2)]
            labels.append( args[(i*2)+1] )
            
            txt = "{0}: {1}\n".format(i+1, txt)
            self.spectext(txt)
            
        # User choice
        got = self.get_choice( range( 1, len(labels)+1 ) )
        return labels[got-1]
        
        
    def do_btnwait(self, var):
        # We emulate it, and don't even care about button definitons
        self.spectext("Button wait mode. (Probably a menu.)\n")
        self.spectext("Input a number between 0 and 9 please.\n")
        self.spectext("9 will be interpreted as '-1', which represents a right-click.\n")
        
        n = self.get_choice( range(10) )
        if n == 9:
            n = -1
            
        self.do_mov(var, n)
        
        
    def spectext(self, s):
        s = s.replace("|", "...") # Tsukihime "…"
        self.stdscr.addstr( s, curses.color_pair(1) )
        self.stdscr.refresh()
        
        
    def get_choice(self, accepted_numbers):
        self.spectext( str(accepted_numbers) )
        # Loop and a half
        while True:
            key = self.stdscr.getch()
            n = key-ord('0')
            #~ self.spectext( str(n) )
            
            if n in accepted_numbers:
                return n
                
                
#~ class WordBreaker(object):
    #~ def __init__(self, fileobj, width, pos = 0):
        #~ self.out = fileobj
        #~ self.width = width
        #~ self.pos = pos
        #~ 
        #~ 
    #~ def write(self, text):
        #~ if text == "\n":
            #~ 
        #~ 
        #~ 
def main():
    if len(sys.argv) != 2:
        print("Usage: pyonscr_curses.py FILENAME")
        exit(1)
        
    curses.wrapper(run_interpreter, sys.argv[1])
    
    
def run_interpreter(stdscr, filename):
    interpreter = CursesInterpreter(stdscr, filename)
    interpreter.run()
    
    
if __name__ == '__main__':
    main()
