"""Created on Tue Nov 12 09:58:47 2019"""

import pygame
import random
import sys
import csv
from pygame.locals import *
import math
import time
import os
os.chdir("assets")

pygame.mixer.pre_init()
pygame.init()

""" default width, height = 1280, 1024 - ------ 800x600-- on laptop"""
window_width = 1280
window_height = 1024
clock = pygame.time.Clock()

#initialize global variables
items_in_inventory = []
for i in range(25):
    items_in_inventory.append("")
all_sprites = pygame.sprite.LayeredUpdates()
tangible = pygame.sprite.Group()
current_background_layer = None
current_hover_text = []
general_log = ["asd","ddd","sasd","dddsd","asdasd"]
general_log_box = pygame.Surface((500,500), pygame.SRCALPHA)
current_action_box = pygame.Surface((300,75), pygame.SRCALPHA)
current_action = None
highlight_target = False
post_battle = 0
to_dissolve = []
shake_pattern = (5,-10,15,-20,25,-30,35,-35,30,-25,20,-15,10,-5)
party_list = []
enemy_list = []
battle_reward = []
stage_num = 1
possible_allies = ["catboy", "kwiz"]
possible_perks = []
post_boss = False
spell_list = ["barrier", "lightning", "blast", "briar", "beam", "blood_bond", "laser_barrage", "mindblow", "flare", "stalactite", "spray_of_bats", "deflection_shield", "squish", "mend", "soul_leech", "revive", "rejuvenation_wave"]
current_cursor = None
shapes = []
particles = []
briar_duration = 0
briar_dmg = 0
colors = {"red" : ["#bf0000","#af0000","#cf0000","#df0000","#ff0000"], "purple": ["#ad6aff", "#9844ff", "#7f16ff", "#6b00ee", "#5b00c9"]}



basic_commands = ["Attack", "Familiar", "Magic", "Defend", "Item", "Flee"]
current_commands = basic_commands

tips = ["NO WEEENIES ALLOWED", "TRY PLAYING AN EASIER GAME", "BABIES LIKE YOU USUALLY LOSE", "EAT THE RICH"]




class Ally(pygame.sprite.Sprite):
    """player controlled in-battle character"""
    """turn_state: 0 = hasn't gone, 1 = current, 2 = went"""
    
    def __init__(self,name = "naruto"):
        
        global all_sprites
        pygame.sprite.Sprite.__init__(self, self.containers)
        
        #descriptive variables
        party_list.append(self)
        self.name = name
        self.animating = False
        self.loot_xp = 0
        self.stats("init")
        self.hp = self.max_hp
        self.boss = False
        self.shake_count = 0
        self.shake_frame = 0
        self.cast_count = 0
        self.cast_frame = 0
        self.turn_state = 0
        
        
        
        #buffs and debuffs
        self.purge_status()
        
        self.familiars = []
        self.base_spells = ["Flare", "briar", "blast", "beam", "laser_barrage"]
        self.learned_spells = ["soul_leech", "revive", "lightning", "stalactite"]
        if self.name == "kwiz":
            self.job_spells = ["mend"]
        else:
            self.job_spells = []
        self.spell_list = list(set(self.base_spells + self.learned_spells + self.job_spells))
        self.spell_list.sort()
        self.default_pos = (window_width * 0 + party_list.index(self)* 100, window_height * 0.2 - party_list.index(self)* 50)
        self.active_pos = (window_width * 0 + party_list.index(self)* 100 + 200, window_height * 0.2 - party_list.index(self)* 50 + 100)
        

        try:
            self.sheet = pygame.Surface.convert_alpha(pygame.image.load(name +".gif"))
        except:
            self.sheet = pygame.Surface.convert_alpha(pygame.image.load("error_100x100.gif"))
        self.image = self.sheet.subsurface(0, 0, 100, 100)
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (self.rect.width * 3, self.rect.height * 3))
        self.rect = self.image.get_rect()
        
        self.rect.move_ip(self.default_pos)
        all_sprites.change_layer(self, -2)
        
        
        Equipment_slot(self, "head")
        Equipment_slot(self, "chest")
        Equipment_slot(self, "legs")
        Equipment_slot(self, "off")
        Equipment_slot(self, "main")
        Equipment_slot(self, "feet")
        Equipment_tab(self)
        for i in tabs:
            all_sprites.change_layer(i, -2)
        Battle_hud(self)


    def purge_status(self):
        self.barrier_hp = 0
        self.deflection = 0
        self.defending = False
        self.panic = False
        self.leeching = None
        self.leeched = False
        self.afraid = 0
        self.bendy = 0
        self.downed = False
        self.stunned = 0
        self.poisoned = False
        self.fire = 0
        self.bonded = []
        
    def stats(self, arg, add = None):
        if arg == "init":
            self.lvl = 1
            self.xp = int((self.lvl - 1) ** 1.1 + (self.lvl - 1) * 50)
            self.xp_to_lvl = int((self.lvl ** 1.1 + self.lvl * 50) - self.xp)
            self.power = 5
            self.magic = 5
            self.defense = 0
            self.evasion = 0
            self.poison_chance = 0
            self.max_hp = 100
            
        elif arg == "lvl_up":
            self.lvl += 1
            self.xp_to_lvl = int((self.lvl ** 1.1 + self.lvl * 50) - self.xp)
            self.max_hp += 8
            self.hp += 8
            
        elif type(arg) == Item:
            if add == True:
                self.power += arg.power
                self.defense += arg.defense
                self.poison_chance += arg.poison_chance
            elif add == False:
                self.power -= arg.power
                self.defense -= arg.defense
                self.poison_chance -= arg.poison_chance
            print("power: " + str(self.power))
            print("defense: " + str(self.defense))
            
            
            
    def update(self):
        global shake_pattern, current_turn
        if self.shake_count > 0:
            self.shake_count = (self.shake_count + 1) % 71
            if self.shake_count % 5 == 0:
                self.shake_frame += 1
                self.rect.move_ip(shake_pattern[self.shake_count % 14], 0)
                
        
        if self.cast_count > 0:
            self.cast_count = (self.cast_count + 1) % 141
            if self.cast_count % 10 == 0:
                self.cast_frame += 1
                if self.cast_count > 20 and (self.cast_count - 20) % 30 == 0:
                    self.cast_frame -= 3

                if self.cast_count % 140 == 0:
                    self.cast_frame = 0
                    self.cast_count = 0
                    

                
                
                self.image = self.sheet.subsurface(100* self.cast_frame, 0, 100, 100)
                self.rect = self.image.get_rect()
                self.image = pygame.transform.scale(self.image, (self.rect.width * 3, self.rect.height * 3))
                self.rect = self.image.get_rect()
                if current_turn == self:
                    self.rect.move_ip(self.active_pos)
                if self.cast_count % 140 == 0:
                    self.animating = False
                    self.cast_count = 0
                    reset_rect(self)
                    self.rect.move_ip(self.default_pos)
                    
        if self.downed:
            if random.random() > 0.5:    
                self.image = self.sheet.subsurface(0, 100, 100, 100)
            else:    
                self.image = self.sheet.subsurface(100, 100, 100, 100)
                    
        if self.leeched:
            leeches = pygame.transform.scale(pygame.image.load("leeches_overlay.gif"), (300, 300))
            self.image.blit(leeches, (0,0))
    
    
    


class Barricade(pygame.sprite.Sprite):
    """in-battle wall between allies and enemies"""
    def __init__(self, species):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.species = species
        self.image = pygame.image.load(species + ".gif")
        self.reverse = random.getrandbits(1)
        self.size = random.choice([15,25,50,75,100])
        if self.reverse:
            self.image = pygame.transform.flip(self.image, True, False)
        self.image = pygame.transform.scale(self.image, (self.size, self.size))
        self.rect = self.image.get_rect()
        self.rect.move_ip(650 + random.randint(-50,50), 400 +random.randint(-200,200))
        all_sprites.change_layer(self, 13)
        
        


class Battle_hud(pygame.sprite.Sprite):
    """ally-specific info shown during battle"""
    global all_sprites
    def __init__(self, who):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = pygame.image.load("battle_hud.gif")
        self.image = self.image.convert()
        self.rect = self.image.get_rect()

        self.who = who

        self.hp_bar_full = pygame.rect.Rect(25,50,150,25)
        self.hp_bar_empty = pygame.rect.Rect(int(200*(self.who.hp/self.who.max_hp)), 40, 200 -200*(self.who.hp/self.who.max_hp), 30)
        pygame.draw.rect(self.image, "#009f00", self.hp_bar_full)
        pygame.draw.rect(self.image, "#bf0000", self.hp_bar_empty)
        self.rect.move_ip(200 * (len(allies) - 1), 0)
        all_sprites.change_layer(self, -2)
        
    def update(self):
        self.image = pygame.image.load("battle_hud.gif")
        self.image = self.image.convert()
        self.hp_bar_empty = pygame.rect.Rect(25 + int(150*(self.who.hp/self.who.max_hp)), 50, 150 -int(150*(self.who.hp/self.who.max_hp)), 25)
        pygame.draw.rect(self.image, "#009f00", self.hp_bar_full)
        pygame.draw.rect(self.image, "#bf0000", self.hp_bar_empty)

        
        self.image.blit(hud_font.render(self.who.name, False, (255,255,255)), (20, 10))
        self.image.blit(hud_font.render("HP: " + str(self.who.hp), False, (255, 255, 255)), (25,50))
        
        
       
        
        


class Character(pygame.sprite.Sprite):
    """player controlled sprite on overworld"""
    def __init__(self):
        
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = pygame.image.load("character.gif")
        self.rect = self.image.get_rect()
        self.rect.move_ip(50,50)

        
    def move(self,direction):
        if direction == "right" and self.rect.right < window_width - 50:
            self.rect.move_ip(100,0)
        elif direction == "left" and self.rect.left > 50:
            self.rect.move_ip(-100,0)
        elif direction == "down" and self.rect.bottom < window_height - 100:
            self.rect.move_ip(0,100)
        elif direction == "up" and self.rect.top > 50:
            self.rect.move_ip(0,-100)



    def update(self):
        global shake_pattern
        return
        




class Chest(pygame.sprite.Sprite):
    
    def __init__(self, col, row):


        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = pygame.image.load("chest.gif")
        self.rect = self.image.get_rect()
        self.unopened = True
        self.remove(tangible)
        self.rect.move_ip(50,50)
        while pygame.sprite.spritecollideany(self, tangible) != None:
            self.rect.move_ip(random.randint(0,col)*100,random.randint(0,row)*100)
            if self.rect.left >= 2000 or self.rect.top >= 2000:
                while self.rect.left >= 150:
                    self.rect.move_ip(-100,0)
                while self.rect.top >= 150:
                    self.rect.move_ip(0,-100)

        self.add(tangible)


    def on_collide(self):
        if self.unopened == True:
            self.image = pygame.image.load("open_chest.gif")
            if "" in items_in_inventory:
                to_inventory(Item())
                self.unopened = False
                toggle_inventory()
            else:
                general_log.append("You can't hold any more items")

    def update(self):
        return



