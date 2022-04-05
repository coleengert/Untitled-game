"""Created on Tue Nov 12 09:58:47 2019"""

import pygame
import random
import sys
import csv
from pygame.locals import *
import math


""" default width, height = 1280, 1024 - ------ 800x600-- on laptop"""
window_width = 1280
window_height = 1024
clock = pygame.time.Clock()


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
post_battle_screen = pygame.Surface((1280,1024), pygame.SRCALPHA)
highlight_target = False
post_battle = 0
to_dissolve = []
shake_pattern = (5,-10,15,-20,25,-30,35,-35,30,-25,20,-15,10,-5)
party_list = []
enemy_list = []
stage_num = 1





basic_commands = ["Attack", "Technique", "Magic", "Defend", "Item", "Flee"]
magic_commands = ["Squish", "Mindblow", "Flare", "Back"] #need to make per-character
current_commands = basic_commands

tips = ["NO WEEENIES ALLOWED", "TRY PLAYING AN EASIER GAME", "BABIES LIKE YOU USUALLY LOSE", "EAT THE RICH"]
hp_bar_full = pygame.rect.Rect(100, 50, 300, 25)
hp_bar_empty = pygame.rect.Rect(0, 0, 0, 0)


# initialize stats
nugs = 5

hp_display = "HP:" + "50"








class Ally(pygame.sprite.Sprite):
    """turn_state: 0 = hasn't gone, 1 = current, 2 = went"""
    
    def __init__(self,name = "naruto"):
        
        global all_sprites
        
        
        
        party_list.append(self)
        self.name = name
        self.animating = False
        self.loot_xp = 0
        self.stats("init")
        self.hp = self.max_hp
        self.downed = False
        self.stunned = 0
        self.poisoned = False
        self.afraid = False
        self.bendy = 0
        self.shake_count = 0
        self.shake_frame = 0
        self.cast_count = 0
        self.cast_frame = 0
        self.turn_state = 0
        self.defending = False
        self.default_pos = (window_width * 0 + party_list.index(self)* 100, window_height * 0.2 - party_list.index(self)* 50)
        self.active_pos = (window_width * 0 + party_list.index(self)* 100 + 200, window_height * 0.2 - party_list.index(self)* 50 + 100)
        pygame.sprite.Sprite.__init__(self, self.containers)


        self.sheet = pygame.Surface.convert_alpha(pygame.image.load(name +".gif"))
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




    def attack(self, target):
        global battle_log
        
        if random.random() > target.evasion:
            attack_damage = int(self.power * random.uniform(0.8,1.2))
            if self.afraid:
                attack_damage = attack_damage//2
            if attack_damage < 0:
                attack_damage = 0
            else:
                target.shake_count = 5
            battle_log.append("You attack for {0} damage!".format(attack_damage))
            
        else:
            attack_damage = 0
            battle_log.append("Your attack misses")
        return battle_update(target, attack_damage, self.poison_chance)


    def update(self):
        global shake_pattern, flare_particle
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
                if self.cast_count == 30:
                    flare_particle.count = 5
                if self.cast_count % 140 == 0:
                    self.cast_frame = 0
                    self.cast_count = 0
                    
                    attack_damage = int(self.magic * random.uniform(1, 1.4))
                    flare_particle.on_hit(attack_damage)
                
                
                self.image = self.sheet.subsurface(100* self.cast_frame, 0, 100, 100)
                self.rect = self.image.get_rect()
                self.image = pygame.transform.scale(self.image, (self.rect.width * 3, self.rect.height * 3))
                self.rect = self.image.get_rect()
                self.rect.move_ip(self.active_pos)
                if self.cast_count % 140 == 0:
                    self.animating = False
                    self.cast_count = 0
                    
                    
                
    
    
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




class Character(pygame.sprite.Sprite):
    
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
            Item()
            self.unopened = False
            toggle_inventory()

    def update(self):
        return



