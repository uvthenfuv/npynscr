#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       onscr_interpreter.py
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
import collections
import functools

import onscr_parse


class InterpreterBase(object):
    # This is supposed to be subclassed.
    
    def __init__(self, filename):
        self.parser = onscr_parse.CmdReader(filename)
        
        self.varkeeper = VarKeeper()
        self.modules = [self, self.varkeeper]
        
        self.waiting = False
        
        
    def run_until_wait(self):
        while not self.waiting:
            self.step()
            
            
    def step(self):
        statement = self.parser.read_next()
        
        self.run_stmt(statement)
        
        
    def run_stmt(self, statement):
        assert len(statement) in (1, 2)
        
        if len(statement) == 2:
            self._run_cmd(*statement)
            
        else:
            assert statement[0][0] == b"*"
            # It's a label.
            pass
            
            
    def _run_cmd(self, cmd, args):
        for module in self.modules:
            fname = 'do_' + cmd
            if hasattr(module, fname):
                func = getattr(module, fname)
                
                func(*args)
                return
                
        # we did not return, ergo we did not find that command
        self.error("**** Command '" + cmd + "' is not supported yet.")
        
        
    def error(self, s):
        print(s)
        
        
    # basic functions
    def do_game(self):
        self.do_goto("*start")
        
        
    def do_click(self):
        # the NScripter command for waiting until a click
        self.waiting = True
        
        
    def do_EOP(self):
        # EOP (end-of-page) is how the parser returns the
        # backslash special command
        self.waiting = True
        
        
    def do_goto(self, label):
        self.parser.goto(label)
        
        
    def do_skip(self, n):
        self.parser.skip(n)
        
        
    def do_gosub(self, label):
        self.parser.gosub(label)
        
        
    def do_return(self):
        self.parser.cmd_return()
        
        
    def clear(self):
        pass
        
        
    def do_notif(self, conds, stmts):
        self.do_if(conds, stmts, False)
        
        
    def do_if(self, conds, stmts, expecting = True):
        if self.eval_conds(conds) == expecting:
            for stmt in stmts:
                self.run_stmt(stmt)
                
                
    def eval_conds(self, conds):
        for cond in conds:
            cmd = cond[0]
            args = [ self.varkeeper.load_var(arg) for arg in cond[1:] ]
            
            if cmd in (b"=", b"==") and args[0] != args[1]:
                return False
                
            elif cmd in (b"!=", b"<>") and args[0] == args[1]:
                return False
                
            elif cmd == b">" and args[0] <= args[1]:
                return False
                
            elif cmd == b"<" and args[0] >= args[1]:
                return False
                
            elif cmd == b">=" and args[0] < args[1]:
                return False
                
            elif cmd == b"<=" and args[0] > args[1]:
                return False
                
        return True
        
        
    def do_cmp(self, var, s, other):
        s = self.varkeeper.unstr( self.varkeeper.load_var(s) )
        other = self.varkeeper.unstr( self.varkeeper.load_var(other) )
        
        if s == other:
            result = 0
            
        elif s > other:
            result = 1
            
        else:
            result = -1
            
        self.varkeeper.do_mov(var, result)
        
        
class VarKeeper(object):
    def __init__(self):
        #~ super(VarKeeper, self).__init__(filename)
        self.numeric_vars = collections.defaultdict(int)
        self.char_vars = collections.defaultdict(str)
        
        self.numalias = dict()
        self.stralias = dict()
        
        
    def load_var(self, var):
        """If the passed argument is a variable, a stralias,
        a numalias, or any combination of these, return the
        value it denotes. Otherwise return it."""
        
        if self.is_name(var):
            return self.unalias(var)
            
        elif type(var) == list and len(var) == 2 and \
        var[0] in "%$":
            
            # The right part of a variable has to be
            # evaluated first.
            # e.g. '%%%0' is valid ONScripter syntax,
            # meaning "the value of the variable 
            # denoted by the value of the variable
            # denoted by the value of the variable
            # denoted by 0". I know, I was shocked too.
            
            var[1] = self.load_var( var[1] )
            
            if var[0] == "%":
                return self.numeric_vars[ var[1] ]
                
            else:
                return self.char_vars[ var[1] ]
                
                
        else:
            return var
            
            
    def abs_var(self, var):
        if type(var[1]) == int:
            return var
            
        else:
            return [var[0], self.load_var(var[1])]
            
            
    def unalias(self, var):
        if var in self.numalias:
            return self.numalias[var]
            
        elif var in self.stralias:
            return self.stralias[var]
            
        return var
        
        
    def do_numalias(self, name, value):
        self.numalias[name] = value
        
        
    def do_stralias(self, name, value):
        self.numalias[name] = value
        
        
    def do_inc(self, var):
        self.do_add(var, 1)
        
        
    def do_dec(self, var):
        self.do_add(var, -1)
        
        
    def do_sub(self, var, num):
        self.do_add(var, -num)
        
        
    def do_add(self, var, num_or_str):
        num_or_str = self.load_var(num_or_str)
        
        if self.is_str(num_or_str):
            s = num_or_str
            var = self.abs_var(var)
            
            self.char_vars[ var[1] ] += s
            
        else:
            num = num_or_str
            var = self.abs_var(var)
            
            self.numeric_vars[ var[1] ] += num
            
            
    def do_mov(self, var, value):
        var = self.abs_var(var)
        
        if self.is_str(value):
            self.char_vars[ var[1] ] = value
            
        else:
            self.numeric_vars[ var[1] ] = value
            
            
    def is_name(self, v):
        return type(v) == str and not self.is_str(v)
        
        
    def is_str(self, v):
        return type(v) == str and v[0] in '"`' and v[0] == v[-1]
        
        
    def unstr(self, s):
        # Remove string markers if it is a string.
        if self.is_str(s):
            s = s[1:-1]
            
        return s
        
        
    def is_color(self, s):
        return type(s) == str and s[0] == "#"
        
        
def variable_loader(f):
    @functools.wraps(f)
    def varloader(self, *args, **kwargs):
        args = map(self.varkeeper.load_var, args)
        
        # I'm running Python 2.6 right now and dict
        # comprehension is introduced in 2.7.
        # Also, note to future me: Be optimistic.
        # Why, you ask? 'Cause it's easier that way.
        kwargs = dict((k, self.varkeeper.load_var(v)) for k, v in kwargs.items())
        
        f(self, *args, **kwargs)
        
    return varloader
    
    
#~ def main():
    #~ if len(sys.argv) != 2:
        #~ print("Usage: onscr_interpreter.py FILENAME")
        #~ exit(1)
        #~ 
    #~ interpreter = SimpleInterpreter( sys.argv[1] )
    #~ interpreter.run()
    #~ 
    #~ 
#~ if __name__ == '__main__':
    #~ main()
