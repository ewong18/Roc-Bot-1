#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from res.common import customemoji, ship_search, sanitise_input, argument_parser, get_em_colour, embed_pagination
import sqlite3 
import discord.ext.commands
from discord.ext.commands import Bot
import urllib.parse
import random


# This class connects to rocbot.sqlite and uses a view to query. The returned 
# data is put into an object where methods run uses this info to generate a
# title, image url, and description which contains emojis. The emoji function 
# uses the Bot instance to perform a lookup which is why it's passed through.
# Because Discord doesn't allow non alpha characters in emojis there's a 
# santise function that strips unwanted characters which is also used on the 
# url formatting function. That's technical debt from when this was orignally
# using json files instead of sqlite and the sub context of the query and name 
# was used as the name to find image files so they had to match. This isn't the 
# case anymore and might be better to edit the image names now. 
class ShipData():
    def __init__(self, bot_self, find_this):
        self.bot_self = bot_self
        self.ship_name = ship_search(find_this)
        self.s_obj = self.sql_ship_obj()
        self.img_url = self.get_ship_image()
        self.embed_info = self.info_embed(find_this)
        self.embed_detail = self.detail_embed(find_this)
        
    def sql_ship_obj(self):
        # connect to the sqlite database
        conn = sqlite3.connect('rocbot.sqlite')
        # return a class sqlite3.row object which requires a tuple input query
        conn.row_factory = sqlite3.Row
        # make an sqlite connection object
        c = conn.cursor()
        # using a defined view s_info find the ship 
        c.execute('select * from s_info where name = ?', (self.ship_name,))
        # return the ship object including the required elemnts
        s_obj = c.fetchone()
        # close the databse connection
        conn.close()
        # return the sqlite3.cursor object
        return s_obj

    # Creates the title of the discord emebed consisting of the rarity emoji 
    # the ship name.
    def get_ship_title(self):
        embed_title = (
            f"{customemoji(self.bot_self, self.s_obj['rarity'])} {self.s_obj['name']}")
        return embed_title
    
    # The embed is made up of two sections of content the title and this section
    # the descriotion. The description contains weapon, aura and zen info using 
    # an emoji followed by the relevant name of the section. 
    #
    # The description previously used format() instead f strings bceause at the 
    # time I didn't see how f strings were suited to json and dicts however 
    # since using a class that's changed and f strings seemed clearer to read. 
    def get_ship_description_info(self):
        embed_description = (
            f"{customemoji(self.bot_self, 'dps')} {self.s_obj['dmg']}\n"
            f"{customemoji(self.bot_self, self.s_obj['affinity'])} {self.s_obj['weapon_name']}\n" 
            f"{customemoji(self.bot_self, self.s_obj['aura'])} {self.s_obj['aura']}\n"
            f"{customemoji(self.bot_self, self.s_obj['zen'])} {self.s_obj['zen']}")
        return embed_description
            
    def get_ship_description_detail(self):
        embed_description = (
            f"{customemoji(self.bot_self, 'dps')} {self.s_obj['dmg']}\n"
            f"{customemoji(self.bot_self, self.s_obj['affinity'])} {self.s_obj['weapon_name']}")
        return embed_description
    
    def get_ship_image(self):
        urlgit = "https://raw.githubusercontent.com/ewong18/Roc-Bot/master/ships/"
        img_url = ("{giturl}ship_{shipnumber}.png").format(giturl=urlgit, shipnumber=self.s_obj['number'])
        return img_url
        
    # create a discod embed object. Using the Ship class to collect the required 
    # data. The embed includes a title as a ship emoji and the ship name queried
    # The description is a combination of weapon, aura and zen names with emojis
    # to suit. weapon zen gets a generic dps emoji and zen|aura get the specific 
    # emoji 
    def info_embed(self, find_this):
        title = self.get_ship_title()
        desc = self.get_ship_description_info()
        col = int(self.s_obj['colour'], 16)
        return discord.Embed(title=title, 
        description=desc, colour=col).set_thumbnail(url=self.img_url)
        
    def detail_embed(self, ship_name):
        title = self.get_ship_title()
        desc = self.get_ship_description_detail()
        col = int(self.s_obj['colour'], 16)
        embed = discord.Embed(title=title, description=desc, colour=col)
        embed.add_field(
            name=f"{customemoji(self.bot_self, self.s_obj['aura'])} {self.s_obj['aura']}",
            value=f"{self.s_obj['aura_desc']}", 
            inline=False)
        embed.add_field(
            name=f"{customemoji(self.bot_self, self.s_obj['zen'])} {self.s_obj['zen']}",
            value=f"{self.s_obj['zen_desc']}", 
            inline=False)
        embed.set_thumbnail(url=self.img_url)
        return embed

