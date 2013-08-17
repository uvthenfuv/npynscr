#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       pool.py
#       
#       Copyright 2011, 2012 Mark Kolloros <uvthenfuv@gmail.com>
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

class _SuperPool(dict):
    def __init__(self, loader, *args, **kwargs):
        super(_SuperPool, self).__init__(*args, **kwargs)
        self.loader = loader
        
        
class Pool(_SuperPool):
    def __getitem__(self, i):
        if i not in self:
            self[i] = self.loader(i)
            
        return super(Pool, self).__getitem__(i)
        
        
class DynamicPool(_SuperPool):
    def __call__(self, *args):
        if args not in self:
            self[args] = self.loader(self, *args)
        
        return super(DynamicPool, self).__getitem__(args)
        
