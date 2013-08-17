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
import itertools

import matrix
import pool
import images
import onscr_interpreter


SCRIPT_NAME = "0.txt"

CLICK_BUTTON = 1
RBUTTON = 3
SKIP_KEY = pygame.K_s
FULLSCREEN_KEY = pygame.K_f

# View
RESOLUTION = (640, 480)

BORDER_WIDTH_MULTIPLIER = 0.8

DIR_FONT = "default.ttf"
FONT_SIZE = 17

OUTLINE_COLOR = b"#000000"
TEXT_COLOR = b"#ffffff"

# etc
DEBUG_MODE = True



class TextlessInterpreter(onscr_interpreter.InterpreterBase):
    MAX_FPS = 60
    VIEW_UPDATE_FREQ = 1
    
    def __init__(self, resolution, filename):
        super(TextlessInterpreter, self).__init__(filename)
        
        # basic setup
        pygame.init()
        self.resolution = resolution
        self.fullscreen_mode = True
        self.toggle_fullscreen()
        
        # graphics
        self.bg = pygame.Surface(self.resolution)
        
        self.standing_pictures = dict() # valid keys are: 'l', 'c' and 'r'
        self.sprites = dict() # valid keys are numbers in the range 0-999
        
        self.view_cycle = itertools.cycle( xrange(self.VIEW_UPDATE_FREQ) )
        
        self.clock = pygame.time.Clock()
        
        # pools
        self.images = pool.Pool( images.image_loader(".") )
        self.spritepool = pool.Pool( self.load_sprite )
        
        # setup
        self.running = False
        self.skip_mode = False
        
        # audio
        self.wavesound = None
        
        
    def toggle_fullscreen(self):
        if self.fullscreen_mode:
            self.fullscreen_mode = False
            self.screen = pygame.display.set_mode(self.resolution)
            
        elif pygame.display.mode_ok(self.resolution, pygame.FULLSCREEN):
            self.fullscreen_mode = True
            self.screen = pygame.display.set_mode(self.resolution, pygame.FULLSCREEN)
            
        else:
            self.error("Can't switch to fullscreen mode!")
            
            
    def run(self):
        self.running = True
        while self.running:
            self.update()
            
            
    def update(self):
        if self.waiting:
            if next(self.view_cycle) == 0:
                self.update_view()
                
            self.user_update()
            
        else:
            self.step()
            
            
            
    def user_update(self):
        # Events
        for event in pygame.event.get():
            self.check_event(event)
            
        # Skip mode
        if self.skip_mode:
            self.waiting = False
            
    def check_event(self, event):
        if self.exit_event_check(event):
            self.running = False
            
        elif event.type == pygame.KEYDOWN:
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
        self.clock.tick(self.MAX_FPS)
        
        self.draw_everything()
        pygame.display.update()
        
        
    def draw_everything(self):
        # background
        self.screen.blit( self.bg, (0, 0) )
        
        # sprites
        for topleft, img in self.sprites.itervalues():
            self.screen.blit(img, topleft)
            
        # standing pictures
        for topleft, img in self.standing_pictures.itervalues():
            self.screen.blit(img, topleft)
            
            
    def localize_path(self, path):
        s = self.varkeeper.unstr(path)
        path = os.path.join( *s.split("\\") )
        if DEBUG_MODE:
            path = os.path.join("arc", path)
            
        return path.lower()
        
        
    def do_end(self):
        self.running = False
        
        
    def do_play(self, name):
        name = self.varkeeper.unstr(name)
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
        
        if self.varkeeper.is_color(something):
            color = self.colors[something]
            self.bg.fill(color)
            
        elif self.varkeeper.is_str(something):
            path = self.localize_path(something)
            
            self.bg.blit(self.images[path], (0, 0))
            
        else:
            self.error("This kind of BG is not supported currently: " + str(something) )
            
            
    @onscr_interpreter.variable_loader
    def do_ld(self, pos, description, effect):
        #~ print(pos, description, effect)
        
        sprite = self.spritepool[description]
        pos = self.varkeeper.unstr(pos)
        
        # precalculate sprite positions
        x, y = sprite.get_size()
        topleft = [ (self.resolution[0]-x)//2+1, self.resolution[1]-y ]
        
        mod = self.resolution[0]//4
        if pos == "l":
            topleft[0] -= mod
            
        elif pos == "r":
            topleft[0] += mod
            
        # add it
        self.standing_pictures[pos] = (topleft, sprite)
        
        
    @onscr_interpreter.variable_loader
    def do_lsp(self, spriteno, description, x, y, opacity=255):
        if opacity != 255:
            e = "Sprite transparency isn't supported yet"
            info = "; called with {0} {1}".format(description, opacity)
            self.error(e+info)
            
        # load sprite and add it
        sprite = self.spritepool[description]
        topleft = (x, y)
        
        self.sprites[spriteno] = (topleft, sprite)
        
        
    def load_sprite(self, description):
        description = self.varkeeper.unstr(description)
        alpha, path = description.split(";")
        
        path = self.localize_path(path)
        # we're not using self.images 'cause it shouldn't remember it
        img = pygame.image.load(path)
        
        if alpha == ":c":
            # just the image; hurray
            sprite = img
            
        elif alpha == ":a":
            # the right side of the image is an alpha mask
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
            
        else:
            self.error("Unsupported image name: " + description)
            
            placeholder = pygame.Surface( (200, 200) )
            
            return placeholder
            
            
        return sprite
        
        
    @onscr_interpreter.variable_loader
    def do_cl(self, pos, effect = None):
        pos = self.varkeeper.unstr(pos)
        if pos == "a":
            self.standing_pictures = {}
            
        else:
            if pos in self.standing_pictures:
                del self.standing_pictures[pos]
                
            else:
                self.error("!? Asked to delete nonexistent picture.")
                
                
    @onscr_interpreter.variable_loader
    def do_csp(self, spriteno):
        if spriteno == -1:
            self.sprites = {}
            
        else:
            del self.sprites[spriteno]
            
            
class PygameInterpreter(TextlessInterpreter):
    #~ DARKENING_INC = 1
    #~ DARKENING_MAX = 80
    
    def __init__(self, resolution, filename):
        super(PygameInterpreter, self).__init__(resolution, filename)
        
        self.texthandler = TextHandler(self.varkeeper, resolution)
        self.modules.append(self.texthandler)
        
        self.menuhandler = MenuHandler(self.varkeeper, self.texthandler)
        self.modules.append(self.menuhandler)
        
        # setup
        self.clearwait = False
        
        #~ # black filter
        #~ self.darkening = 0
        
        # menu
        #~ self.rmenu = None
        
        # saving
        # normally this should be read in from the savenumber command
        self.savenumber = 20
        self.saves = dict()
        
        
    #~ def check_event(self, event):
        #~ super(PygameInterpreter, self).check_event(event)
        #~ 
        #~ if event.type == pygame.MOUSEBUTTONDOWN:
            #~ if event.button == RBUTTON:
                #~ self.menuhandler.open_rmenu()
                #~ 
                #~ 
    def step(self):
        if self.clearwait:
            self.clear()
            self.clearwait = False
        
        super(PygameInterpreter, self).step()
        
        
    def draw_everything(self):
        super(PygameInterpreter, self).draw_everything()
        
        self.texthandler.render_text(self.screen)
        
        #~ if self.waiting and self.darkening < self.DARKENING_MAX:
            #~ self.darkening += self.DARKENING_INC
            #~ 
        #~ # black filter behind text
        #~ black = pygame.Surface(self.resolution)
        #~ black.set_alpha(self.darkening)
        #~ self.screen.blit( black, (0, 0) )
        
        
    @onscr_interpreter.variable_loader
    def do_rmenu(self, *args):
        # definition of the right-click menu
        args = (self.varkeeper.unstr(a) for a in args)
        # (names, functionality)
        self.rmenu = unpack_args(args)
        
        
    def open_rmenu(self):
        if self.rmenu != None:
            # rmenu mode
            
            # temporarily remove text
            self.swapout_text()
            
            choices, funcs = self.rmenu
            result = self.text_menu(choices, True)
            
            # uses internal counting
            if result >= 0:
                f = funcs[result]
                if f == "skip":
                    self.skip_mode = True
                    
                elif f == "reset":
                    self.do_reset()
                    self.waiting = False
                    
                elif f == "save":
                    self.open_save_menu()
                    
                elif f == "load":
                    #~ self.open_load_menu()
                    pass
                    
                elif f == "end":
                    self.do_end()
                    
                else:
                    self.error("Menu function not implemented yet:"+f)
                    
            # return
            self.swapin_text()
            
            
    def do_reset(self):
        # TODO: reset local variables
        self.clear()
        self.do_game()
        
        
    def open_save_menu(self):
        self.swapout_text()
        
        # This could state data about the save
        slot_name = "Slot {0}"
        choices = [ slot_name.format(i) for i in xrange(self.savenumber) ]
        
        result = self.text_menu(choices, True)
        
        # uses internal counting
        if result >= 0:
            # save to the given slot
            self.save_state(result)
            
        self.swapin_text()
        
        
    def open_load_menu(self):
        pass
        
        
    def save_state(self, slot):
        pass
        #~ 
        #~ self.saves[slot] = save_data
        
        
    def do_EOP(self):
        self.waiting = True
        self.clearwait = True
        
        
    def do_select(self, *args):
        self.do_goto( self.menuhandler.selection(args) )
        self.clear()
        
        
    def do_selgosub(self, *args):
        self.do_gosub( self.menuhandler.selection(args) )
        self.clear()
        
        
class MenuHandler(object):
    def __init__(self, varkeeper, texthandler):
        self.varkeeper = varkeeper
        self.texthandler = texthandler
        
        # buttons
        self.buttons = []
        
        
    def selection(self, args):
        texts, results = unpack_args(args)
        
        # User choice
        got = self.text_menu(texts)
        return results[got]
        
        
    def text_menu(self, choices, accept_rclick = False):
        areas = []
        for choice in choices:
            self.texthandler.next_line()
            areas.append( self.render_text_with_area(choice) )
            
        while True: # loop and a half
            result = self.button_choice(areas)
            # internally we count the choices from 0
            if result >= 0 or accept_rclick:
                break
                
        return result
        
        
    def render_text_with_area(self, text):
        before = self.texthandler.get_textpos()
        
        self.texthandler.do_text(text)
        
        after = self.texthandler.get_textpos()
        
        return self.texthandler.area_between_positions(before, after)
        
        
    def do_btndef(self, name):
        # currently we don't do anything with the name
        
        del self.buttons[:]
        
        
    def do_btn(self, num, x, y, w, h, xshift, yshift):
        # Note: xshift and yshift are not implemented
        
        self.buttons.append( (num, (x, y), (w, h)) )
        
        
    def do_btnwait(self, var):
        areas = [ [pygame.Rect(topleft, size)] for num, topleft, size in self.buttons ]
        
        result = self.button_choice(areas)
        
        # internally the choices are one less than the ones we return
        if result >= 0:
            # the user clicked on a button
            result = self.buttons[result][0] # the zeroth value is the num
            del self.buttons[:]
            
        else:
            # right-click or other exit
            result += 1
            
        self.varkeeper.do_mov(var, result)
        
        
    def button_choice(self, areas):
        # button mode
        self.skip_mode = False
        areacount = len(areas)
        
        while True: # there's a return statement inside
            for event in pygame.event.get():
                if self.exit_event_check(event):
                    exit(0)
                    
                elif event.type == pygame.KEYDOWN:
                    # Hopefully pygame will keep the numbers of
                    # K_0, K_1, ... K_9 sequential
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        # player choices are indexed from 1,
                        # but our area return values are indexed from 0
                        i = event.key-pygame.K_1
                        if i < areacount:
                            return i
                            
                            
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == CLICK_BUTTON:
                        for i in xrange( areacount ):
                            area = areas[i]
                            pos = event.pos
                            if is_in_area(area, pos):
                                return i
                                
                        return -1
                        
                    elif event.button == RBUTTON:
                        # internally we return -2 instead of -1 for right-clicking
                        return -2
                        
            self.update_view()
            
            
class TextHandler(object):
    def __init__(self, varkeeper, resolution):
        self.varkeeper = varkeeper
        
        self.colors = pool.Pool(pygame.Color)
        
        # Font
        if os.path.exists(DIR_FONT):
            font_name = DIR_FONT
            
        else:
            self.error( "No {0}. Falling back to pygame default font.".format(DIR_FONT) )
            font_name = None # pygame default
            
        self.font = pygame.font.Font(font_name, FONT_SIZE)
        
        # pixel positioning
        self.text_height = self.font.get_linesize()
        
        border_width = int(self.text_height*BORDER_WIDTH_MULTIPLIER)
        self.text_topleft = [border_width]*2
        txt_area_size = matrix.sub( resolution, matrix.mul(self.text_topleft, [2, 2]) )
        self.row_length = txt_area_size[0]
        
        # text placing
        self.linenumber = 0
        self.remaining_row = self.row_length
        
        self.text = []
        
        self.text_states = []
        
        
    def render_text(self, surface):
        for topleft, s in self.text:
            text_size = self.font.size(s)
            text_area = pygame.Rect(topleft, text_size)
            
            # once in black, to outline it
            outline_topleft = matrix.add(topleft, [1, 1])
            text = self.font.render(s, True, self.colors[OUTLINE_COLOR])
            surface.blit( text, outline_topleft )
            
            # and once normally
            text = self.font.render(s, True, self.colors[TEXT_COLOR])
            surface.blit( text, topleft )
            
            
    def do_text(self, s):
        if " " in s and s != " ":
            for part in s.partition(" "):
                if part == "":
                    pass
                    
                else:
                    self.do_text(part)
                    
        else:
            # words and spaces
            self.add_word(s)
            
            
    def swapout_text(self):
        # This and swapin_text act like a stack
        state = (self.text, self.linenumber, self.remaining_row)
        self.clear()
        self.text_states.append(state)
        
        
    def swapin_text(self):
        self.clear()
        state = self.text_states.pop()
        self.text, self.linenumber, self.remaining_row = state
        
        
    def do_br(self):
        # a linefeed
        self.next_line()
        
        
    def add_word(self, s):
        needed = self.font.size(s)[0]
        
        if needed > self.remaining_row:
            self.next_line()
            
        topleft = self._get_pixelpos(self.linenumber, self.remaining_row)
        topleft = matrix.add(topleft, self.text_topleft)
        
        self.text.append( (topleft, s) )
        
        self.remaining_row -= needed
        
        
    def _get_pixelpos(self, line, row = None):
        if row == None:
            x = 0
            
        else:
            x = self.row_length-row
            
        y = line*self.text_height
        return (x, y)
        
        
    def next_line(self):
        self.linenumber += 1
        self.remaining_row = self.row_length
        
        
    def clear(self):
        #~ self.text_surface.fill( self.colors[b"#000000"] )
        
        self.linenumber = 0
        self.remaining_row = self.row_length
        
        self.text = []
        
        
    def get_textpos(self):
        return (self.linenumber, self.remaining_row)
        
        
    def area_between_positions(self, before, after):
        # This is messy. Maybe I should refactor this.
        
        line_a, row_a = before
        line_b, row_b = after
        
        def global_rect(topleft, width):
            # They have to be global positions
            return pygame.Rect( matrix.add(self.text_topleft, topleft), width )
            
            
        # line_a, row_a has to be before line_b, row_b
        area = []
        
        # first line
        topleft = self._get_pixelpos(line_a, row_a)
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
        
        
def is_in_area(area, pos):
    for rect in area:
        if rect.collidepoint(pos):
            return True
            
    return False
    
    
def unpack_args(seq):
    seq = list(seq)
    a = []
    b = []
    for i in xrange( len(seq)//2 ):
        a.append( seq[(i*2)] )
        b.append( seq[i*2+1] )
        
    return a, b
    
    
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