class Cursor(pygame.sprite.Sprite):
    
    def __init__(self, species, item = None, targets = [], caster = None, action = None):
        global current_cursor
        pygame.sprite.Sprite.__init__(self, self.containers)
        try:
            self.image = pygame.image.load("{0}_cursor.gif".format(species))
        except:
            self.image = pygame.image.load("target_cursor.gif")
        self.rect = self.image.get_rect()
        
        current_cursor = self
        self.species = species
        self.item = item
        self.caster = caster
        self.action = action
        
        
        if species == "target":
            targets = [enemies, allies]
            
            
        elif species == "out_of_battle":
            targets = tabs
            
            
        
        elif species == "reward":
            targets = reward_panels
         
        if species == "menu":
            self.rect.move_ip(10, (round(window_height*0.666,0)))
            self.pos = 0
        else:
            self.target_list = []
            for i in targets:
                #if i is iterable e.g. a sprite group, append all items in group
                if hasattr(i, "__iter__"):
                    for j in i:
                        self.target_list.append(j)
                else:
                    self.target_list.append(i)
            self.target = self.target_list[0]
            self.rect.move_ip(self.target.rect.centerx, self.target.rect.centery - 200)
        
        all_sprites.change_layer(self,13)

            
        
            
    def cycle(self,direction):
        
        if self.species == "menu":
            if direction == 1:
                if self.pos + 1 < len(current_commands):
                    self.pos += 1
                    self.rect.move_ip(0, 40)
                else:
                    self.reset()
            elif direction == 0:
                if self.pos > 0:
                    self.pos -= 1
                    self.rect.move_ip(0, -40)
                else:
                    self.pos = len(current_commands) -1
                    self.rect.move_ip(0, 40* (len(current_commands) -1))
        else:
                
            if direction == 1:
                try:
                    self.target = self.target_list[self.target_list.index(self.target) + 1]             
                except:
                    self.target = self.target_list[0]
                    
            elif direction == 0:
                try:
                    self.target = self.target_list[self.target_list.index(self.target) - 1]             
                except:
                    self.target = self.target_list[-1]
                    
            self.rect.move_ip(-self.rect.left, -self.rect.top)
            self.rect.move_ip(self.target.rect.centerx, self.target.rect.centery - 200)
            
    def reset(self):
        self.pos = 0
        self.rect.move_ip(-self.rect.left, -self.rect.top)
        self.rect.move_ip(10, (round(window_height*0.666,0)))
    
    def update(self):
        return
          

class Enemy(pygame.sprite.Sprite):
    
    def __init__(self, species, col = 0, row = 0, boss = False):
        global battle_log, enemy_list
        pygame.sprite.Sprite.__init__(self, self.containers)
        enemy_info = open("enemies.csv", "r")
        read_data = list(csv.reader(enemy_info))
        del read_data[0]
            
        if species == "random":
            while True:
                self.data = random.choice(read_data)
                if bool(self.data[9]) == False:
                    break
        else:
            for i in read_data:
                   if i[0] == species:
                       self.data = i
                       break

        enemy_info.close()

        #stats and statuses
        enemy_list.append(self)
        self.turn_state = 0
        self.name = self.data[0]
        self.max_hp = int(self.data[1])
        self.hp = int(self.data[1])
        self.power = int(self.data[2])
        self.evasion = float(self.data[3])
        self.defense = float(self.data[4])
        self.xp = int(self.data[5])
        self.poison_chance = float(self.data[6])
        self.magic = int(self.data[7])
        if str(self.data[9]) == "TRUE":
            self.boss = True
        else:
            self.boss = False

        try:
            self.image = pygame.image.load(self.name + ".gif")
        except:
            if self.boss:
                self.image = pygame.image.load("error_150x150.gif")
            else:
                self.image = pygame.image.load("error_100x100.gif")
        self.image = self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.poisoned = False
        self.stunned = 0
        self.bendy = 0
        self.deflection = 0
        self.barrier_hp = 0
        self.afraid = 0
        self.defending = False
        self.sicko = False
        self.angle = 0
        self.rotate = 0
        self.panic = False
        self.leeching = None
        self.leeched = False
        self.fire = 0
        self.bonded = []
        
        

            
        # animation variables
        self.animating = False
        self.pos = self.rect.topleft
        self.shake_frame = 0
        self.shake_count = 0
        self.dissolve_step = 0
        self.dissolved_rows = 0
        
        all_sprites.change_layer(self, 12)
        self.image = pygame.transform.scale(self.image, (self.rect.width * 3, self.rect.height * 3))
        self.rect = self.image.get_rect()
        self.default_pos = (window_width * 0.6 + enemy_list.index(self) * 50, window_height * 0.2 + enemy_list.index(self) * 100)
        self.active_pos = (window_width * 0.6 + enemy_list.index(self) * 50 - 100, window_height * 0.2 + enemy_list.index(self) * 50)
        if self.name != "eyestalk": 
            self.rect.move_ip(self.default_pos)
        
        


        
        
        
    def on_death(self):
        living = 0
        for i in allies:
            living +=1
        for i in allies:
            if i.is_alive:
               i.xp += self.xp // living
        
        
    def turn(self):
        """randomly choose an action attack/spell/whatever"""
        possible_targets = party_list[:]
        for i in possible_targets:
            if i.downed:
                possible_targets.remove(i)
        target = random.choice(possible_targets)
                
        rng = random.random()
        
        if self.name == "bad_dog":
            if rng > 0.8:
                bark(self, target)
            else:
                attack(self,target)
                
        elif self.name == "beelzeboob":
            if  rng > 0.2 and len(enemy_list) < 3:
                malevolent_milking()
            else:
                attack(self,target)
                
                
        elif self.name == "lobster_linguini":
            if rng < 0.3:
                if random.random() >= 0.5:
                    attack(self, target, action = "Noodler", update = False)
                else:
                    attack(self, target, action = "Noodler")
            elif rng >= 0.3 and rng <= 0.6:
                
                target.barrier_hp = 0
                target.deflection = 0
                for i in status_icons:
                    if i.status == "deflection" and i.target == target:
                        i.kill()
                        break
                for i in status_icons:
                    if i.status == "barrier" and i.target == target:
                        i.kill()
                        break
                self.power = self.power * 2
                attack(self, target, action = "Pinch")
                self.power = self.power / 2
            elif rng > 0.9:
                bisque(self)
            else:
                attack(self,target)
                
                
        elif self.name == "mental_illness":
            if self.hp <= self.max_hp / 2 and self.sicko == False:
                sicko_mode(self)
            elif rng < 0.3:
                panic(self)
            elif rng < 0.6:
                sneeze(self, target)
            elif rng < 0.8 and self.sicko == True:
                schizoid_break()
            else:
                attack(self,target)
                
        
        
        
        elif self.name == "snooter":
            if rng > 0.5:
                sneeze(self, target)
            else:
                attack(self,target)
        
        
        
        
                
        
        
        else:
            attack(self,target)
        
        
        
        
    def update(self):
        global shake_pattern
        if self.shake_count > 0:
            self.shake_count = (self.shake_count + 1) % 71
            if self.shake_count % 5 == 0:
                self.shake_frame += 1
                self.rect.move_ip(shake_pattern[self.shake_frame % 14], 0)
        if self.name == "eyestalk":
            if self.rotate == 3:
                fixed_rect = self.rect
                self.angle += random.randint(-1,1)
                self.image = pygame.transform.rotate(pygame.image.load("eyestalk.gif"), self.angle)
                self.image = pygame.transform.scale(self.image, (self.rect.width * 1, self.rect.height * 1))
                self.rect = fixed_rect
                reset_rect(self)
                self.rect.move_ip(self.default_pos)
                self.rotate = 0
            else:
                self.rotate +=1
        if self.leeched:
            leeches = pygame.transform.scale(pygame.image.load("leeches_overlay.gif"), (300, 300))
            self.image.blit(leeches, (0,0))

            

class Equipment_slot(pygame.sprite.Sprite):
    
    def __init__(self, owner, slot):
        global all_sprites, equip_layer
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.owner = owner
        self.slot = slot
        self.index = party_list.index(owner)
        self.image = pygame.image.load("equipment_slot.gif")
        self.rect = self.image.get_rect()
        self.occupied = False
        all_sprites.change_layer(self, -2)
        if slot == "head":
            self.rect.move_ip(equip_layer.rect.left + 184 , equip_layer.rect.top + 2)
        elif slot == "chest":
            self.rect.move_ip(equip_layer.rect.left + 178 , equip_layer.rect.top + 122)
        elif slot == "main":
            self.rect.move_ip(equip_layer.rect.left + 346 , equip_layer.rect.top + 116)
        elif slot == "off":
            self.rect.move_ip(equip_layer.rect.left + 50 , equip_layer.rect.top + 116)
        elif slot == "legs":
            self.rect.move_ip(equip_layer.rect.left + 174, equip_layer.rect.top + 239)
        elif slot == "feet":
            self.rect.move_ip(equip_layer.rect.left + 178, equip_layer.rect.top + 368)
        
        def update(self):
            return
        
        
class Equipment_tab(pygame.sprite.Sprite):
    
    def __init__(self,who):
        
        pygame.sprite.Sprite.__init__(self, self.containers)
        if len(tabs) == 1:
            self.state = "active"
        else:
            self.state = "inactive"
            
        self.who = who
        self.name = who.name
        self.index = len(tabs)
        self.image = pygame.image.load(self.name + "_icon_" + self.state + ".gif")
        self.rect = self.image.get_rect()
        all_sprites.change_layer(self,all_sprites.get_layer_of_sprite(current_background_layer) + 3)
        
        self.rect.move_ip(equip_layer.rect.left + (len(tabs) -1) * 125, equip_layer.rect.bottom)
        
        
        
    def toggle(self):
        """changes which equipment tab is active, shows proper items/slots"""
        global all_sprites, highlight_target
        if highlight_target:
            if highlight_target.equipped:
                highlight_target = False
        if self.state == "active":
            self.state = "inactive"
            for i in equipment_slots:
                if i.owner.name == self.name:
                    all_sprites.change_layer(i, -2)
            for i in items:
                if i.equipped:
                    i.highlighted = False
                    if i.equipped.name == self.name:
                        all_sprites.change_layer(i, -2)
                    
        elif self.state == "inactive":
            self.state = "active"
            for i in equipment_slots:
                if i.owner.name == self.name:
                    all_sprites.change_layer(i,all_sprites.get_layer_of_sprite(current_background_layer) + 3)
            for i in items:
                if i.equipped:
                    if i.equipped.name == self.name:
                        all_sprites.change_layer(i,all_sprites.get_layer_of_sprite(current_background_layer) + 4)
            
        self.image = pygame.image.load(self.name + "_icon_" + self.state + ".gif")

            
            

    def update(self):
        return
        


   
