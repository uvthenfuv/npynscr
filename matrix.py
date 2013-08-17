#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       matrix.py
#       
#       Copyright 2011, 2012, 2013 Mark Kolloros <uvthenfuv@gmail.com>
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

"""Common 2-dimensional utility functions and classes."""

from __future__ import division, print_function, unicode_literals

import math # for sqrt
import operator
import functools
import itertools
#~ import collections

import warnings


class _Matrix(object):
    def __init__(self, size):
        self.size = tuple(size)
        
        
    def is_valid(self, pos):
        for d in xrange(2):
            if pos[d] < 0 or pos[d] >= self.size[d]:
                return False
                
        return True
        
        
    def rotate_coords(self, pos, offset):
        assert offset in xrange(4)
        
        if offset == 0:
            return (x, y)
            
        elif offset == 1:
            return (y, self.size-1-x)
            
        elif offset == 2:
            return (self.size-1-x, self.size-1-y)
            
        else:
            return (self.size-1-y, x)
            
            
class CalculateMatrix(_Matrix):
    def __init__(self, filler = None, *args, **kwargs):
        super(CalculateMatrix, self).__init__(*args, **kwargs)
        
        total_size = self.size[0]*self.size[1]
        self._array = [filler for i in xrange(total_size)]
        
        
    def __getitem__(self, pos):
        return self._array[self._get_pos(pos)]
        
        
    def __setitem__(self, pos, value):
        self._array[self._get_pos(pos)] = value
        
        
    def _get_pos(self, pos):
        x, y = pos
        return x*self.size[1] + y
        
        
class ArrayMatrix(_Matrix):
    def __init__(self, filler = None, *args, **kwargs):
        super(ArrayMatrix, self).__init__(*args, **kwargs)
        
        x, y = self.size
        self._array = [ [filler for j in xrange(y)] for i in xrange(x) ]
        
        
    def __getitem__(self, pos):
        x, y = pos
        return self._array[x][y]
        
        
    def __setitem__(self, pos, value):
        x, y = pos
        self._array[x][y] = value
        
        
class DictMatrix(_Matrix):
    def __init__(self, *args, **kwargs):
        super(DictMatrix, self).__init__(*args, **kwargs)
        
        self._dict = dict()
        
        
    def __iter__(self):
        return self._dict.iteritems()
        
        
    def is_empty(self, pos):
        """Returns whether the position is empty. The return value is
        undefined if the position is not valid (i.e. outside bounds)."""
        return tuple(pos) not in self._dict
        
        
    def __getitem__(self, pos):
        return self._dict[tuple(pos)]
        
        
    def __setitem__(self, pos, value):
        assert self.is_valid(pos)
        
        self._dict[tuple(pos)] = value
        
        
    def __delitem__(self, pos):
        del self._dict[tuple(pos)]
        
        
def listmatrix(sizes, filler=None):
    if len(sizes) == 0:
        return filler
        
    elif len(sizes) == 1:
        # a little optimization
        return [filler for i in xrange(sizes[0])]
        
    else:
        return [listmatrix(sizes[1:]) for i in xrange(sizes[0])]
        
        
def yield_between(start, end, size = None):
    # accounts for wrapping around if size is passed
    # includes the endpoint's row and column
    
    if end[0] < start[0] or end[1] < start[1]:
        if size == None:
            raise ValueError("'end' is before 'start' and no size was passed")
            
    elif size == None:
        size = (None, None)
        
    x_iter, y_iter = map(_modrange, start, end, size)
    result = itertools.product(x_iter, y_iter)
    
    return result
    
    
def _modrange(start, end, mod = None):
    # this version includes the endpoint
    if start > end:
        return itertools.chain( xrange(start, mod), xrange(0, end+1) )
        
    else:
        return xrange(start, end+1)
        
        
def side_positions(start, end):
    #~ end = add(start, size, (-1, -1))
    for j in xrange(start[0], end[0]+1):
        yield (j, start[1])
        yield (j, end[1])
    for j in xrange(start[1]+1, end[1]):
        yield (start[0], j)
        yield (end[0], j)
    
    
def matching_scale(size, match_to):
    """Deprecated, consider using min(matrix.div(b, a)) instead."""
    warnings.warn("matching_scale is deprecated", DeprecationWarning)
    
    scales = [match_to[d]/size[d] for d in xrange(2)]
    return min(scales)
    
    
# I didn't realize it would be this trivial
#~ def relative_position(base, pos):
    #~ """relative_position(base, pos) -> the position of pos relative
    #~ to base; the offset needed to move from base to pos."""
    #~ return sub(pos, base)
    
    
def is_between(topleft, bottomright, pos):
    for i in xrange(2):
        if pos[i] < topleft[i]:
            return False
        elif pos[i] > bottomright[i]:
            return False
    return True
    
    
def neighbours((x, y), cardinal=False):
    for xmod in (-1, 0, 1):
        for ymod in (-1, 0, 1):
            cardinal_check = not cardinal or 0 in (xmod, ymod)
            if not xmod == ymod == 0 and cardinal_check:
                #~ yield tuple( add(pos, (xmod, ymod)) )
                yield (x+xmod, y+ymod)
                
                
def add_at(seq, pos, value):
    new = list(seq)
    new[pos] = value
    return new
    
    
def in_area(topleft, size, pos):
    for i in xrange(2):
        if pos[i] < topleft[i]:
            return False
        elif pos[i] >= topleft[i]+size[i]:
            return False
    return True
    
    
def distance((x1, y1), (x2, y2)):
    # using a**2+b**2 = c**2
    return math.sqrt( (x1-x2)**2+(y1-y2)**2 )
    
    
def cartesian((distance, angle)):
    # Convert from polar to cartesian coordinate.
    # https://en.wikipedia.org/wiki/Polar_coordinate_system
    return (distance*math.cos(angle), distance*math.sin(angle))
    
    
def polar((x, y)):
    # Convert from cartesian to polar coordinate.
    return (math.sqrt(x**2+y**2), math.atan2(y, x))
    
    
def list_add(func, *lists):
    """Add the values of the iterables passed together and return them
    as a list. The func argument, if not None, specifies a function to
    use instead of integer addition."""
    
    # No keyword-only arguments in Python 2. : /
    
    if func in (operator.add, None):
        # Default case, optimization
        sumfunc = lambda *x : sum(x)
        
    else:
        sumfunc = lambda *x : functools.reduce(func, x)
        
    return list( map(sumfunc, *lists) )
    
    
def add(*lists):
    return list_add(operator.add, *lists)
    
    
def sub(*lists):
    return list_add(operator.sub, *lists)
    
    
def mul(*lists):
    return list_add(operator.mul, *lists)
    
    
def div(*lists):
    """Divide, returning a list of floats."""
    return list_add(operator.div, map(float, lists[0]), *lists[1:])
    
    
def floordiv(*lists):
    return list_add(operator.floordiv, *lists)
    
    
def mod(*lists):
    return list_add(operator.mod, *lists)
    
    