class ShipLister():
    def __init__(self, bot_self, ctx, arg1, sc):
        self.bot_self = bot_self
        self.ctx = ctx
        self.arg1 = argument_parser(sc, arg1)
        self.sub_command = sc
        self.embed_title = self.title()
        self.s_obj = self.sql_ship_obj()

    def sql_ship_obj(self):
        conn = sqlite3.connect('rocbot.sqlite')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if self.sub_command in ('all', 'rand'):
            c.execute("select * from s_info")
        else:
            c.execute(f"select * from s_info where {self.sub_command} = ?", (self.arg1,))
        s_obj = c.fetchall()
        conn.close()
        print(self.arg1)
        return s_obj

    def create_description(self):
        description = []
        if self.sub_command == 'dmg':
            for i in self.s_obj:
                description.append(
                    f"{customemoji(self.bot_self, i['affinity'])} "
                    f"{customemoji(self.bot_self, i['name'])} "
                    f"{i['name']}")
            return embed_pagination(description)
        elif self.sub_command == 'affinity':
            for i in self.s_obj:
                description.append(
                    f"{customemoji(self.bot_self, i['name'])} "
                    f"{i['name']}")
            return embed_pagination(description)
        elif self.sub_command == 'rand':
            for i in self.s_obj:
                description.append(
                    f"{customemoji(self.bot_self, i['affinity'])} "
                    f"{customemoji(self.bot_self, i['name'])} "
                    f"{i['name']}")
            return embed_pagination(random.sample(description, int(self.arg1)))
        # having an else without knowing what uses it sucks
        else:
            for i in self.s_obj:
                description.append(
                    f"{customemoji(self.bot_self, i['affinity'])} "
                    f"{customemoji(self.bot_self, i['name'])} "
                    f"{i['name']}")
            return embed_pagination(description)

    async def create_embed(self):
        ctx = self.ctx
        if self.sub_command == 'affinity':
            colour = get_em_colour(self.arg1)
            for page in self.create_description():
                await ctx.send(embed=discord.Embed(
                    title=self.embed_title, 
                    description=page, 
                    color=colour))
        else:
            for page in self.create_description():
                await ctx.send(embed=discord.Embed(
                    title=self.embed_title, 
                    description=page))

    def title(self):
        if self.sub_command == "dmg":
            return f"{customemoji(self.bot_self, 'dps')} {self.arg1} DPS Ships"
        if self.sub_command == "all":
            return "All Ship Listing"
        if self.sub_command == "rand":
            return f"Random list of {self.arg1} ships"
        else:
            return f"{customemoji(self.bot_self, self.arg1)} {self.arg1} Ships"

class CategoryLister():
    def __init__(self, bot_self, sub_command):
        self.bot_self = bot_self
        self.sub_command = sub_command
        self.s_obj = self.sql_ship_obj()
        self.embed_list = self.create_list()

    def sql_ship_obj(self):
        # connect to the sqlite database
        conn = sqlite3.connect('rocbot.sqlite')
        # return a class sqlite3.row object which requires a tuple input query
        conn.row_factory = sqlite3.Row
        # make an sqlite connection object
        c = conn.cursor()
        # using a defined view s_info collect all table info 
        c.execute('select * from s_info')
        # return the ship object including the required elemnts
        s_obj = c.fetchall()
        # close the databse connection
        conn.close()
        # return the sqlite3.cursor object
        return s_obj

    def create_list(self):
        new_set = set({})
        list1 = []
        for i in self.s_obj:
            new_set.add(i[self.sub_command])
        if self.sub_command == 'dmg':
            for i in sorted(new_set):
                list1.append(f"{i}")
            description = '\n'.join(list1)
        else:
            for i in sorted(new_set):
                list1.append(f"{customemoji(self.bot_self, i)} {i}")
            description = '\n'.join(list1)
        return discord.Embed(title=self.title(), description=description)

    def title(self):
        if self.sub_command == "affinity":
            return f"{customemoji(self.bot_self, 'damage')} Main Weapon Affinities"
        elif self.sub_command == "dmg":
            return f"{customemoji(self.bot_self, 'dps')} Damage Brackets"
        elif self.sub_command == "aura":
            return f"{customemoji(self.bot_self, 'aura')} Auras"
        elif self.sub_command == "zen":
            return f"{customemoji(self.bot_self, 'zen')} Zens"
        elif self.sub_command == "rarity":
            return f"{customemoji(self.bot_self, 'pinchallenge')} Rarities"
        else:
            pass