class Cursor(pygame.sprite.Sprite):
    
    def __init__(self, species, what = None):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = pygame.image.load("{0}_cursor.gif".format(species))
        self.rect = self.image.get_rect()
        
        
        if species == "menu":
            self.rect.move_ip(10, (round(window_height*0.666,0)))
            self.pos = 0
        
        elif species == "target":
            self.what = what
            self.target_list = []
            for i in enemies:
                self.target_list.append(i)
            for i in allies:
                self.target_list.append(i)

            self.target = self.target_list[0]
            
            all_sprites.change_layer(self,13)
            self.rect.move_ip(self.target.rect.centerx, self.target.rect.centery - 200)


            
            
    def cycle(self,direction):
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
    
    def __init__(self, species, col = 0, row = 0):
        global battle_log, enemy_list
        pygame.sprite.Sprite.__init__(self, self.containers)
        enemy_info = open("enemies.csv", "r")
        read_data = list(csv.reader(enemy_info))
        del read_data[0]
            
        if species == "random":       
            self.data = random.choice(read_data)
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
        self.dmg = int(self.data[2])
        self.evasion = float(self.data[3])
        self.defense = float(self.data[4])
        self.xp = int(self.data[5])
        self.poison_chance = float(self.data[6])
        self.magic = int(self.data[7])
        try:
            self.image = pygame.image.load(self.name + ".gif")
        except:
            self.image = pygame.image.load("error_100x100.gif")
        self.image = self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.poisoned = False
        self.stunned = 0
        self.bendy = 0
        self.afraid = False
        
        

            
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
        self.rect.move_ip(self.default_pos)
        
        

        
        
    def turn(self):
        """randomly choose an action attack/spell/whatever"""
        
        target = random.choice(party_list)
        rng = random.random()
        if self.name == "snooter":
            if rng > 0.5:
                sneeze(self, target)
            else:
                self.attack(target)
        
        elif self.name == "beelzeboob":
            if  rng > 0.2 and len(enemy_list) < 3:
                malevolent_milking()
            else:
                self.attack(target)
        
        
        
        else:
            self.attack(target)


        
        

    def attack(self, target):
        global battle_log, hp, max_hp, hp_bar_empty, hp_display
        
        if random.random() > target.evasion:
            damage = random.randint(int(self.dmg * 0.8), int(self.dmg * 1.2))
            if self.afraid:
                damage = damage//2
            damage -= target.defense
            if target.defending:
                damage = damage // 2
            if damage <= 0:
                damage = 0
            else:
                target.shake_count += 5
            battle_log.append("{0} attacked for {1} damage!".format(self.name.replace("_"," "), str(damage)))
            target.hp -= damage
            if target.hp <= 0 :
                death(self.name)
            else: 
                hp_bar_empty = pygame.rect.Rect(100 + 300*(target.hp/target.max_hp), 50, 300 -300*(target.hp/target.max_hp), 25)
                hp_display = "HP:" + str(target.hp)
        else:
            battle_log.append("{0}'s attack misses!".format(self.name))
        return battle_update(target, damage, self.poison_chance)
        
        
    def on_death(self):
        living = 0
        for i in allies:
            living +=1
        for i in allies:
            if i.is_alive:
               i.xp += self.xp // living
        
        
    def update(self):
        global shake_pattern
        if self.shake_count > 0:
            self.shake_count = (self.shake_count + 1) % 71
            if self.shake_count % 5 == 0:
                self.shake_frame += 1
                self.rect.move_ip(shake_pattern[self.shake_frame % 14], 0)
            

class Equipment_slot(pygame.sprite.Sprite):
    
    def __init__(self, owner, slot):
        global all_sprites, equip_surface
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.owner = owner
        self.slot = slot
        self.index = party_list.index(owner)
        self.image = pygame.image.load("equipment_slot.gif")
        self.rect = self.image.get_rect()
        self.occupied = False
        all_sprites.change_layer(self, -2)
        if slot == "head":
            self.rect.move_ip(equip_surface.rect.left + 184 , equip_surface.rect.top + 2)
        elif slot == "chest":
            self.rect.move_ip(equip_surface.rect.left + 178 , equip_surface.rect.top + 122)
        elif slot == "main":
            self.rect.move_ip(equip_surface.rect.left + 346 , equip_surface.rect.top + 116)
        elif slot == "off":
            self.rect.move_ip(equip_surface.rect.left + 50 , equip_surface.rect.top + 116)
        elif slot == "legs":
            self.rect.move_ip(equip_surface.rect.left + 174, equip_surface.rect.top + 239)
        elif slot == "feet":
            self.rect.move_ip(equip_surface.rect.left + 178, equip_surface.rect.top + 368)
        
        def update(self):
            return
        
        