class Item(pygame.sprite.Sprite):
    
    def __init__(self, species = "rand"):
        pygame.sprite.Sprite.__init__(self, self.containers)
        global items_in_inventory, all_sprites

        with open("items.csv") as f: # import data from spreadsheet
            read_data = list(csv.reader(f))
            header = read_data[0]
            del read_data[0]
        
        if species == "rand":
            self.data = random.choice(read_data)
        else:
            for i in read_data:
                if i[0] == species:
                    self.data = i
                    break
        
        
        self.name = self.data[0]
        self.power = int(self.data[2])
        self.defense = int(self.data[3])
        self.poison_chance = float(self.data[4])
        if str(self.data[6]) == "TRUE":
            self.consumable = True
        elif str(self.data[6]) == "FALSE":
            self.consumable = False
        else:
            self.consumable = str(self.data[6])
        self.use_effect = str(self.data[7])
        self.use_value = int(self.data[8])
        self.description = str(self.data[-1])
        
        if self.name == "spell_tome":
            self.spell = random.choice(spell_list)
            self.description += " " + self.spell
            
        
        
        self.highlighted = False
        self.equipped = None
        self.slot = self.data[1]
        if self.slot == "1hand":
            self.slot = ["main","off"]
        elif self.slot == "2hand":
            self.slot = "main"


        self.hover_text = [("  ".join(header[1:-4])),("  ".join(self.data[1:-4])), self.description]
        
        for i in range(len(self.data[-2]) % 40):
            if 40*(i+1) <= len(self.data[-2]):
                self.hover_text.append(self.data[-2][40*i : 40*(i+1)])
            else:
                self.hover_text.append(self.data[-2][40*i :])
                
        try:
            self.image = pygame.image.load(self.name +".gif")
        except:
            self.image = pygame.image.load("error_50x50.gif")    
        self.rect = self.image.get_rect()

#        all_sprites.change_layer(self, all_sprites.get_layer_of_sprite(current_background_layer) + 4)
        all_sprites.change_layer(self, -2)
        
            
        
     
        
            
        
        
    def use(self, target):
        global  battle_log
        if self.use_effect:              
                       
            if self.use_effect == "heal":
                target.hp += self.use_value
                if target.hp > target.max_hp:
                    target.hp = target.max_hp
                if current_background_layer == battle_arena:
                    battle_log.append("The potion mends {0}'s insides".format(target.name))
                else:
                    general_log.append("The potion mends {0}'s insides".format(target.name))
                    
            elif self.use_effect == "damage":
                target.hp -= self.use_value
                if "fire" in self.name:
                    if target.fire == 0:
                        Status_icon("fire", target)
                    target.fire += random.randint(4,8)
                    explosion(target.rect.center)
                    
                    
            elif self.use_effect == "bendy":
                if current_background_layer == battle_arena:
                    Status_icon("bendy",target)
                    target.bendy += self.use_value
                    battle_log.append("{0} starts to wiggle".format(target.name))
                else:
                    return
            
            elif self.use_effect == "learn":
                target.learned_spells.append(self.spell)
                target.spell_list = list(set(target.base_spells + target.learned_spells + target.job_spells))
                target.spell_list.sort()
                general_log.append("{0} learned {1}".format(target.name, self.spell))
            
            
            if self.consumable:
                items_in_inventory.remove(self)
                self.kill()     
            toggle_inventory()

           
        
        
    def update(self):
       return