class ApexLister():
    def __init__(self, bot_self, find_this):
        self.bot_self = bot_self
        self.ship_name = ship_search(find_this)
        self.s_apex_obj = self.sql_apex_obj()
        self.embed_list = self.create_list()

    def sql_apex_obj(self):
        # connect to the sqlite database
        conn = sqlite3.connect('rocbot.sqlite')
        # return a class sqlite3.row object which requires a tuple input query
        conn.row_factory = sqlite3.Row
        # make an sqlite connection object
        c = conn.cursor()
        # using a defined view s_info collect all table info
        c.execute('select * from s_apex where name = ?', (self.ship_name,))
        # return the ship object including the required elemnts
        s_apex_obj = c.fetchall()
        # close the databse connection
        conn.close()
        # return the sqlite3.cursor object
        return s_apex_obj

    def create_list(self):
        description = ''
        for i in self.s_apex_obj:
            apex_type = ''
            ship_apex = sanitise_input(i['name'].lower() + i['rank'].upper())
            find_emoji = discord.utils.get(self.bot_self.bot.emojis, name = ship_apex)
            if i['type'] == 'aura':
                apex_type = i['aura']
            if i['type'] == 'zen':
                apex_type = i['zen']
            if i['type'] == 'weapon':
                apex_type = 'Main Weapon'
            description = f"{description} {find_emoji} {i['rank']}: {i['apex']} - {apex_type} (cost: {i['cost']:,}\xa2) \n"
        return description
        
class ApexData():
    def __init__(self, bot_self, find_this, res):
        self.bot_self = bot_self
        self.ship_name = find_this
        self.apex_tier = res
        self.apex_obj = self.sql_apex_obj()
        self.embed_title = self.get_title()
        self.embed_desc = self.get_description()
        
    def sql_apex_obj(self):
        # connect to the sqlite database
        conn = sqlite3.connect('rocbot.sqlite')
        # return a class sqlite3.row object which requires a tuple input query
        conn.row_factory = sqlite3.Row
        # make an sqlite connection object
        c = conn.cursor()
        # using a defined view s_info find the ship
        c.execute('select * from s_apex where name = ? and rank = ?', (self.ship_name,self.apex_tier))
        # return the ship object including the required elemnts
        s_apex_obj = c.fetchone()
        # close the databse connection
        conn.close()
        # return the sqlite3.cursor object
        return s_apex_obj

    # Creates the title of the discord emebed consisting of the rarity emoji
    # the ship name.
    def get_title(self):
        embed_title = (
            f"{self.apex_obj['name']} {self.apex_obj['rank']}")
        return embed_title
    
    # The embed is made up of two sections of content the title and this section
    # the descriotion. The description contains weapon, aura and zen info using
    # an emoji followed by the relevant name of the section.
    #
    # The description previously used format() instead f strings bceause at the
    # time I didn't see how f strings were suited to json and dicts however
    # since using a class that's changed and f strings seemed clearer to read.
    def get_description(self):
        row = self.apex_obj
        apex_type = ''
        if row['type'] == 'aura':
            apex_type = row['aura']
        if row['type'] == 'zen':
            apex_type = row['zen']
        if row['type'] == 'weapon':
            apex_type = 'Main Weapon'
        embed_description = (
            f"Cost: {row['cost']:,}\xa2\n"
            f"Apex: {row['apex']}\n"
            f"Type: {apex_type}\n"
            f"Description: {row['a_desc']}")
        return embed_description
    