class Equipment_tab(pygame.sprite.Sprite):
    
    def __init__(self,name):
        
        pygame.sprite.Sprite.__init__(self, self.containers)
        if len(tabs) == 1:
            self.state = "active"
        else:
            self.state = "inactive"
        
        self.name = name
        self.index = len(tabs)
        self.image = pygame.image.load(self.name + "_icon_" + self.state + ".gif")
        self.rect = self.image.get_rect()
        all_sprites.change_layer(self,all_sprites.get_layer_of_sprite(current_background_layer) + 3)
        
        self.rect.move_ip(equip_surface.rect.left + (len(tabs) -1) * 125, equip_surface.rect.bottom)
        
        
        
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
        if str(self.data[7]) == "TRUE":
            self.consumable = True
        else:
            self.consumable = False
        self.use_effect = str(self.data[7])
        self.use_value = int(self.data[8])
        
        
        self.highlighted = False
        self.equipped = None
        self.slot = self.data[1]
        if self.slot == "1hand":
            self.slot = ["main","off"]
        elif self.slot == "2hand":
            self.slot = "main"


        self.hover_text = [("  ".join(header[1:-4])),("  ".join(self.data[1:-4])), str(self.data[-1])]
        
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

        all_sprites.change_layer(self, all_sprites.get_layer_of_sprite(current_background_layer) + 4)
        if "" in items_in_inventory:
            to_inventory(self)
            
        
     
        
            
        
        
    def consume(self, target):
        global  battle_log
        if self.consumable == True:
            if self.use_effect == "heal":
                target.hp += self.use_value
                if target.hp > target.max_hp:
                    target.hp = target.max_hp
                if current_background_layer == battle_arena:
                    battle_log.append("The potion mends your insides")
                    
            elif self.use_effect == "bendy":
                if current_background_layer == battle_arena:
                    Status_icon("bendy",target)
                    target.bendy += self.use_value
                    
            items_in_inventory.remove(self)
            self.kill()        
                #code for use out of battle here
            
            
                    
        
        
    def update(self):
       return

class Menu_button(pygame.sprite.Sprite):
    
    def __init__(self, pic):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = pygame.image.load(str(pic) + ".gif")
        self.rect = self.image.get_rect()
        if pic == "use_button":
            self.rect.move_ip(inv_surface.rect.right - 60, inv_surface.rect.bottom - 35)
            all_sprites.change_layer(self, -22)
        else:
            self.rect.move_ip(window_width - 100*(len(menu_buttons)), 5)
        

    def update(self):
        return



class NPC(pygame.sprite.Sprite):
    
    def __init__(self, species, col = 0, row = 0):

        pygame.sprite.Sprite.__init__(self, self.containers)
        self.fighting = False
        enemy_info = open("enemies.csv", "r")
        read_data = list(csv.reader(enemy_info))
        del read_data[0]
            
        if species == "random":       
            self.data = random.choice(read_data)
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
            self.image = pygame.image.load("error_100x100.gif")
        self.image = self.image.convert_alpha()
        self.rect = self.image.get_rect()
        

        if col != 0 and row != 0:
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
        battle_init(self.name)
        self.fighting = True


        
        
    def update(self):
        return
            
        





class Particle(pygame.sprite.Sprite):
    global all_sprites
    def __init__(self, which, target):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.sheet = pygame.Surface.convert_alpha(pygame.image.load(which + ".gif"))
        self.image = self.sheet.subsurface(0, 0, 50, 50)
        self.rect = self.image.get_rect()
        self.rect.move_ip(window_width * 0.2 + 100, window_height * 0.2 - 100)
        all_sprites.change_layer(self, 10)
        
        self.count = 0
        self.frame = 0
        self.dx = target.rect.left - self.rect.right
        self.dy = target.rect.centery - self.rect.bottom
        self.target = target
    
    
    
    def on_hit(self, dmg):
        battle_log.append("Flare hits for {0} damage!".format(dmg))
        battle_update(self.target, dmg)
        
        
        
        
    def update(self):
        if self.count > 0:
            self.count = (self.count + 1) % 81
            
            if self.count % 10 == 0:
                self.frame += 1
                if self.count == 80:    
                    self.frame = 0
                    self.kill()
                    self.target.shake_count = 5
            
                self.image = self.sheet.subsurface(50* (self.frame % 4), 0, 50, 50)
                self.rect = self.image.get_rect()
                self.image = pygame.transform.scale(self.image, (self.rect.width * 3, self.rect.height * 3))
                self.rect = self.image.get_rect()
                self.rect.move_ip(100 + ((self.dx * self.frame)/8) + window_width * 0.2, window_height * 0.2 - 100 + ((self.frame * self.dy)/8))





