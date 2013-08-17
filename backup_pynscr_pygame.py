#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       pynscr_pygame.py
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
import os
import pygame

import matrix
import pool
import images
import onscr_interpreter


SCRIPT_NAME = "0.txt"

CLICK_BUTTON = 1
SKIP_KEY = pygame.K_s
FULLSCREEN_KEY = pygame.K_f

# View
RESOLUTION = (640, 480)

BORDER_WIDTH_MULTIPLIER = 0.8

DIR_FONT = "default.ttf"
FONT_SIZE = 18

OUTLINE_COLOR = b"#000000"
TEXT_COLOR = b"#ffffff"

# etc
DEBUG_MODE = True



class PygameInterpreter(onscr_interpreter.VarKeeper):
    def __init__(self, resolution, filename):
        super(PygameInterpreter, self).__init__(filename)
        
        # basic setup
        pygame.init()
        self.resolution = resolution
        self.fullscreen_mode = True
        self.toggle_fullscreen()
        
        # graphics
        self.bg = pygame.Surface(self.resolution)
        #~ self.standing_pictures = {'l':None, 'c':None, 'r':None}
        self.standing_pictures = dict()
        
        # pools
        self.colors = pool.Pool(pygame.Color)
        self.images = pool.Pool( images.image_loader(".") )
        self.sprites = pool.Pool( self.load_sprite )
        
        self._setup_text(FONT_SIZE)
        
        # setup
        self.running = False
        self.clearwait = False
        self.skip_mode = False
        
        # buttons
        self.buttons = []
        
        # audio
        self.wavesound = None
        
        
    def _setup_text(self, size):
        if os.path.exists(DIR_FONT):
            font_name = DIR_FONT
            
        else:
            self.error( "No {0}. Falling back to pygame default font.".format(DIR_FONT) )
            font_name = None # pygame default
            
        self.font = pygame.font.Font(font_name, size)
        
        self.text_height = self.font.get_linesize()
        
        border_width = int(self.text_height*BORDER_WIDTH_MULTIPLIER)
        self.text_topleft = [border_width]*2
        txt_area_size = matrix.sub( self.resolution, matrix.mul(self.text_topleft, [2, 2]) )
        self.row_length = txt_area_size[0]
        
        #~ self.text_surface = pygame.Surface(txt_area_size)
        #~ self.text_surface.set_colorkey( self.colors[b"#000000"] )
        #~ self.clear()
        
        # text placing
        self.linenumber = 0
        self.remaining_row = self.row_length
        
        self.text = []
        
        
    def toggle_fullscreen(self):
        if self.fullscreen_mode:
            self.fullscreen_mode = False
            self.screen = pygame.display.set_mode(self.resolution)
            
        elif pygame.display.mode_ok(self.resolution, pygame.FULLSCREEN):
            self.fullscreen_mode = True
            self.screen = pygame.display.set_mode(self.resolution, pygame.FULLSCREEN)
            
        else:
            self.error("Can't switch to full screen mode!")
            
            
    def run(self):
        self.running = True
        while self.running:
            if self.waiting:
                self.user_update()
                
            else:
                if self.clearwait:
                    self.clear()
                    self.clearwait = False
                self.step()
                
            self.update_view()
            
            
    def user_update(self):
        # Events
        for event in pygame.event.get():
            if self.exit_event_check(event):
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.waiting = False
                    self.skip_mode = False
                    
                elif event.key == SKIP_KEY:
                    self.skip_mode = not self.skip_mode
                    
                elif event.key == FULLSCREEN_KEY:
                    self.toggle_fullscreen()
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == CLICK_BUTTON:
                    self.waiting = False
                    self.skip_mode = False
                    
        # Skip mode
        if self.skip_mode:
            self.waiting = False
            
    def exit_event_check(self, event):
        # returns True if the program should exit
        # and False otherwise
        if event.type == pygame.QUIT:
            return True
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                return True
                
        return False
        
        
    def update_view(self):
        # restart from black (not needed)
        #~ self.screen.fill( self.colors[b"#000000"] )
        
        # background
        self.screen.blit( self.bg, (0, 0) )
        
        # sprites
        for topleft, img in self.standing_pictures.itervalues():
            self.screen.blit(img, topleft)
            
        # text display
        for topleft, s in self.text:
            text_size = self.font.size(s)
            text_area = pygame.Rect(topleft, text_size)
            
            # once in black, to outline it
            outline_topleft = matrix.add(topleft, [1, 1])
            text = self.font.render(s, True, self.colors[OUTLINE_COLOR])
            self.screen.blit( text, outline_topleft )
            
            # and once normally
            text = self.font.render(s, True, self.colors[TEXT_COLOR])
            self.screen.blit( text, topleft )
            
        # draw onto the screen
        pygame.display.update()
        
        
    def clear(self):
        #~ self.text_surface.fill( self.colors[b"#000000"] )
        
        self.linenumber = 0
        self.remaining_row = self.row_length
        
        self.text = []
        
        
    def localize_path(self, path):
        s = self.unstr(path)
        path = os.path.join( *s.split("\\") )
        if DEBUG_MODE:
            path = os.path.join("arc", path)
            
        return path.lower()
        
        
    def do_text(self, s):
        if " " in s and s != " ":
            for part in s.partition(" "):
                if part == "":
                    pass
                    
                else:
                    self.do_text(part)
                    
        else:
            # words and spaces
            self.render_word(s)
            
            
    def do_br(self):
        # a linefeed
        self._next_line()
        
        
    def render_word(self, s):
        needed = self.font.size(s)[0]
        
        #~ rendered = self.font.render(s, True, self.colors[TEXT_COLOR])
        
        if needed > self.remaining_row:
            self._next_line()
            
        topleft = self.get_pixelpos(self.linenumber, self.remaining_row)
        topleft = matrix.add(topleft, self.text_topleft)
        
        #~ self.text_surface.blit( rendered, topleft )
        self.text.append( (topleft, s) )
        
        self.remaining_row -= needed
        
        
    def _next_line(self):
        self.linenumber += 1
        self.remaining_row = self.row_length
        
    def do_EOP(self):
        self.waiting = True
        self.clearwait = True
        
        
    def do_select(self, *args):
        self.do_goto( self.selection(args) )
        self.clear()
        
        
    def do_selgosub(self, *args):
        self.do_gosub( self.selection(args) )
        self.clear()
        
        
    def selection(self, args):
        texts = []
        results = []
        for i in xrange( len(args)//2 ):
            texts.append( args[(i*2)] )
            results.append( args[(i*2)+1] )
            
        # User choice
        got = self.text_menu(texts)
        return results[got]
        
        
    def text_menu(self, choices):
        areas = []
        for choice in choices:
            self._next_line()
            areas.append( self.render_text_with_area(choice) )
            
        return self.button_choice(areas)
        
        
    def render_text_with_area(self, text):
        before_linenumber = self.linenumber
        before_row = self.remaining_row
        
        self.do_text(text)
        
        return self.area_between_positions(before_linenumber, \
        before_row, self.linenumber, self.remaining_row)
        
        
    def area_between_positions(self, line_a, row_a, line_b, row_b):
        # This is messy. Maybe I should refactor this.
        
        def global_rect(topleft, width):
            # They have to be global positions
            return pygame.Rect( matrix.add(self.text_topleft, topleft), width )
            
            
        # line_a, row_a has to be before line_b, row_b
        area = []
        
        # first line
        topleft = self.get_pixelpos(line_a, row_a)
        if line_a == line_b:
            width = row_a-row_b
            
        else:
            width = row_a
            
        rect = global_rect( topleft, (width, self.text_height) )
        area.append(rect)
        
        # intermediate lines
        for line in xrange(line_a, line_b-1):
            
            topleft = self.get_pixelpos(line)
            size = (self.row_length, self.text_height)
            
            rect = global_rect(topleft, size)
            area.append(rect)
            
        # final line
        if line_a != line_b:
            topleft = self.get_pixelpos(line_b)
            size = (self.row_length-row_b, self.text_height)
            rect = global_rect(topleft, size)
            area.append(rect)
            
        return area
        
        
    def button_choice(self, areas):
        # button mode
        self.skip_mode = False
        
        while True: # there's a return statement inside
            for event in pygame.event.get():
                if self.exit_event_check(event):
                    exit(0)
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for i in xrange( len(areas) ):
                        area = areas[i]
                        pos = event.pos
                        if is_in_area(area, pos):
                            return i
                            
                            
            self.update_view()
            
            
    def get_pixelpos(self, line, row = None):
        if row == None:
            x = 0
            
        else:
            x = self.row_length-row
            
        y = line*self.text_height
        return (x, y)
        
        
    def do_end(self):
        self.running = False
        
        
    def do_play(self, name):
        name = self.unstr(name)
        try:
            tracknum = int(name[1:])
            
        except ValueError:
            self.error("Music track with name " + track + " not supported!")
            
        namebase = "CD/Track{0:02}".format(tracknum)
        tracknames = [namebase+".mp3", namebase+".ogg"]
        
        for name in tracknames:
            #~ print("Try", name)
            if os.path.exists(name):
                #~ print("Gotcha!")
                pygame.mixer.music.load(name)
                pygame.mixer.music.play(-1)
                break
                
                
    @onscr_interpreter.variable_loader
    def do_waveloop(self, path):
        self.do_wavestop()
        
        path = self.localize_path(path)
        self.wavesound = pygame.mixer.Sound(path)
        self.wavesound.play(-1)
        
        
    @onscr_interpreter.variable_loader
    def do_wave(self, path):
        self.do_wavestop()
        
        path = self.localize_path(path)
        self.wavesound = pygame.mixer.Sound(path)
        self.wavesound.play()
        
        
    def do_stop(self):
        self.do_playstop()
        self.do_wavestop()
        
        
    def do_playstop(self):
        pygame.mixer.music.stop()
        
        
    def do_wavestop(self):
        if self.wavesound != None:
            self.wavesound.stop()
            
            
    @onscr_interpreter.variable_loader
    def do_bg(self, something, effect):
        self.do_cl("a")
        
        if self.is_color(something):
            color = self.colors[something]
            self.bg.fill(color)
            
        elif self.is_str(something):
            path = self.localize_path(something)
            
            self.bg.blit(self.images[path], (0, 0))
            
        else:
            self.error("This kind of BG is not supported currently: " + str(something) )
            
            
    def do_btn(self, num, x, y, w, h, xshift, yshift):
        # Note: xshift and yshift are not implemented
        
        self.buttons.append( (num, (x, y), (w, h)) )
        
        
    def do_btnwait(self, var):
        btns = self.buttons
        self.buttons = []
        
        areas = [ [pygame.Rect(topleft, size)] for num, topleft, size in btns ]
        result = self.button_choice(areas)
        result = btns[result][0] # the zeroth value is the num
        
        self.do_mov(var, result)
        
        
    @onscr_interpreter.variable_loader
    def do_ld(self, pos, description, effect):
        #~ print(pos, description, effect)
        
        sprite = self.sprites[description]
        pos = self.unstr(pos)
        
        # precalculate sprite positions
        x, y = sprite.get_size()
        topleft = [ (self.resolution[0]-x)//2+1, self.resolution[1]-y ]
        
        mod = self.resolution[0]//4
        if pos == "l":
            topleft[0] -= mod
            
        elif pos == "r":
            topleft[0] += mod
            
        # add sprite
        self.standing_pictures[pos] = (topleft, sprite)
        
        
    def load_sprite(self, description):
        description = self.unstr(description)
        alpha, path = description.split(";")
        if alpha != ":a":
            self.error("Unsupported image name: " + description)
            
            placeholder = pygame.Surface( (200, 200) )
            
            return placeholder
            
        else:
            path = self.localize_path(path)
            # we're not using self.images 'cause it shouldn't remember it
            img = pygame.image.load(path)
            x, y = img.get_size()
            img_x = x//2
            
            sprite_size = (img_x, y)
            sprite = pygame.Surface(sprite_size, pygame.SRCALPHA)
            sprite.blit( img, (0, 0) )
            
            alpha = pygame.surfarray.pixels_alpha(sprite)
            
            mask_area = pygame.Rect((img_x, 0), sprite_size)
            mask = img.subsurface(mask_area)
            mask_array = pygame.surfarray.array2d(mask)
            
            # set alpha to distance from (255, 255, 255)
            white_surface = pygame.Surface( mask_area.size )
            white_surface.fill( pygame.Color(b"#ffffff") )
            full_white = pygame.surfarray.array2d(white_surface)
            
            alpha[:] = full_white-mask_array
            
            del alpha # otherwise we can't touch the sprite
            
            return sprite
            
            
    @onscr_interpreter.variable_loader
    def do_cl(self, pos, effect = None):
        pos = self.unstr(pos)
        if pos == "a":
            self.standing_pictures = {}
            
        else:
            del self.standing_pictures[pos]
            
            
def is_in_area(area, pos):
    for rect in area:
        if rect.collidepoint(pos):
            return True
            
    return False
    
    
def main():
    if len(sys.argv) == 2:
        directory = sys.argv[1]
        
    elif len(sys.argv) == 1:
        directory = os.curdir
        
    else:
        print("Usage: pynscr_pygame.py [DIRECTORY]")
        exit(1)
        
    if not os.path.exists(directory):
        print("Specified directory doesn't seem to exist. Exiting.")
        exit(2)
        
    # maybe chdir isn't the best way, but right now it's not important
    os.chdir(directory)
    
    if not os.path.exists(SCRIPT_NAME):
        print("No script found. Exiting.")
        exit(3)
        
    interpreter = PygameInterpreter(RESOLUTION, SCRIPT_NAME)
    interpreter.run()
    
    
if __name__ == '__main__':
    main()
