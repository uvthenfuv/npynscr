#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       images.py
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

import os
import pygame

def image_loader(directory):
    
    def load_image(name):
        path = os.path.join(directory, name)
        
        return load(path)
        
        
    return load_image
    
    
def load(path):
    # taken from the pygame chimp example, modified
    
    image = pygame.image.load(path)
    
    #~ image = image.convert()
    image = image.convert_alpha()
    
    return image
    
    