class Surface(pygame.sprite.Sprite):
    """this class should be replaced by actual pygame surfaces"""
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
    
    
    
class Stairs(pygame.sprite.Sprite):
    def __init__(self, col, row):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.image = pygame.image.load("stairs.gif")
        self.rect = self.image.get_rect()
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
            if i.target == self.target:
                self.status_num += 1
            
        

        all_sprites.change_layer(self, all_sprites.get_layer_of_sprite(current_background_layer) + 3)
        
        if status == "fear":
            target.isafraid = True
        elif status == "bendy":
            target.evasion *= 1.5

    def update(self):
        self.rect.move_ip(-self.rect.left, -self.rect.top)
        self.rect.move_ip(self.target.rect.left + self.status_num * 50, self.target.rect.top - 20)



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








#def draw_grid(column_num,row_num,surface):
#    
#    for i in range(column_num):
#        pygame.draw.lines(surface,(0,0,0),False,((50 + i*100,50),(50 + i*100,row_num*100 - 50)),3)
#    for i in range(row_num):
#        pygame.draw.lines(surface,(0,0,0),False,((50,i*100 + 50),(column_num*100 - 50, i*100 + 50)),3)

##########################################################################
##########################################################################
############GENERAL GAME FUNCTIONS########################################
##########################################################################
##########################################################################




def battle_init(species):
    global current_background_layer,current_turn, naruto, battle_log, menu_cursor, current_commands, use_button

    Enemy(species)
    Enemy(species)
    
    all_sprites.change_layer(battle_arena, 10)
    current_background_layer = battle_arena
    all_sprites.change_layer(battle_menu_bg, 11)
    all_sprites.change_layer(menu_cursor, 12)
    
    for i in enemies:
        battle_log = ["","","","","You encounter a(n) %s!"%((i.name.replace("_", " ")))]
    
        if "skele" in i.name:
            for j in allies:
                if random.random() > 0.5:
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


        


def battle_end(condition):
    global background, current_background_layer, all_sprites, battle_arena, battle_menu_bg, menu_cursor, enemy_list, post_battle
    
    for i in allies:
        all_sprites.change_layer(i, -2)
        i.rect.move_ip(-i.rect.left, -i.rect.top)
        i.rect.move_ip(i.default_pos)
    
    if condition == "flee":
        current_background_layer = background
        all_sprites.change_layer(battle_arena, -2)
        all_sprites.change_layer(battle_menu_bg, -2)
        all_sprites.change_layer(menu_cursor, -2)
        for i in npcs:
            if i.fighting:
                i.fighting = False
                break
        
        
        
    elif condition == "win":
        current_background_layer = background
        all_sprites.change_layer(battle_arena, -2)
        all_sprites.change_layer(battle_menu_bg, -2)
        all_sprites.change_layer(menu_cursor, -2)
        post_battle = 1
        for i in npcs:
            if i.fighting:
                i.kill()
                break
                
    for i in status_icons:
        i.kill()
    for i in enemies:
        i.kill()
    
    
    enemy_list = []
    
    


def battle_update(target = False, dmg = 0, poison_chance = 0, action = None):
    global to_dissolve, battle_log, current_turn, current_action
    
    current_action = action
    if target:
        target.hp -= dmg
        if poison_chance >= random.random() and target.poisoned == False:
                target.poisoned = True
                Status_icon("poison", target)
                battle_log.append(target.name + " becomes poisoned")
        if target.hp <= 0:
            target.turn_state = 2
            if type(target) == Enemy:
                to_dissolve.append(target)
                target.animating = True
            elif type(target) == Ally:
                target.downed = True
            
                    
    
    for i in combatants:
        if i.turn_state == 1:
            i.turn_state = 2
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
            break
        
    for i in combatants:
        if i.turn_state == 0:
            current_turn = i
            i.turn_state = 1
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
                battle_update()
            break
            
    else:
            
        for i in combatants:
            if i.turn_state != 2:
                break
        else:
            for i in combatants:
                i.turn_state = 0
            battle_update()
    

            
        

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
    



def death(cause):
    global all_sprites, current_background_layer, death_screen, death_text
    current_background_layer = death_screen
    all_sprites.change_layer(death_screen, 20)
    death_text = ["YOU LOSE","You died to " + cause.replace("_", " "), "TIP: " + str(random.choice(tips))]
    
    

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
        target.kill()
        if len(enemies) == 0:
            battle_end("win")






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
            
            

            
            