class Layer(pygame.sprite.Sprite):
    """this class should probably be replaced by actual pygame surfaces"""
    def __init__(self, which):
        global all_sprites
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.image = pygame.image.load(which +".gif")
        self.rect = self.image.get_rect()
        if which == "inventory":
            self.rect.move_ip(window_width//2,5)
            all_sprites.change_layer(self,-2)
        elif which == "background":
            all_sprites.change_layer(self,-1)
        elif which == "battle_menu_bg":
            all_sprites.change_layer(self,-2)
            self.rect.move_ip(0,round(window_height * 0.666, 0))
        
        else:
            all_sprites.change_layer(self, -2)

    def update(self):
        return
    





class Menu_button(pygame.sprite.Sprite):
    
    def __init__(self, pic):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = pygame.image.load(str(pic) + ".gif")
        self.rect = self.image.get_rect()
        if pic == "use_button":
            self.rect.move_ip(inv_layer.rect.right - 60, inv_layer.rect.bottom - 35)
            all_sprites.change_layer(self, -22)
        else:
            self.rect.move_ip(window_width - 100*(len(menu_buttons)), 5)
        

    def update(self):
        return



class NPC(pygame.sprite.Sprite):
    """enemies or neutral interactable entities outside of battle"""
    def __init__(self, species, col = 0, row = 0, boss = False):

        pygame.sprite.Sprite.__init__(self, self.containers)
        self.fighting = False
        self.boss = boss
        enemy_info = open("enemies.csv", "r")
        read_data = list(csv.reader(enemy_info))
        del read_data[0]
            
        if species == "random":
            while True:
                i = random.choice(read_data) 
                if i[9] == "FALSE":
                    self.data = i
                    break
            
        elif species == "boss":

            while True:
                i = random.choice(read_data) 
                if i[9] == "TRUE":
                    self.data = i

                    break
                    
        else:
            for i in read_data:
                   if i[0] == species:
                       self.data = i
                       break

        enemy_info.close()

        self.name = self.data[0]
        try:
            self.image = pygame.image.load(self.name + ".gif")
        except:
            if boss:
                self.image = pygame.image.load("error_150x150.gif")
#                self.image = pygame.image.load("150test.gif")
            else:
                self.image = pygame.image.load("error_100x100.gif")
        self.image = self.image.convert_alpha()
        self.rect = self.image.get_rect()
        

        if col != 0 and row != 0:
            self.remove(tangible)
            if self.boss:
                self.rect.move_ip(25, 25)
            else:
                self.rect.move_ip(50, 50)
            while pygame.sprite.spritecollideany(self, tangible) != None:
                self.rect.move_ip(random.randint(0,col)*100,random.randint(0,row)*100)
                if self.rect.left >= 2000 or self.rect.top >= 2000:
                    while self.rect.left >= 150:
                        self.rect.move_ip(-100,0)
                    while self.rect.top >= 150:
                        self.rect.move_ip(0,-100)
            self.add(tangible)
  
        

    def on_collide(self):
        battle_init(self.name, self.boss)
        self.fighting = True


        
        
    def update(self):
        return
            
        

class Particle():
    """particle effects, e.g. explosions"""
    global particles, colors
    
    def __init__(self, name, color, angle = 360, count = 0, velocity = 50, start_pos = (0,0)):
        """ 0 degree angle points up. increases clockwise"""
        particles.append(self)
        self.name = name
        self.count = count
        self.velocity = velocity
        self.pos = start_pos
        self.rect = pygame.Rect(self.pos[0], self.pos[1], 5, 5)
        self.color = random.choice(colors[color])
        if angle == 180:
            self.angle = random.randint(-90, 90)
        else:
            self.angle = random.randint(0,359)
        if self.name == "explosion":
            self.xvel = math.sin(math.radians(self.angle)) * self.velocity 
            self.yvel = math.cos(math.radians(self.angle)) * self.velocity 
        
    def update(self):
        self.count += 1
        if self.name == "explosion":
            
            if self.count % 2 == 0:    
                self.rect.move_ip(round(self.xvel), -round(self.yvel))
                
                self.xvel = round(self.xvel * 0.9)
                self.yvel -= 5
            
            if self.count >= 20:
                particles.remove(self)
                    
    



class Projectile(pygame.sprite.Sprite):
    """moving sprites used in battle animations"""
    global all_sprites
    
    def __init__(self, name, target, total_frames : int = 0, damage : int = 0, size : int = 25, caster = None):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.name = name
        self.target = target
        self.dmg = damage
        self.caster = caster
        self.sheet = pygame.Surface.convert_alpha(pygame.image.load(self.name + ".gif"))
        self.size = size
        self.image = self.sheet.subsurface(0, 0, size, size)
        self.rect = self.image.get_rect()
        if self.name == "stalactite":
            self.image = self.sheet
            self.image = pygame.transform.scale(self.image, (20,20))
            self.rect = self.image.get_rect()
            self.rect.move_ip(target.rect.centerx - self.rect.width // 2, target.rect.top - 300)
        else:
            self.rect.move_ip(window_width * 0.2 + random.randint(30,340), window_height * 0.2 - random.randint(80,180))
        self.total_frames = total_frames
        all_sprites.change_layer(self, all_sprites.get_layer_of_sprite(target) + 1)
        
        self.count = 1
        self.frame = 0
        self.dx = target.rect.left - self.rect.right
        self.dy = target.rect.centery - self.rect.bottom
        
    
    
    
    def on_hit(self):
        battle_log.append("{0} hits for {1} damage!".format(self.name, self.dmg))
        battle_update(self.target, self.dmg, action = self.name)
        
        
        
        
    def update(self):
        if self.count > 0:
            if self.name == "flare" or self.name =="bat":
            
                self.count = (self.count + 1) % 81
                if self.count % 10 == 0:
                    self.frame += 1
                    if self.count == 80:    
                        self.frame = 0
                        self.kill()
                        self.target.shake_count = 5
                        self.on_hit()
                        return
            
                    self.image = self.sheet.subsurface(self.size* (self.frame % self.total_frames), 0, self.size, self.size)
                    self.rect = self.image.get_rect()
                    self.image = pygame.transform.scale(self.image, (self.rect.width * 3, self.rect.height * 3))
                    self.rect = self.image.get_rect()
                    self.rect.move_ip(100 + ((self.dx * self.frame)/8) + window_width * 0.2, window_height * 0.2 - 100 + ((self.frame * self.dy)/8))

            elif self.name == "stalactite":
                self.count = (self.count + 1) % 151
                if self.count == 150:    
                        self.kill()
                        self.target.shake_count = 5
                        self.on_hit()
                        return
                if self.count % 10 == 0:
                    if self.count < 51:
                        self.image = pygame.Surface.convert_alpha(pygame.image.load(self.name + ".gif"))
                        self.image = pygame.transform.scale(self.image, (60 * self.count // 10, 60 * self.count // 10))       
                        self.rect = self.image.get_rect()
                        reset_rect(self)
                        self.rect.move_ip(self.target.rect.centerx - self.rect.width // 2, self.target.rect.top - 300)
                    elif self.count > 101:
                        self.frame += 1
                        self.rect.move_ip(0, (300//15) * self.frame )


class Reward_panel(pygame.sprite.Sprite):
    """displays reward choices after defeating a boss"""
    global all_sprites
    def __init__(self, reward):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.image = pygame.image.load("reward_panel.gif")
        self.image = self.image.convert()
        self.rect = self.image.get_rect()
        self.panel_num = len(reward_panels) - 1
        self.color = random.choice(["#15f2b0", "#208ae1", "#ef0000", "#ff8619", "#dd5e00", "#ffff00", "#ffffcf", "#77ff4f", "#00ff00", "#0000df", "#48009f", "#ff00ff"])
        self.reward = reward
        pygame.draw.rect(self.image, self.color, (self.rect.left + 10, self.rect.top + 10, self.rect.width - 20, self.rect.height - 20), width = 5)
        
        try:
            self.reward_image = pygame.image.load("{0}.gif".format((reward)))
        except:
            self.reward_image = pygame.image.load("error_100x100.gif")
            
        
            
        self.rect.move_ip((self.panel_num * window_width //3.5 + 100 , window_height // 4))
        
        all_sprites.change_layer(self, all_sprites.get_layer_of_sprite(current_background_layer) + 1)
        
        if type(reward) is Item:
            all_sprites.change_layer(reward, all_sprites.get_layer_of_sprite(current_background_layer) + 2)
            reward.rect.move_ip(self.rect.centerx - 25, self.rect.top + 100)
        elif reward in possible_allies:
            self.reward_image = self.reward_image.subsurface(0, 0, 100, 100)
            self.image.blit(self.reward_image, (self.rect.width // 2 - 50, 100))
            self.image.blit(test_font.render("{0} joins your party".format(reward), True, (255,255,255)), (20, 200))
     
        
        
    def grant_reward(self):
        if self.reward in possible_allies:
            Ally(self.reward)
            possible_allies.remove(self.reward)
            
        elif type(self.reward) == Item:
            to_inventory(self.reward)
        
        for i in items:
            all_sprites.change_layer(i, -2)
    
    def update(self):
        return
        

            
class Shape():
    """non-sprite entites used in battle animations"""
    def __init__(self, name, caster, target, dmg = 0, passed_start_pos = None, count = 1, branch = False):
        global shapes
        self.name = name
        self.target = target
        self.dmg = dmg
        self.caster = caster
        self.count = count
        self.hit = False
        
        
        
        shapes.append(self)
        
        if self.name == "beam":
            self.start_pos = (caster.rect.centerx, caster.rect.centery) 
            self.end_pos = (target.rect.centerx, target.rect.centery)
            self.color = "#bf0000"
            self.width = 1
        
        elif self.name == "point":
            self.rect = pygame.Rect(0,0, 15, 15)
            self.color = "#676767"
            self.rect.move_ip(caster.rect.centerx, caster.rect.centery)
            if shapes.index(self) % 2 == 0:
                self.direction = 1
            else:
                self.direction = -1
                
        elif self.name == "lightning":
            if passed_start_pos:
                self.start_pos = passed_start_pos
            else:
                self.start_pos = (target.rect.centerx, 0) 
            self.end_pos = (target.rect.centerx, target.rect.bottom)
            self.current_pos = self.start_pos
            self.dy = (target.rect.bottom - (self.start_pos[1]//2)) // 15
            self.segments = []
            self.branch = branch
            if self.branch:
                self.xvariance = 75
            else:
                self.xvariance = 30
                
            
        
    def on_hit(self):
        global current_action
        for i in shapes:
            if i.name == "beam":
                return
        else: 
            self.target.shake_count = 5
            battle_update(self.target, self.dmg, action = "Laser Barrage", dmg_type = "magical")
            battle_log.append("{0}'s {1} hit for {2} damage!".format(self.caster.name, current_action, self.dmg))
            
            
        
    def update(self):
        global shapes
        
        if self.name == "beam":
            if self.count > 0:
                self.count = (self.count + 1) % 121
                if self.count == 120:
                    shapes.remove(self)
                    self.on_hit()
                    return
                
                self.color = random.choice(["#bf0000","#af0000","#cf0000","#df0000","#ff0000"])
                if self.count > 30 and self.count < 50 and self.count % 2 == 0:
    
                    self.width += 3
                elif self.count > 90 and self.count < 100 and self.count % 2 == 0:
                    self.width -= 1

        elif self.name == "point":
            if self.count > 0:
                self.count = (self.count + 1) % 201
                if self.count == 200:
                    shapes.remove(self)
                    return
                
                if self.count % 5 == 0 and self.count <= 80:
                    self.rect.move_ip(5 * self.direction, random.randint(-25,15))
                    
                if self.count == 90:
                    Shape("beam", self, self.target, self.dmg)
                    
        elif self.name == "lightning":
            if self.count > 0:
                
                if self.count >= 30:
                    
                    if self.count >= 35:
                        shapes.remove(self)
                        return
                    if self.hit == False:
                        self.segments = []
                        if self.dmg:
                            self.on_hit() 
                        self.hit = True
                    if self.dmg:
                        explosion(self.target.rect.center, color = "purple")
                
                    
                
                elif self.count % 2 == 0:
                    segment_color = random.choice(colors["purple"])
                    self.next_pos = (random.randint(self.target.rect.centerx - self.xvariance, self.target.rect.centerx + self.xvariance), self.current_pos[1] + self.dy)
                    self.segments.append((segment_color, self.current_pos, self.next_pos))
                    
                    if random.random() > 0.8 and self.branch == False:
                        stop_branching = False
                        if random.random() > 0.7:
                            stop_branching = True
                        Shape("lightning", self.caster, self.target, passed_start_pos = self.current_pos, count = self.count + random.randint(4, 10), branch = stop_branching)
                    self.current_pos = self.next_pos
                    
                self.count +=1
                    
                

    
class Stairs(pygame.sprite.Sprite):
    """leads to next stage"""
    def __init__(self, col, row):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.image = pygame.image.load("stairs.gif")
        self.image = self.image.convert()
        self.rect = self.image.get_rect()
        self.locked = True
        self.image.blit(pygame.image.load("lock.gif"), ((25,25)))
        self.remove(tangible)
        self.rect.move_ip(50,50)
        while pygame.sprite.spritecollideany(self, tangible) != None:
            self.rect.move_ip(random.randint(0,col)*100,random.randint(0,row)*100)
            if self.rect.left >= 2000 or self.rect.top >= 2000:
                while self.rect.left >= 150:
                    self.rect.move_ip(-100,0)
                while self.rect.top >= 150:
                    self.rect.move_ip(0,-100)
        self.add(tangible)
        
    def on_collide(self):
        if self.locked == False:
            stage_setup(stage_clear())

    def update(self):
        return



class Status_icon(pygame.sprite.Sprite):
    def __init__(self, status, target):
        global all_sprites, current_background_layer
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.image = pygame.image.load(status + "_icon.gif")
        self.rect = self.image.get_rect()
        self.target = target
        self.status = status
        self.status_num = 0
        
        for i in status_icons:
            if i.target == self.target and self.status != "barrier" and self.status != "deflection":
                self.status_num += 1
            
        

        all_sprites.change_layer(self, all_sprites.get_layer_of_sprite(current_background_layer) + 3)
        
        if status == "fear":
            target.isafraid = True
        elif status == "bendy":
            target.evasion *= 1.5

    def update(self):
        self.rect.move_ip(-self.rect.left, -self.rect.top)
        if self.status != "barrier" and self.status != "deflection":
            self.rect.move_ip(self.target.rect.left + self.status_num * 50, self.target.rect.top - 20)
        else:
            self.rect.move_ip(self.target.rect.right + 10, self.target.rect.top + 30)



class Tile(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.image = pygame.image.load("cobble_tile.gif")
        self.rect = self.image.get_rect()
        all_sprites.change_layer(self, all_sprites.get_layer_of_sprite(current_background_layer)-1)

    def update(self):
        return
    
    
    
class Wall(pygame.sprite.Sprite):
    def __init__(self, orient, col, row):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.image = pygame.image.load(orient + "_wall.gif")
        self.rect = self.image.get_rect()
        
        
        
    def randomize(self, col, row):
        self.remove(tangible)
        while pygame.sprite.spritecollideany(self, tangible) != None:
           self.rect.topleft = (0,0)
           self.rect.move_ip(random.randint(0,col)*100+50,random.randint(0,row)*100+50)
        self.add(tangible)
        
        

    def update(self):
        return




##########################################################################
##########################################################################
############GENERAL GAME FUNCTIONS########################################
##########################################################################
##########################################################################

def act(caster, target = None, action = None):
    global current_cursor

    action = action.lower()
    globals()[action](caster, target)
    for i in cursors:
        i.kill()
    current_cursor = None

    
    
    
    


def battle_init(species, boss):
    global current_background_layer,current_turn, naruto, battle_log, menu_cursor, current_commands, use_button

    Enemy(species, boss)
    
    
    all_sprites.change_layer(battle_arena, 10)
    current_background_layer = battle_arena
    all_sprites.change_layer(battle_menu_bg, 11)
    menu_cursor = Cursor("menu")
    all_sprites.change_layer(menu_cursor, 12)
    for i in battle_huds:
        all_sprites.change_layer(i, 12)
    
    for i in enemies:
        battle_log = ["","","","","You encounter a(n) %s!"%((i.name.replace("_", " ")))]
    
        if "skele" in i.name:
            for j in allies:
                if random.random() > 0.5 and j.afraid == False and j.downed == False:
                    Status_icon("fear", j)
                    j.afraid = True
                    battle_log.append("%s strikes fear into your heart!"% i.name)
    

    for i in allies:
        all_sprites.change_layer(i, 20 - party_list.index(i))
        i.turn_state = 0
    current_turn = naruto
    naruto.turn_state = 1
    naruto.rect.move_ip(200,100)
    
    
    current_commands = basic_commands
    menu_cursor.reset()


    
    for i in menu_buttons:
        if i is not use_button:
            all_sprites.change_layer(i, all_sprites.get_layer_of_sprite(current_background_layer) + 1)


        


def battle_end(condition, boss = False):
    global background, briar_duration, current_cursor, post_boss, current_background_layer, post_battle_layer, all_sprites, battle_arena, battle_menu_bg, menu_cursor, enemy_list, post_battle, battle_reward
    
    
    briar_duration = 0
    for i in allies:
        all_sprites.change_layer(i, -2)
        i.rect.move_ip(-i.rect.left, -i.rect.top)
        i.rect.move_ip(i.default_pos)
    
    if condition == "flee":
        current_background_layer = background
        all_sprites.change_layer(battle_arena, -2)
        all_sprites.change_layer(battle_menu_bg, -2)
        all_sprites.change_layer(menu_cursor, -2)
        for i in battle_huds:
            all_sprites.change_layer(i, -2)
        for i in npcs:
            if i.fighting:
                i.fighting = False
                break
    
        
        
    elif condition == "win":
        
        all_sprites.change_layer(battle_arena, -2)
        all_sprites.change_layer(battle_menu_bg, -2)

        for i in battle_huds:
            all_sprites.change_layer(i, -2)
        post_battle = 1
        current_background_layer = post_battle_layer
        all_sprites.change_layer(post_battle_layer, 10)
        if boss:
            post_boss = True
            for i in tangible:
                if type(i) == Stairs:
                    i.locked = False
                    i.image = pygame.image.load("stairs.gif")
        for i in npcs:
            if i.fighting:
                i.kill()
                break
                
    for i in status_icons:
        i.kill()
    for i in enemies:
        i.kill()
    for i in barricades:
        i.kill()
    
    
    enemy_list = []
    for i in cursors:
        i.kill()
    current_cursor = None
    
    


def battle_update(target = False, dmg = 0, poison_chance = 0, fear_chance = 0, action = None, update = True, dmg_type = "physical"):
    """everything combat related, advances turn order, updates status effects"""
    global to_dissolve, battle_log, current_turn, current_action, current_cursor, briar_duration, briar_dmg
    
    current_action = action

    if type(target) is list:
        for i in target:
            battle_update(target = i, dmg= dmg, poison_chance = poison_chance, fear_chance = fear_chance, action = action, update = False, dmg_type = dmg_type)
        battle_update()
    elif target:
        
        if target.deflection and dmg_type == "physical":
            target.deflection -= 1
            if target.deflection == 0:
                for i in status_icons:
                    if i.status == "deflection" and i.target == target:
                        i.kill()
                        break
            target_list = []
            for i in allies:
                target_list.append(i)
            for i in enemies:
                target_list.append(i)
            target_list.remove(target)
            target = random.choice(target_list)
            
        if target.barrier_hp > 0:
            target.barrier_hp -= dmg
            if target.barrier_hp <= 0:
                battle_log.append(target.name + "'s magical protection dissipates")
                dmg = target.barrier_hp * -1
                target.barrier_hp = 0
                for i in status_icons:
                    if i.status == "barrier" and i.target == target:
                        i.kill()
                        break
        if briar_duration and action == "attack":
            current_turn.hp -= briar_dmg
            battle_log.append("{0} takes {1} damage from brambles".format(current_turn.name, briar_dmg))
        
        
        if poison_chance >= random.random() and target.poisoned == False:
                    target.poisoned = True
                    Status_icon("poison", target)
                    battle_log.append(target.name + " becomes poisoned")
        if fear_chance >= random.random() and not target.afraid:
            target.afraid = 3
            Status_icon("fear", target)
            battle_log.append(target.name + " is scared")
        
        if dmg:
            if target.bonded:
                dmg = dmg // (len(target.bonded) + 1)
            
            target.hp -= dmg
            target.shake_count = 5
            sound_num = random.randint(0,15)
            if sound_num < 10:
                sound_num = "0" + str(sound_num)
            else:
                sound_num = str(sound_num)
            hit_sound = pygame.mixer.Sound("nes-samples/nes-08-%s.wav" % sound_num)
            hit_sound.play()
            
            for i in target.bonded:
                i.hp -= dmg
                i.shake_count = 5
                sound_num = random.randint(0,15)
                if sound_num < 10:
                    sound_num = "0" + str(sound_num)
                else:
                    sound_num = str(sound_num)
                hit_sound = pygame.mixer.Sound("nes-samples/nes-08-%s.wav" % sound_num)
                hit_sound.play()
        
        for i in combatants:
            if i.fire:
                fire_dmg = random.randint(8,12)
                i.hp -= fire_dmg
                battle_log.append("{0} took {1} damage from fire".format(i.name, fire_dmg))
                i.fire -= 1
                if i.fire == 0:
                    for j in status_icons:
                        if j.target == i and j.status == "fire":
                            j.kill()
        if target.hp <= 0:
            target.turn_state = 2
            for i in combatants:
                if i.leeching == target:
                    i.leeching = None
            if type(target) == Enemy:
                enemy_list.remove(target)
                to_dissolve.append(target)
                target.animating = True
                
                if random.random() > 0.5: 
                    battle_reward.append(Item())
            elif type(target) == Ally:
                target.purge_status()
                target.downed = True
                target.remove(combatants)
                
                for i in party_list:
                    if i.downed == False:
                        break
                else:
                    game_over(enemy_list[0].name)
                    return
                        
            
                    
    if update == True:
        for i in combatants:
            if i.turn_state == 1:
                i.turn_state = 2
                if i.name != "eyestalk":
                    i.rect.move_ip(-i.rect.left, -i.rect.top)
                    i.rect.move_ip(i.default_pos)
                
                
                if i.bendy > 0:
                    i.bendy -= 1
                    if i.bendy == 0:
                        i.evasion /= 1.5
                        for j in status_icons:
                            if j.status == "bendy" and j.target == i:
                                j.kill()
                                
                if i.poisoned:
                    battle_log.append(i.name + " took %d damage from poison" % int(i.max_hp / 8))
                    i.hp -= int(i.max_hp / 8)
                    
                if i.afraid:
                    i.afraid -= 1
                
                if i.leeched:
                    suck = i.hp //10
                    i.hp -= suck
                    for j in combatants:
                        if j.leeching == i:
                            j.hp += suck
                            if j.hp > j.max_hp:
                                j.hp = j.max_hp
                            battle_log.append("{0}'s soul leeches sucked {1} HP from {2}".format(j.name, suck, i.name))
                break
            
        for i in combatants:
            if i.turn_state == 0:
                current_turn = i
                i.turn_state = 1
                if i.name != "eyestalk":
                    i.rect.move_ip(-i.rect.left, -i.rect.top)
                    i.rect.move_ip(i.active_pos)
                i.defending = False
                
                if i.stunned > 0:
                    i.stunned -= 1
                    if i.stunned == 0:
                        for j in status_icons:
                            if j.status == "stun" and j.target == i:
                                j.kill()
                    battle_log.append("{0} couldn't move!".format(current_turn.name))
                    battle_update(action = action)
                break
                
        else:
                
            for i in combatants:
                if i.turn_state != 2:
                    break
            else:
                for i in combatants:
                    i.turn_state = 0
                if briar_duration:
                    briar_duration -= 1
                    if briar_duration == 0:
                        for i in barricades:
                            i.kill()
                battle_update(action = action)
        
        if type(current_turn) == Ally:
            if current_turn.downed:
                battle_update(action = action)
    

            
        for i in combatants:
            print("{0} : {1}".format(i.name, i.turn_state))
            print("")


def collide_check(obj, group, direction):
    global all_sprites, current_background_layer
   
    if direction == "right":
        check = Rect(obj.rect.right ,obj.rect.centery, 5, 1)
    elif direction == "left":
        check = Rect(obj.rect.left -5, obj.rect.centery, 6, 1)
    elif direction == "up":
        check = Rect(obj.rect.centerx, obj.rect.top -5,  1, 6)
    elif direction == "down":
        check = Rect(obj.rect.centerx, obj.rect.bottom -1, 1, 6)

    obj.remove(group)
    for i in group:

        if check.colliderect(i.rect):
            obj.add(group)
            if type(i) is Wall:
                return True
            if type(i) is Chest or type(i) is NPC:
                i.on_collide()
            elif type(i) is Stairs:
                i.on_collide()
            obj.add(group)
            return True
    obj.add(group)
    




    

def dev_display(surface,font,mouse_pos):
    """display mouse cursor coordinates"""
    text = font.render("X = {0}    Y = {1}       fps = {2}".format(mouse_pos[0],mouse_pos[1], int(clock.get_fps())), True, (0,0,0))
    surface.blit(text, (200,25))

    
    


def dissolve(target):
    global to_dissolve, current_background_layer, enemy_list
    pix = pygame.PixelArray(target.image)
    # when background image is more complicated, change tuple in current_background_layer.image.get_at((0,0)) to (target.left + x, target.top + y)
    try:
        for i in range(target.rect.width * 4):
            if target.dissolve_step % target.rect.width == 0:
                target.dissolved_rows += 1
            pix[target.dissolve_step - (target.dissolved_rows * target.rect.width), target.dissolve_step //target.rect.width] = current_background_layer.image.get_at((0,0))
            target.dissolve_step += 1
            

    except:
        to_dissolve.remove(target)
        target.animating = False
        for i in allies:
            i.loot_xp += target.xp // len(party_list)
        if target.boss:
            target.kill()
            battle_end("win", boss = True)
            return
        target.kill() 
        
        if len(enemies) == 0:
            battle_end("win")


def explosion(pos, color = "red", size = "medium"):
    if size == "medium":
        for i in range(20):
            Particle("explosion", color, 180, start_pos = pos)
            


def game_over(cause):
    global all_sprites, current_background_layer, death_screen, death_text
    for i in enemies:
        i.kill()
    current_background_layer = death_screen
    all_sprites.change_layer(death_screen, 20)
    death_text = ["YOU LOSE","You died to " + cause.replace("_", " "), "TIP: " + str(random.choice(tips))]



def highlight(target = False):
    global main_surface
    if target:
        pygame.draw.rect(main_surface, (175,175,0), target.rect, 3)
    
    
    
def move_screen(direction):
    global all_sprites
    for i in tangible:
        if direction == "right":
            i.rect.move_ip(-100, 0)
        elif direction == "left":
            i.rect.move_ip(100, 0)
        elif direction == "up":
            i.rect.move_ip(0, 100)
        elif direction == "down":
            i.rect.move_ip(0, -100)
            
            
def reset_rect(obj):
    obj.rect.move_ip(- obj.rect.left, -obj.rect.top)
            
            

def stage_clear():
    global stage_num
    for i in tangible:
        i.kill()
    stage_num += 1
    return stage_num
        


def stage_setup(stage_num = 1):
    global character
    

     #make border walls
    for i in range(2 * (column_num + row_num)):
        if i < (column_num + row_num):
            new_hori = Wall("horizontal", column_num, row_num )
            new_hori.rect.move_ip(50 + 100*i, 50)
            new_vert = Wall("vertical", column_num, row_num)
            new_vert.rect.move_ip(50, 100*i + 50)
        elif i >= (column_num + row_num):
            j = i - (column_num + row_num)
            new_hori = Wall("horizontal", column_num, row_num)
            new_hori.rect.move_ip(50 + 100*j, (row_num)*100 +50)
            new_vert = Wall("vertical", column_num, row_num)
            new_vert.rect.move_ip(50+ 100*(column_num), 100*j + 50)
    
    #make random other walls
    for i in range(150):
        wall_type = random.randint(0,1)
        if wall_type == 1:
            wall_type = "vertical"
        else:
            wall_type = "horizontal"
        new_wall = Wall(wall_type, column_num, row_num)
        new_wall.randomize(column_num, row_num)
        
    #make character, enemies, chests, stairs
    Stairs(column_num , row_num)
    character = Character()
    for i in range(12):
        new_chest = Chest(column_num, row_num)
    if stage_num == 1:
        new_enemy = NPC("mental_illness", column_num, row_num, boss = True)
    elif stage_num == 2:
        new_enemy = NPC("lobster_linguine", column_num, row_num, boss = True)
    else:
        new_enemy = NPC("boss", column_num, row_num, boss = True)
    for i in range(8):
        new_enemy = NPC("random", column_num, row_num)

    
    for i in range(row_num):
        for j in range(column_num):
            new_tile = Tile()
            new_tile.rect.move_ip(50 + 100*i,50+ 100*j)



def to_inventory(item):
    global items_in_inventory, inv_layer
    
    if item not in items_in_inventory:
        if item.highlighted:
            item.highlighted = False
        for i in items_in_inventory:
            if i == "":
                if item.equipped:
                    for j in equipment_slots:
                        if item.rect.collidepoint(j.rect.center) and all_sprites.get_layer_of_sprite(j) > 0:
                            j.occupied = False
                            break
                    item.equipped.stats(item, False)
                    item.equipped = None
                    item.image = pygame.transform.scale(item.image, (50, 50))
                    item.rect = item.image.get_rect()
                item.rect.move_ip(-item.rect.left, -item.rect.top)
                item.rect.move_ip(inv_layer.rect.left + 25 + 100*(items_in_inventory.index(i) % 5), inv_layer.rect.top + 25 + 100*(items_in_inventory.index(i)//5))
                items_in_inventory[items_in_inventory.index(i)] = item
                break



def toggle_equipment():
    global naruto
    if all_sprites.get_layer_of_sprite(equip_layer) < 0:
        all_sprites.change_layer(equip_layer, all_sprites.get_layer_of_sprite(current_background_layer) + 2)
        for i in equipment_slots:
            if i.owner == naruto:
                all_sprites.change_layer(i,all_sprites.get_layer_of_sprite(current_background_layer) + 3)
        for i in items:
            if i.equipped == naruto:
                all_sprites.change_layer(i,all_sprites.get_layer_of_sprite(current_background_layer) + 4)
        for i in tabs:
            all_sprites.change_layer(i,all_sprites.get_layer_of_sprite(current_background_layer) + 4)

            
    else:
        for j in items:
            if j.equipped:
                all_sprites.change_layer(j, -2)
                if j.highlighted:
                    j.highlighted = False
                    highlight_target = False
        all_sprites.change_layer(equip_layer, -2)
        for i in tabs:
            all_sprites.change_layer(i, -2)
        for i in equipment_slots:
            all_sprites.change_layer(i, -2)
            
            
            
def toggle_info():
    global naruto, current_background_layer, info_screen
    if all_sprites.get_layer_of_sprite(info_screen) < 0:
        all_sprites.change_layer(info_screen, all_sprites.get_layer_of_sprite(current_background_layer) + 2)
        current_background_layer = info_screen
    
    else:
        all_sprites.change_layer(info_screen, -2)
        if all_sprites.get_layer_of_sprite(battle_arena) > 0:
            current_background_layer = battle_arena
        else:
            current_background_layer = background

            
 
def toggle_inventory():
    global inv_layer, highlight_target
    if all_sprites.get_layer_of_sprite(inv_layer) < 0:
        all_sprites.change_layer(inv_layer, all_sprites.get_layer_of_sprite(current_background_layer) + 2)
        all_sprites.change_layer(use_button, all_sprites.get_layer_of_sprite(current_background_layer) + 3)
        for j in items:
            if j in items_in_inventory:
                all_sprites.change_layer(j, all_sprites.get_layer_of_sprite(current_background_layer) + 4)
    else:
        all_sprites.change_layer(inv_layer, -2)
        all_sprites.change_layer(use_button, -22)
        highlight_target = False

        for j in items:
            if j in items_in_inventory:
                if j.highlighted:
                    j.highlighted = False
                                                
                all_sprites.change_layer(j, -2)
                

            
            

            
    

##########################################################################
######################Spells and Techniques##############################################
##########################################################################
            
def attack(caster, target, action = "attack", update = True):
    global battle_log
    
    if random.random() > target.evasion:
        damage = int(caster.power * random.uniform(0.8,1.2))
        if caster.afraid:
            damage = damage//2
        damage -= target.defense
        if target.defending:
            damage = damage // 2
        if damage <= 0:
            damage = 0
        damage = int(damage)
        battle_log.append("{0} attacked for {1} damage!".format(caster.name.replace("_"," "), str(damage)))      
    else:
        damage= 0
        battle_log.append("{0}'s attack misses!".format(caster.name))
    return battle_update(target, damage, caster.poison_chance, action = action, update = update)        
            
            
            
def bark(caster, target):
    """insults/provokes enemies into fear"""
    global battle_log
    insults = ["I'd bet this loser spends their free time playing video games", "I'm gonna make you eat my shorts, kid", "Hey kid. Where'd you get your fashion sense, the circus?"]
    battle_log.append(caster.name + ": " + random.choice(insults))
    battle_update(target, fear_chance = 0.5, action = bark.__name__)
    
    
            
def barrier(caster, target):
    """prevents damage from next attack"""
    global battle_log
    target.barrier_hp += caster.magic * random.uniform(0.8, 1.3)
    Status_icon("barrier", target)
    battle_update(action = barrier.__name__)
    
def beam(caster, target):
    if random.random() >= 0.6:
        target.fire += random.randint(3,5)
    dmg = int(caster.magic * random.uniform(1.8, 2.4))
    caster.cast_count = 5
    caster.animating = True
    Shape("beam", caster, target, dmg)    
    
def bisque(caster):
    damage = int(caster.magic * random.uniform(1, 2))
    battle_update(target = party_list, dmg = damage, action = "Bisque", dmg_type = "magic", update = False)
    
def blast(caster, target):
    damage = int(caster.magic * random.uniform(0.9, 1.6))
    battle_update(target, damage, action = "Blast", dmg_type = "magic")
    explosion(target.rect.center)
    
def blood_bond(caster, target):
    """spread incoming damage across self and targets"""
    caster.bonded.append(target)
    target.bonded.append(caster)
    battle_log.append("A spectral bond forms between {0} and {1}".format(caster.name, target.name))
    battle_update(target, action = "Blood Bond")
    
    
def briar(caster, target):
   """causes physical dmg to anyone who attacks"""
   global briar_duration, briar_dmg
   if briar_duration == 0:
       briar_duration = 3
       briar_dmg = int(caster.magic * random.uniform(0.5, 0.9))
       size = random.randint(14, 20)
       for i in range(size):
           Barricade("briar")
       battle_update(action = "Briar")
   else:
       battle_log.append("spell failed!")
       battle_update()
   
    
def bum_rush(caster,target):
    """dmg + self dmg"""
    global battle_log
    damage = int(caster.power * random.uniform(1.8, 2.8))
    self_damage = damage // 3
    caster.hp -= self_damage
    battle_log.append(caster.name + "hurt themselves for {0} damage".format(self_damage))
    battle_update(target, damage, action = bum_rush.__name__)
    
    
def deflection_shield(caster, target):
    global battle_log
    Status_icon("deflection", target)
    battle_update(action = deflection_shield.__name__)
    target.deflection = 3    
    
def flare(caster, target):
    global current_action
    current_action = "Flare"
    caster.cast_count = 5
    caster.animating = True
    Projectile("flare", target, 4, int(caster.magic * random.uniform(1, 1.4)), 50)


def intense_blast(caster, target):
    damage = int(caster.magic * random.uniform(1.6, 3.2))
    battle_update(target, damage, action = "Intense Blast", dmg_type = "magic")
    explosion(target.rect.center)
    
def laser_barrage(caster, target):
    rng = random.randint(0,4)
    dmg_mult = [2.2, 2.4, 2.6, 2.8, 3.0]
    dmg = int(caster.magic * dmg_mult[rng])
    for i in range(rng + 1):
        Shape("point", caster, target, dmg)
    caster.cast_count = 5
    caster.animating = True
    
def lightning(caster, target):
    dmg = int(caster.magic * random.uniform(1.6, 2.0))
    Shape("lightning", caster, target, dmg)
    Shape("lightning", caster, target, 0)
    caster.cast_count = 5
    caster.animating = True
    
def malevolent_milking():
    battle_log.append("Beelzeboob is doing something horrific!")
    Enemy("mayonnaise_elemental")
    battle_update(action = "Malevolent Milking")
    
def mend(caster, target):
    amount = caster.magic * 2
    target.hp += amount
    if target.hp > target.max_hp:
        target.hp = target.max_hp
    battle_log.append("{0} healed {1} by {2}".format(caster.name, target.name, amount))
    battle_update(action = "Mend")
    
    
def mindblow(target):
    global battle_log
    if random.randint(0,1) == 1 and target.stunned == 0:
        battle_log.append("%s is stunned!"% target.name)
        target.stunned = 2
        Status_icon("stun", target)
    else:
        battle_log.append("The spell had no effect")
    battle_update(action = mindblow.__name__)
    
def needle(target):
    damage = 5
    battle_update(target, damage, 0.5, action = needle.__name__)
    
    
def panic(caster):
    caster.stunned = 1
    for i in allies:
        i.panic = True
    battle_update(action = "Panic")
    
def rejuvenation_wave(caster, target):
    for i in combatants:
        amount = int(caster.magic* random.uniform(0.8,1.4))
        i.hp += amount
        if i.hp > i.max_hp:
            i.hp = i.max_hp
        battle_log.append("{0} healed for {1}".format(i.name, amount))
        battle_update(action = "Rejuvenation Wave")
        
    
    
def revive(caster, target):
    if target.downed:
        target.hp = caster.magic * 2
        target.downed = False
        target.add(combatants)
        target.image = pygame.transform.scale(target.sheet.subsurface(0, 0, 100, 100), (300,300))
        target.rect = target.image.get_rect()
        reset_rect(target)
        target.rect.move_ip(target.default_pos)
        
    battle_update(action = "revive")
    
            
def sicko_mode(caster):
    caster.sicko = True
    battle_log.append("{0} transforms".format(caster.name))
    caster.image = pygame.image.load("mental_illness_sicko.gif")
    caster.rect = caster.image.get_rect()
    caster.image = pygame.transform.scale(caster.image, (caster.rect.width * 3, caster.rect.height * 3))
    caster.rect = caster.image.get_rect()
    caster.rect.move_ip(caster.default_pos)
    eye1 = Enemy("eyestalk")
    eye2 = Enemy("eyestalk")
    reset_rect(eye1)
    reset_rect(eye2)
    eye1.default_pos = (caster.rect.left -24, caster.rect.top - 10)
    eye2.default_pos = (caster.rect.left + 90 , caster.rect.top + 40)
    eye1.rect.move_ip(eye1.default_pos)
    eye2.rect.move_ip(eye2.default_pos)
    all_sprites.change_layer(eye1, 11)
    all_sprites.change_layer(eye2, 13)
    battle_update(action = "SICKO MODE")

def schizoid_break():
    Enemy("nervous_nelly")
    battle_update(action = "Schizoid break")
    
def soul_leech(caster, target):
    if target.leeched == False:
        target.leeched = True
        caster.leeching = target
    else:
        battle_log.append("Spell failed!")
    battle_update(action = "Soul Leech")
        
    
def sneeze(caster, target):
    damage = int(caster.magic * random.uniform(0.8,1.2))
    battle_update(target, damage, 0.33, action = "Sneeze")
    
def spray_of_bats(caster, target):
    global current_action
    caster.cast_count = 5
    caster.animating = True
    current_action = "Spray of bats"
    for i in range(random.randint(3, 7)):
        Projectile("bat", target, 3, int(caster.magic / 2), 25)
    

def squish(caster, target):
    global battle_log
    attack_damage = 50 + random.randint(-5,10)
    if attack_damage < 0:
        attack_damage = 0
    battle_log.append("Squish deals {0} damage!".format(attack_damage))
    battle_update(target, attack_damage, action = squish.__name__, dmg_type = "magic")
    

def stalactite(caster, target):
    dmg = int(caster.magic * random.uniform(1.6, 2.1))
    caster.cast_count = 5
    caster.animating = True
    Projectile("stalactite", target, damage = dmg)

    



pygame.display.set_icon(pygame.image.load("icon.gif"))
game_window = pygame.display.set_mode((window_width,window_height))
main_surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
#    column_num = int((window_width/100 -((window_width%100)/100)))
#    row_num = int((window_height/100 - ((window_height%100)/100)))
column_num = 20
row_num = 20
test_font = pygame.font.SysFont("Courier",15)
menu_font = pygame.font.SysFont("Courier",45)
hud_font = pygame.font.SysFont("Courier", 30)
    


    
    #create sprite groups
chests = pygame.sprite.Group()
enemies = pygame.sprite.Group()
items = pygame.sprite.Group()
menu_buttons = pygame.sprite.Group()
walls = pygame.sprite.Group()
highlights = pygame.sprite.Group()
equipment = pygame.sprite.Group()
equipment_slots = pygame.sprite.Group()
status_icons = pygame.sprite.Group()
allies = pygame.sprite.Group()
combatants = pygame.sprite.Group()
tabs = pygame.sprite.Group()
npcs = pygame.sprite.Group()
reward_panels = pygame.sprite.Group()
battle_huds = pygame.sprite.Group()
cursors = pygame.sprite.Group()
barricades = pygame.sprite.Group()


    #assign groups to each sprite class
Character.containers = all_sprites, tangible
Chest.containers = chests, all_sprites, tangible
Enemy.containers = enemies, all_sprites, combatants
NPC.containers = all_sprites, tangible, npcs
Item.containers = items, all_sprites
Menu_button.containers = menu_buttons, all_sprites
Layer.containers = all_sprites
Wall.containers = all_sprites, tangible, walls
Cursor.containers = all_sprites, cursors
Equipment_slot.containers = all_sprites, equipment, equipment_slots
Stairs.containers = all_sprites, tangible
Status_icon.containers = all_sprites, status_icons
Tile.containers = all_sprites
Projectile.containers = all_sprites
Ally.containers = all_sprites, allies, combatants
Equipment_tab.containers = all_sprites, tabs
Reward_panel.containers = all_sprites, reward_panels
Battle_hud.containers = all_sprites, battle_huds
Barricade.containers = all_sprites, barricades





def main():
    
    #initialize surfaces and window, global variables
    global character, post_boss, info_screen, shapes, current_cursor, battle_reward, post_battle_layer, player_turn, post_battle, current_action, target_cursor,targeting, use_button, naruto, background, current_turn, to_dissolve, current_commands, highlight_target, equip_layer, death_text, death_screen, all_sprites,menu_cursor, battle_arena, battle_menu_bg, battle_log, tangible, current_background_layer, cursor, items_in_inventory, walls, inv_layer, chests
   
    frame_count = 0
    player_turn = True
    
    
    #create objects - always spawn walls, then chests, then enemies
    inv_layer = Layer("inventory")
    equip_layer = Layer("equipment_bg")
    background = Layer("background")
    battle_arena = Layer("battle_arena")
    battle_menu_bg = Layer("battle_menu_bg")
    death_screen = Layer("death_screen")
    info_screen = Layer("info_screen")
    post_battle_layer = Layer("post_battle")

    
    stage_setup()
    backpack = Menu_button("backpack")
    equipment = Menu_button("equipment")   
    info_button = Menu_button("info_button")
    use_button = Menu_button("use_button")
    
   

    naruto = Ally("naruto")
    Ally("kwiz")
    Ally("catboy")
    
    #assign layers to sprites
    current_background_layer = background

    for i in items:
        all_sprites.change_layer(i, -2)


    

    #events make stuff happen
    while True:
        """poll for events, key presses, mouse hovering over objects etc and trigger corresponding action"""
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or ev.type == KEYDOWN and ev.key == K_ESCAPE:
                pygame.quit()
                
            if ev.type == USEREVENT:

                if type(current_turn) == Enemy:
                    current_turn.turn()
                    pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                elif current_turn.animating:
                    pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                elif current_turn.panic:
                    current_turn.panic = False
                    act(current_turn, random.choice(list(combatants)), "attack")  
                    current_action = "Panic"
                    pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                else:
                    if enemy_list:
                        player_turn = True
                        menu_cursor = Cursor("menu")
                        current_commands = basic_commands
                    
           

                            
                            
            elif ev.type == KEYDOWN:

                if current_cursor: 
                    if current_cursor.species == "target":
                        if ev.key == K_SPACE:
                            if current_cursor.item:
                                current_cursor.item.use(current_cursor.target)
                                for i in cursors:
                                    i.kill()
                                current_cursor = None
                            elif current_cursor.action:
                                act(target_cursor.caster, target_cursor.target, target_cursor.action)
                            
                                
                            pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                            player_turn = False
                            
                    elif current_cursor.species == "menu":                         
                        if ev.key == K_SPACE:
                            if current_commands[menu_cursor.pos] == "Defend":
                                current_turn.defending = True
                                battle_update()
                                pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                                player_turn = False
                                menu_cursor.kill()
                                current_cursor = None
                                
                            elif current_commands[menu_cursor.pos] == "Back":
                                current_commands = basic_commands
                                menu_cursor.reset()
                                
                            elif current_commands[menu_cursor.pos] == "Flee":
                                battle_end("flee")
                                
                            elif current_commands[menu_cursor.pos] == "Magic":
                                current_commands = current_turn.spell_list.copy()
                                current_commands.append("Back")
                                menu_cursor.reset()
                                
                            elif current_commands[menu_cursor.pos] == "Item":
                                toggle_inventory()
                            else:
                                target_cursor = Cursor("target", caster = current_turn, action = current_commands[menu_cursor.pos])
                                   
                    elif current_cursor.species == "reward":
                        if ev.key == K_SPACE:
                            current_cursor.target.grant_reward()
                            current_cursor = None
                            for i in cursors:
                                i.kill()
                            if current_background_layer == post_battle_layer:
                                current_background_layer = background
                                all_sprites.change_layer(post_battle_layer, -2)
                                post_battle = 0
                            
                            for i in reward_panels:
                                i.kill()
                    
                    elif current_cursor.species == "out_of_battle":
                        if ev.key == K_SPACE:
                            if current_cursor.item:
                                current_cursor.item.use(current_cursor.target.who)
                            elif current_cursor.action:
                                globals()[current_cursor.action](current_cursor.caster, current_cursor.target)
                            for i in cursors:
                                i.kill()
                                current_cursor = None
                            for i in tabs:
                                all_sprites.change_layer(i, -2)

                            
                    if ev.key == K_s or ev.key == K_a:
                        current_cursor.cycle(1)
                        
                    if ev.key == K_w or ev.key == K_d:
                        current_cursor.cycle(0)
                                
                    if ev.key == K_BACKSPACE:
                            current_cursor.kill()  
                            if current_background_layer == battle_arena:
                                menu_cursor = Cursor("menu")
                                
              
                        
                                    
                          #move character after checking for collision
                elif current_background_layer == background and all_sprites.get_layer_of_sprite(equip_layer) < 0 and all_sprites.get_layer_of_sprite(inv_layer) < 0:
                    if ev.key == K_d:
                        if not collide_check(character,tangible, "right"):
                            if character.rect.right + 200 > window_width:
                                move_screen( "right")
                            character.move("right")
                    elif ev.key == K_s:
                        if not collide_check(character,tangible, "down"):
                            if character.rect.bottom + 200 > window_height:
                                move_screen("down")
                            character.move("down")
                    elif ev.key == K_a:
                        if not collide_check(character,tangible, "left"):
                            if character.rect.left - 200 < 100:
                                move_screen("left")
                            character.move("left")
                    elif ev.key == K_w:
                        if not collide_check(character,tangible, "up"):
                            if character.rect.top - 200 < 0:
                                move_screen("up")
                            character.move("up")
                            
                            
                elif all_sprites.get_layer_of_sprite(equip_layer) > 0:
                    if ev.key == K_d:
                        for i in tabs:
                            if i.state == "active" and len(tabs) > 1:
                                i.toggle()
                                if i.index == len(tabs):
                                    for j in tabs:
                                        if j.index == 1:
                                            j.toggle()
                                else:
                                    for j in tabs:
                                        if j.index == i.index + 1:
                                            j.toggle()
                                break
                                           
                        
                        
                        
                        #trigger actions during battle depending on selected command
                if ev.key == K_SPACE:

                    if post_battle == 1:
                        post_battle = 2
                    elif post_battle == 2 and party_list[-1].loot_xp == 0:
                        post_battle = 3
                        for i in battle_reward:
                            i.rect.move_ip(int((window_width //2 -25) - 300*len(battle_reward) + 150*battle_reward.index(i)), window_height // 2 - 25)
                            all_sprites.change_layer(i, all_sprites.get_layer_of_sprite(current_background_layer) + 2)
                    elif post_battle == 3:
                        if post_boss:
                            post_boss = False
                            post_battle = 4
                            boss_rewards = []
                            if len(allies) < 4 and possible_allies:
                                boss_rewards.append(random.choice(possible_allies))
                            while len(boss_rewards) < 3:
                                reward_rng = random.random()
                                if reward_rng >= 0.33:
                                    boss_rewards.append(Item())
                                elif reward_rng <= 0.5:
                                    boss_rewards.append(Item("spell_tome"))
                                else:
                                    try:
                                        """instead of item, tome that teaches spell to party member, or job-changing equipment/ permanent changer?"""
                                        boss_rewards.append(random.choice(possible_perks))
                                    except:
                                        print("oops")
                                
                            for i in boss_rewards:
                                Reward_panel(i)
                            reward_cursor = Cursor("reward")
                                
                        else:
                            post_battle = 0
                            current_background_layer = background
                            all_sprites.change_layer(post_battle_layer, -2)
                        
                        for i in battle_reward:
                            to_inventory(i)
                            all_sprites.change_layer(i, -2)
                        battle_reward = []
                    


                    
                            
                            
            elif ev.type == MOUSEBUTTONDOWN:
                for i in all_sprites:
                    if all_sprites.get_layer_of_sprite(i) >= 0 and i.rect.collidepoint(pygame.mouse.get_pos()):

                        if type(i) is Menu_button:   #open/close inventory/equipment menu and populate each with correct items
                            if i == backpack:
                                toggle_inventory()
                            elif i == equipment:
                                toggle_equipment()
                            elif i == info_button:
                                toggle_info()
                                    
                            elif i == use_button:
                                for j in items:
                                    if j.highlighted == True:
                                        highlight_target = False
                                        j.highlighted = False
                                        toggle_inventory()
                                        if (j.consumable == "battle" and current_background_layer == battle_arena) or (j.consumable == "noncombat" and current_background_layer == background) or j.consumable == True:
                                            if current_background_layer == battle_arena:
                                                target_cursor = Cursor("target", item = j)
                                            else:
                                                target_cursor = Cursor("out_of_battle", item = j)
                                                for i in tabs:
                                                    all_sprites.change_layer(i, all_sprites.get_layer_of_sprite(current_background_layer) + 5)
                            

                        if i is inv_layer:

                            for j in items:
                                if j.rect.collidepoint(pygame.mouse.get_pos()):
                                    break
                            else:
                                for j in items:
                                    if j.highlighted and j.equipped:
                                        highlight_target = False
                                        to_inventory(j)
                                        break
                                
                                
                                
                                
                                
                        if type(i) is Item:   #highlights item upon clicking

                            if i.highlighted == True:
                                i.highlighted = False
                                highlight_target = False
                            else:
                                for j in items:
                                    j.highlighted = False
                                highlight_target = i
                                i.highlighted = True

                                
                        if type(i) is Equipment_slot:  #moves highlighted item to equipment slot
                            if not i.occupied:
                                for k in items:
                                    if k.highlighted == True and not k.equipped and i.slot in k.slot:
                                        k.highlighted = False
                                        k.image = pygame.transform.scale(k.image, (100,100))
                                        k.rect = k.image.get_rect()
                                        k.rect.move_ip(i.rect.topleft)
                                        k.equipped = i.owner
                                        i.occupied = True
                                        items_in_inventory[items_in_inventory.index(k)] = ""
                                        i.owner.stats(k, True)
                                        break
                            highlight_target = False
                        

                        
                        if type(i) is Reward_panel:
                            i.grant_reward()
                            if current_background_layer == post_battle_layer:
                                current_background_layer = background
                                all_sprites.change_layer(post_battle_layer, -2)
                                post_battle = 0
                            
                            for i in reward_panels:
                                i.kill()
                            for i in cursors:
                                i.kill()
                            current_cursor = None
 
    
                                
            else:    #display tooltip/hovertext
                for i in all_sprites:
                    if i.rect.collidepoint(pygame.mouse.get_pos()) and all_sprites.get_layer_of_sprite(i) > 0:
                        if type(i) is Item:
                            current_hover_text = i.hover_text
                            break
                    else:
                        current_hover_text = []

                        
          
        



        #draw what needs to be drawn

        game_window.blit(main_surface, (0,0))
        main_surface.fill("#01563f")   
        all_sprites.update()
        for i in shapes:
            i.update()
        
        all_sprites.draw(main_surface)
        highlight(highlight_target)
        
        if current_background_layer == battle_arena:

            for i in range(5):
                main_surface.blit(test_font.render(battle_log[-5 + i], True, (255,255,255)), (round(window_width*0.6666,0), 20*i + round(window_height*0.666,0)))
            for i in range(len(current_commands)):
                main_surface.blit(menu_font.render(current_commands[i], True, (255,255,255)), (60, 40*i + round(window_height*0.666,0)))
            if current_action and current_action != "attack":
                current_action_box.fill((127,127,127,150))
                render = test_font.render(current_action, True, (255,255,255))
                current_action_rect = current_action_box.get_rect()
                current_action_box.blit(render, (current_action_rect.centerx - render.get_size()[0] / 2, current_action_rect.centery - render.get_size()[1] / 2 ))
                main_surface.blit(current_action_box,(round(window_width*0.5) - 150, 0))
            
            
            for i in particles:
                i.update()
                pygame.draw.rect(main_surface, i.color, i.rect)
            for i in shapes:
                if i.name == "beam":
                    pygame.draw.line(main_surface, i.color, i.start_pos, i.end_pos, i.width)
                elif i.name == "point":
                    pygame.draw.rect(main_surface, i.color, i.rect)
                elif i.name == "lightning":
                    for j in i.segments:
                        pygame.draw.line(main_surface, j[0], j[1], j[2], 4)

                
        elif current_background_layer == death_screen:

            main_surface.blit(menu_font.render(death_text[0], True, (255,255,255)), (round(window_width*0.45, 0), round(window_height*0.25, 0)))
            main_surface.blit(menu_font.render(death_text[1], True, (255,255,255)), (round(window_width*0.33, 0), round(window_height*0.45,0)))
            main_surface.blit(menu_font.render(death_text[2], True, (255,255,255)), (round(window_width*0.25, 0), round(window_height*0.666,0)))
            
            
        elif current_background_layer == background:
            main_surface.blit(general_log_box,(round(window_width*0.666), round(window_height * 0.8)))
            general_log_box.fill((0,0,0,150))

            for i in range(5):
                main_surface.blit(test_font.render(general_log[-5 + i], True, (255,255,255)), (round(window_width*0.6666,0), 20*i + round(window_height*0.8,0)))
            
        elif current_background_layer == info_screen:
            for i in allies:
                main_surface.blit(pygame.image.load(i.name + ".gif").subsurface(0, 0, 100, 100), (150*party_list.index(i), 25))
            
            
            
            
        if post_battle > 0:
            
            
            if post_battle < 3:      
                main_surface.blit(menu_font.render("Reward:  " + str(naruto.loot_xp), True, (255,255,255)), (round(window_width*0.1 + 200, 0), round(window_height * 0.1 - 50, 0)))
                for i in allies:
                    main_surface.blit(menu_font.render((i.name), True, (255,255,255)), (round(window_width*0.1, 0), round(window_height * 0.1 + 200*party_list.index(i), 0)))
                    main_surface.blit(menu_font.render(("    Level: " + str(i.lvl)), True, (255,255,255)), (round(window_width*0.1, 0), round(window_height * 0.1 + 200*party_list.index(i) + 50, 0)))
                    main_surface.blit(menu_font.render(("EXP: " + str(i.xp)), True, (255,255,255)), (round(window_width*0.5, 0), round(window_height * 0.1 + 200*party_list.index(i), 0)))
                    main_surface.blit(menu_font.render((("EXP to level: " + str(i.xp_to_lvl))), True, (255,255,255)), (round(window_width*0.5, 0), round(window_height * 0.1 + 200*party_list.index(i) + 50, 0)))
                if post_battle == 2:
                    for i in allies:
                        if i.loot_xp > 0 and frame_count % 3 == 0:
                            i.loot_xp -= 1
                            i.xp += 1
                            i.xp_to_lvl = int((i.lvl ** 1.1 + i.lvl * 50) - i.xp)
                        if i.xp_to_lvl == 0:
                            i.stats("lvl_up")
            elif post_battle == 3:
                
                main_surface.blit(menu_font.render("You found:", True, (255,255,255)), (window_width // 3, int(window_height * 0.4)))
                
            elif post_battle == 4:
                main_surface.blit(menu_font.render("THERE CAN BE ONLY ONE", True, (255,255,255)), (window_width // 3 - 100, int(window_height * 0.1)))
                

                
            
        dev_display(main_surface,test_font,pygame.mouse.get_pos())
        for i in current_hover_text:
            if pygame.mouse.get_pos()[0] < 700:
                main_surface.blit(test_font.render(i, True, (255,255,255)), (pygame.mouse.get_pos()[0] - 100, pygame.mouse.get_pos()[1] + (30 * current_hover_text.index(i))))
            else:
                main_surface.blit(test_font.render(i, True, (255,255,255)), (700, pygame.mouse.get_pos()[1] + (30 * current_hover_text.index(i))))
           
        if len(to_dissolve) != 0:
            for i in to_dissolve:
                dissolve(i)
        

        pygame.display.flip()
        
        frame_count += 1
        
        """limit to 60 fps"""
        clock.tick(60)
    
    
    pygame.quit()
    
main()

#################################################################
#################  NOTES TO SELF  ###############################
#################################################################
"""TO DO"""
""" splash screen my face on naruto"""
"""taking stairs actually changes which enemies will spawn etc"""
"""more spells"""
"""job system"""
"""currency nuggies, shop/poopsmith"""
"""properly scale everything on different resolutions -consider setting game_window.display.set_mode to 0,0 instead of resoultion"""
"""djinn/class system - change job via loader (neuromancer style microsoft)"""
"""instead of elemental types/weaknesses use pierce/bludgeon/slash"""
"""entomb spell, encases in rock, stuns for a while"""
"""do something on overworld instead of just move?"""
"""retry button on game over screen"""
"""have several battle_arena background images"""
"""improve look of item hover text"""
"""make item drops not 100% random"""
"""sometimes an invisible wall blocks movement on overworld"""
"""update older sprites to color palette"""
"""should overworld grid be arranged as an array? each tile would then be directly modifiable"""
"""elemental and status  weakness/resistance"""
"""adjust loot drops to be enemy specific?"""
"""more items/loot"""
"""mkae list of possible encounters/enemy combinations"""
"""dialog box + avatar of speaker"""
"""make iron mask actually give fear immunity"""
"""items that change class"""
"""hemomancer class: summons units at cost of hp, like hemomancer from rabbits vs sheep"""
"""four elements for djinn/familiars - life/bio, death, energy, metal/earth/inanimate/inorganic"""
"""speech bubbles in combat responding to events e.g. on fear "jesus christ how horrifying"""


"""ALLY IDEAS"""
"""goblin joe"""

"""ENEMY IDEAS"""
"""beefy boy"""
""" bad dog uses wheeze?"""
"""protect spell"""
"""stall tactics"""
"""damage based on % of player hp"""

"""TOP PRIORITY"""
"""make intense blast trigger explosion multiple times"""
"""job system"""
"""laser barrage fucks turn order if used before enemy turn"""
"""djinn"""
"""more spells"""
"""status screen like golden sun"""
"""turn system like FFX, each action adds a number of ticks to combatants (modified by speed stat), ticks count down until the next turn happens"""