def stage_clear():
    global stage_num
    for i in tangible:
        i.kill()
    stage_num += 1
    return stage_num
        


def stage_setup(stage_num = 1):
    global character, catboy, kwiz
    
    if stage_num == 2:
        catboy = Ally("catboy")
    elif stage_num == 3:
        kwiz = Ally("kwiz")
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
    for i in range(8):
        new_enemy = NPC("random", column_num, row_num)

    
    for i in range(row_num):
        for j in range(column_num):
            new_tile = Tile()
            new_tile.rect.move_ip(50 + 100*i,50+ 100*j)



def to_inventory(item):
    global items_in_inventory, inv_surface
    
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
                item.rect.move_ip(inv_surface.rect.left + 25 + 100*(items_in_inventory.index(i) % 5), inv_surface.rect.top + 25 + 100*(items_in_inventory.index(i)//5))
                items_in_inventory[items_in_inventory.index(i)] = item
                break


def toggle_inventory():
    global inv_surface, highlight_target
    if all_sprites.get_layer_of_sprite(inv_surface) < 0:
        all_sprites.change_layer(inv_surface, all_sprites.get_layer_of_sprite(current_background_layer) + 2)
        all_sprites.change_layer(use_button, all_sprites.get_layer_of_sprite(current_background_layer) + 3)
        for j in items:
            if j in items_in_inventory:
                all_sprites.change_layer(j, all_sprites.get_layer_of_sprite(current_background_layer) + 4)
    else:
        all_sprites.change_layer(inv_surface, -2)
        all_sprites.change_layer(use_button, -22)
        highlight_target = False

        for j in items:
            if j in items_in_inventory:
                if j.highlighted:
                    j.highlighted = False
                                                
                all_sprites.change_layer(j, -2)
                

            
            
def toggle_equipment():
    global naruto
    if all_sprites.get_layer_of_sprite(equip_surface) < 0:
        all_sprites.change_layer(equip_surface, all_sprites.get_layer_of_sprite(current_background_layer) + 2)
        for i in equipment_slots:
            if i.owner == naruto:
                all_sprites.change_layer(i,all_sprites.get_layer_of_sprite(current_background_layer) + 3)
        for i in items:
            if i.equipped == naruto:
                all_sprites.change_layer(i,all_sprites.get_layer_of_sprite(current_background_layer) + 4)
        for i in allies:
            Equipment_tab(i.name)

            
    else:
        for j in items:
            if j.equipped:
                all_sprites.change_layer(j, -2)
                if j.highlighted:
                    j.highlighted = False
                    highlight_target = False
        all_sprites.change_layer(equip_surface, -2)
        for i in tabs:
            i.kill()
        for i in equipment_slots:
            all_sprites.change_layer(i, -2)
            
    

##########################################################################
######################Spells and Techniques##############################################
##########################################################################
def bum_rush(caster,target):
    global battle_log
    damage = int(caster.power * random.uniform(1.8, 2.8))
    self_damage = damage // 3
    caster.hp -= self_damage
    battle_log.append(caster.name + "hurt themselves for {0} damage".format(self_damage))
    battle_update(target, damage, action = bum_rush.__name__)
    
def flare(caster, target):
    global flare_particle
    caster.cast_count = 5
    caster.animating = True
    flare_particle = Particle("flare", target)

def malevolent_milking():
    battle_log.append("Beelzeboob is doing something horrific!")
    Enemy("mayonnaise_elemental")
    
    
    
    
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
    
def sneeze(caster, target):
    damage = int(caster.magic * random.uniform(0.8,1.2))
    battle_update(target, damage, 0.33, action = sneeze.__name__)

def squish(target):
    global battle_log
    attack_damage = 50 + random.randint(-5,10)
    if attack_damage < 0:
        attack_damage = 0
    battle_log.append("Squish deals {0} damage!".format(attack_damage))
    battle_update(target, attack_damage, action = squish.__name__)

    


pygame.init()
pygame.display.set_icon(pygame.image.load("icon.gif"))
main_surface = pygame.display.set_mode((window_width,window_height))
#    column_num = int((window_width/100 -((window_width%100)/100)))
#    row_num = int((window_height/100 - ((window_height%100)/100)))
column_num = 20
row_num = 20
test_font = pygame.font.SysFont("Courier",15)
menu_font = pygame.font.SysFont("Courier",45)
    


    
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


    #assign groups to each sprite class
Character.containers = all_sprites, tangible
Chest.containers = chests, all_sprites, tangible
Enemy.containers = enemies, all_sprites, combatants
NPC.containers = all_sprites, tangible, npcs
Item.containers = items, all_sprites
Menu_button.containers = menu_buttons, all_sprites
Surface.containers = all_sprites
Wall.containers = all_sprites, tangible, walls
Cursor.containers = all_sprites
Equipment_slot.containers = all_sprites, equipment, equipment_slots
Stairs.containers = all_sprites, tangible
Status_icon.containers = all_sprites, status_icons
Tile.containers = all_sprites
Particle.containers = all_sprites
Ally.containers = all_sprites, allies, combatants
Equipment_tab.containers = all_sprites, tabs





def main():
    
    #initialize surfaces and window, global variables
    global character,player_turn, post_battle, current_action, target_cursor,targeting, use_button, naruto, background, current_turn, to_dissolve, current_commands, highlight_target, equip_surface, death_text, death_screen, hp_display, all_sprites,menu_cursor, battle_arena, battle_menu_bg, battle_log, tangible, current_background_layer, cursor, items_in_inventory, walls, inv_surface, chests
  
    frame_count = 0
    player_turn = True
    targeting = False
    
    #create objects - always spawn walls, then chests, then enemies
    inv_surface = Surface("inventory")
    equip_surface = Surface("equipment_bg")
    background = Surface("background")
    battle_arena = Surface("battle_arena")
    battle_menu_bg = Surface("battle_menu_bg")
    death_screen = Surface("death_screen")

    
    stage_setup()
    backpack = Menu_button("backpack")
    equipment = Menu_button("equipment")
    use_button = Menu_button("use_button")
    
   

    naruto = Ally("naruto")
    menu_cursor = Cursor("menu")
    
    #assign layers to sprites
    current_background_layer = background
    all_sprites.change_layer(menu_cursor, -2)
    for i in items:
        all_sprites.change_layer(i, -2)


    


    #events make stuff happen
    while True:
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or ev.type == KEYDOWN and ev.key == K_ESCAPE:
                pygame.quit()
                
            if ev.type == USEREVENT:
                if type(current_turn) == Enemy:
                    current_turn.turn()
                    pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                elif current_turn.animating:
                    pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                else:
                    player_turn = True
           

                            
                            
            elif ev.type == KEYDOWN:
                #move character after checking for collision
                if all_sprites.get_layer_of_sprite(inv_surface) < 0 and all_sprites.get_layer_of_sprite(battle_arena) < 0 and all_sprites.get_layer_of_sprite(equip_surface) < 0 and post_battle == 0:
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
                            
                            
                elif all_sprites.get_layer_of_sprite(equip_surface) > 0:
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
                                            
                            
                            #move menu cursor in battle screen
                elif current_background_layer == battle_arena and player_turn == True:
                    if ev.key == K_s:
                        if targeting:
                            target_cursor.cycle(1)
                        elif menu_cursor.pos < len(current_commands) -1:
                            menu_cursor.rect.move_ip(0,40)
                            menu_cursor.pos += 1
                    if ev.key == K_w:
                        if targeting:
                            target_cursor.cycle(0)
                        elif menu_cursor.pos > 0:
                            menu_cursor.rect.move_ip(0,-40)
                            menu_cursor.pos -= 1
                
                            
                    if ev.key == K_BACKSPACE:
                        if targeting:
                            targeting = False
                            target_cursor.kill()
                        
                        #trigger actions during battle depending on selected command
                    if ev.key == K_SPACE:
                        
                            
                        if current_commands[menu_cursor.pos] == "Attack":
                            if targeting:
                                current_turn.attack(target_cursor.target)
                                pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                                player_turn = False
                                target_cursor.kill()
                                targeting = False
                                print(pygame.event.get())
                                    
                            else:
                                target_cursor = Cursor("target")
                                targeting = True
                            
                            
                        elif current_commands[menu_cursor.pos] == "Flee":
                            battle_end("flee")
                            
                        elif current_commands[menu_cursor.pos] == "Defend":
                            current_turn.defending = True
                            battle_update()
                            pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                            player_turn = False
                        
                        elif current_commands[menu_cursor.pos] == "Magic":
                            current_commands = magic_commands
                            menu_cursor.reset()
                        elif current_commands[menu_cursor.pos] == "Item":
                            if targeting:
                                targeting = False
                                target_cursor.what.consume(target_cursor.target)
                                pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                                player_turn = False
                                target_cursor.kill()
                            else:
                                toggle_inventory()                         
                        elif current_commands[menu_cursor.pos] == "Back":
                            current_commands = basic_commands
                            menu_cursor.reset()
                        elif current_commands[menu_cursor.pos] == "Squish":
                            if targeting:
                                squish(target_cursor.target)
                                pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                                player_turn = False
                                target_cursor.kill()
                                targeting = False
                                    
                            else:
                                target_cursor = Cursor("target")
                                targeting = True
                        elif current_commands[menu_cursor.pos] == "Mindblow":
                            if targeting:
                                mindblow(target_cursor.target)
                                pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                                player_turn = False
                                target_cursor.kill()
                                targeting = False
                                    
                            else:
                                target_cursor = Cursor("target")
                                targeting = True
                        elif current_commands[menu_cursor.pos] == "Flare":
                            if targeting:
                                flare(current_turn, target_cursor.target)
                                pygame.time.set_timer(pygame.USEREVENT, 1000, True)
                                player_turn = False
                                target_cursor.kill()
                                targeting = False
                                    
                            else:
                                target_cursor = Cursor("target")
                                targeting = True
                
                elif post_battle == 1:
                    post_battle = 2
                elif post_battle > 1 and naruto.loot_xp == 0:
                    post_battle = 0
                                
                            
                            
            elif ev.type == MOUSEBUTTONDOWN:
                for i in all_sprites:
                    if all_sprites.get_layer_of_sprite(i) >= 0 and i.rect.collidepoint(pygame.mouse.get_pos()):

                        if type(i) is Menu_button:   #open/close inventory/equipment menu and populate each with correct items
                            if i == backpack:
                                toggle_inventory()
                            elif i == equipment:
                                toggle_equipment()
                                    
                            elif i == use_button:
                                for j in items:
                                    if j.highlighted == True:
                                        targeting = True
                                        target_cursor = Cursor("target", j)
                                        all_sprites.change_layer(inv_surface, -2)
                                        all_sprites.change_layer(use_button, -22)
                                        highlight_target = False
                                        for j in items:
                                            if j in items_in_inventory:
                                                if j.highlighted:
                                                    j.highlighted = False
                                                all_sprites.change_layer(j, -2)
                            
                            
                        if i is inv_surface:

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
                        




                            
            else:    #display tooltip/hovertext
                for i in all_sprites:
                    if i.rect.collidepoint(pygame.mouse.get_pos()):
                        if type(i) is Item:
                            current_hover_text = i.hover_text
                            break
                    else:
                        current_hover_text = []

                        
          
        



        #draw what needs to be drawn
        main_surface.fill((20,163,199))
        
#        draw_grid(column_num,row_num,main_surface)

        
        all_sprites.update()
        all_sprites.draw(main_surface)
        highlight(highlight_target)
        if current_background_layer == battle_arena:
            for i in range(5):
                main_surface.blit(test_font.render(battle_log[-5 + i], True, (255,255,255)), (round(window_width*0.6666,0), 20*i + round(window_height*0.666,0)))
            for i in range(len(current_commands)):
                main_surface.blit(menu_font.render(current_commands[i], True, (255,255,255)), (60, 40*i + round(window_height*0.666,0)))
            main_surface.blit(test_font.render(hp_display, True, (255,255,255)), (round(window_width * 0.1), round(window_height * 0.1)))
            pygame.draw.rect(main_surface, (153,255,51), hp_bar_full)
            pygame.draw.rect(main_surface, (0,43,0), hp_bar_empty)
            if current_action:
                current_action_box.fill((127,127,127,150))
                print(current_action)
                render = test_font.render(current_action, True, (255,255,255))
                current_action_rect = current_action_box.get_rect()
                current_action_box.blit(render, (current_action_rect.centerx - render.get_size()[0] / 2, current_action_rect.centery - render.get_size()[1] / 2 ))
                main_surface.blit(current_action_box,(round(window_width*0.5) - 150, 0))
                
        elif current_background_layer == death_screen:

            main_surface.blit(menu_font.render(death_text[0], True, (255,255,255)), (round(window_width*0.45, 0), round(window_height*0.25, 0)))
            main_surface.blit(menu_font.render(death_text[1], True, (255,255,255)), (round(window_width*0.33, 0), round(window_height*0.45,0)))
            main_surface.blit(menu_font.render(death_text[2], True, (255,255,255)), (round(window_width*0.25, 0), round(window_height*0.666,0)))
            
            
        elif current_background_layer == background:
            main_surface.blit(general_log_box,(round(window_width*0.666), round(window_height * 0.8)))
            general_log_box.fill((0,0,0,150))

            for i in range(5):
                main_surface.blit(test_font.render(general_log[-5 + i], True, (255,255,255)), (round(window_width*0.6666,0), 20*i + round(window_height*0.8,0)))
            
            
        if post_battle > 0:
            main_surface.blit(post_battle_screen, (0,0))
            post_battle_screen.fill((10,30,200))
            post_battle_screen.blit(menu_font.render("Reward:  " + str(naruto.loot_xp), True, (255,255,255)), (round(window_width*0.1 + 200, 0), round(window_height * 0.1 - 50, 0)))
            for i in allies:
                post_battle_screen.blit(menu_font.render((i.name), True, (255,255,255)), (round(window_width*0.1, 0), round(window_height * 0.1 + 200*party_list.index(i), 0)))
                post_battle_screen.blit(menu_font.render(("    Level: " + str(i.lvl)), True, (255,255,255)), (round(window_width*0.1, 0), round(window_height * 0.1 + 200*party_list.index(i) + 50, 0)))
                post_battle_screen.blit(menu_font.render(("EXP: " + str(i.xp)), True, (255,255,255)), (round(window_width*0.5, 0), round(window_height * 0.1 + 200*party_list.index(i), 0)))
                post_battle_screen.blit(menu_font.render((("EXP to level: " + str(i.xp_to_lvl))), True, (255,255,255)), (round(window_width*0.5, 0), round(window_height * 0.1 + 200*party_list.index(i) + 50, 0)))
            if post_battle == 2:
                for i in allies:
                    if i.loot_xp > 0 and frame_count % 3 == 0:
                        i.loot_xp -= 1
                        i.xp += 1
                        i.xp_to_lvl = int((i.lvl ** 1.1 + i.lvl * 50) - i.xp)
                    if i.xp_to_lvl == 0:
                        i.stats("lvl_up")
            
        dev_display(main_surface,test_font,pygame.mouse.get_pos())
        for i in current_hover_text:
            main_surface.blit(test_font.render(i, True, (255,255,255)), (pygame.mouse.get_pos()[0] - 100, pygame.mouse.get_pos()[1] + (30 * current_hover_text.index(i))))
        
        if len(to_dissolve) != 0:
            for i in to_dissolve:
                dissolve(i)
        

        pygame.display.flip()
        
        frame_count += 1
        
        """limit to 60 fps"""
        clock.tick(60)
    
    
    pygame.quit()
    
main()

"""TO DO"""
""" splash screen my face on naruto"""
"""taking stairs actually changes stage_num, changes which enemies will spawn etc"""
"""more spells"""
"""currency nuggies, shop/poopsmith"""
"""stats/attributes? different potions increase different stats"""
""" properly scale everything on different resolutions -consider setting main_surface.display.set_mode to 0,0 instead of resoultion"""
"""djinn/class system - change job via loader (neuromancer style microsoft)"""
"""instead of elemental types/weaknesses use pierce/bludgeon/slash"""
"""entomb spell, encases in rock, stuns for a while"""
"""do something on overworld instead of just move?"""
"""retry button on game over screen"""
"""have several battle_arena background images"""
"""Boss before stairs? or every X levels"""
"""improve look of item hover text"""
"""item drops aren't 100% random"""
"""loot from enemies"""
"""sometimes an invisible wall blocks movement on overworld"""
"""different attacks/moves from different enemies, chance to cause statuses"""
"""consume items out of combat"""
"""update sprites to color palette"""
"""blit transparent surface on battle_arena for animations"""



"""ENEMY IDEAS"""
"""lobster linguini - plate of noods with pinchy claws"""
"""dogboy"""
"""mayonnaise elemental"""
"""leech seed like spell, maybe toss soul leeches"""
"""protect spell"""
"""stall tactics"""
"""damage based on % of player hp"""


"""party member ideas - dwarf, karate wizard, hobo, catboy"""


"""OTHER THINGS TO KEEP IN MIND"""
"""max of 4 allies at a time, chance to swap them if you find another?"""