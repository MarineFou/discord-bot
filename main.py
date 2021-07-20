import discord
import os
import requests

from discord import ChannelType, Member
from discord.ext.commands import Bot
from dotenv import load_dotenv
from emoji import emoji_lis

load_dotenv()

print_information = False


def get_nickname(member: Member):
    return member.nick if member.nick else member.name


class MyBot(Bot):
    async def on_ready(self):
        print('------')
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

        if print_information:
            # Display categories and channels of the target Discord server
            target_guild_id = int(os.getenv('TARGET_GUILD_ID'))
            for guild in bot.guilds:
                if int(guild.id) == target_guild_id:
                    categories = [c for c in guild.channels if c.type == ChannelType.category]
                    text_channels = [c for c in guild.channels if c.type == ChannelType.text]
                    category_to_channel = {}
                    for category in categories:
                        print(f'{category.name} :')
                        category_to_channel[category.name] = []
                        for c in text_channels:
                            if c.category_id == category.id:
                                print(' -', c, repr(c))
                                category_to_channel[category.name].append(c)


if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.members = True
    bot = MyBot(command_prefix='!', intents=intents)

    @bot.command()
    async def ping(ctx):
        await ctx.channel.send("pong")\


    @bot.command(name='alerte-la-planete', aliases=['alerte-la-planète'])
    async def mention_planet_members(ctx, *args):
        print(ctx.message.content)

        # Create a list with all emojis to search in usernames
        emojis = []
        # Add emoji from mentioned channels in the args list
        for channel in ctx.message.channel_mentions:
            args = (channel.name,)
        # Foreach args, check that is starts with an emoji and add it to the emoji list
        for arg in args:
            emoji_list = emoji_lis(arg)
            if emoji_list and emoji_list[0]['location'] == 0:
                emojis.append(emoji_list[0]['emoji'])

        print('emojis : ', str(emojis))

        # Search the emoji in the nickname of all guild members
        members_to_ping = []
        for member in ctx.guild.members:
            # Use nickname to search the emoji inside (fallback to the name if nickname hasn't been set)
            for emoji in emojis:
                if emoji in get_nickname(member):
                    members_to_ping.append(member)
                    break

        # Ping all targeted members if at least one has been found
        if members_to_ping:
            print('Nombre de personnes à pinguer : ', len(members_to_ping))
            offset = 80
            for start in range(1 + (len(members_to_ping) - 1) // offset):
                start = start * offset
                await ctx.message.reply(
                    ' '.join(user.mention for user in members_to_ping[start:start + offset]),
                    mention_author=True
                )
        else:
            await ctx.message.reply(
                'Aucun utilisateur à mentionner...',
                mention_author=True
            )

    @bot.command(name='search-links')
    async def search_links(ctx, *args):
        found_links = []
        if args:
            url = 'https://api.short.io/api/links'
            querystring = {'domain_id': os.getenv('SHORT_IO_DOMAIN_ID')}
            headers = {
                'Accept': 'application/json',
                'Authorization': os.getenv('SHORT_IO_SECRET_KEY')
            }
            response = requests.get(url, headers=headers, params=querystring)

            # Loop through each links and add it to found_links if one of the args is matching
            for link in response.json()['links']:
                # Ignore archived links
                if link['archived']:
                    continue

                for arg in args:
                    # Stop searching if link has been added
                    if link in found_links:
                        break

                    # Check if in one of the fields is matching one of the args
                    for field in ('title', 'originalURL'):
                        if arg.lower() in link[field].lower():
                            found_links.append(link)
                            break

                    # Check in the tags if link is still not in found_links
                    if link not in found_links:
                        for tag in link['tags']:
                            if arg.lower() in tag.lower():
                                found_links.append(link)
                                break

        if found_links:
            embed = discord.Embed()
            embed.title = ' '.join(args)
            embed.description = '\n'.join(f'- [{link["title"]}]({link["shortURL"]})' for link in found_links)
            initial_search = ' '.join(args)
            await ctx.message.reply(
                f'Voici les résultats de votre recherche "{initial_search}":',
                mention_author=True
            )
            for link in found_links:
                embed = discord.Embed()
                embed.title = link['title']
                embed.type = 'link'
                embed.url = link['shortURL']
                embed.set_thumbnail(url=link['icon'])
                embed.add_field(name='Lien', value=link["shortURL"], inline=False)
                if link['tags']:
                    embed.add_field(name='Tags', value=' | '.join(tag for tag in link['tags']))
                await ctx.send(embed=embed)
        else:
            await ctx.message.reply(
                'Aucun résultat pour votre recherche...',
                mention_author=True
            )


    @bot.command(name='quarks-a-accueillir', aliases=['quarks-à-accueillir'])
    async def quarks_to_welcome(ctx):
        filename = 'quarks à accueillir.txt'
        written = False
        with open(filename, "w", encoding="utf-8") as file:
            for member in ctx.guild.members:
                if not member.bot and '*' not in get_nickname(member):
                    file.write(f'{member.nick} [@{member}] - {member.joined_at.strftime("%d/%m/%Y %H:%M")}\n')
                    written = True

        if written:
            # Send file to Discord in message
            with open(filename, "rb") as file:
                await ctx.message.reply(
                    "Fichier texte contenant la liste des quarks n'ayant pas d'astérique dans leur nom :",
                    file=discord.File(file, filename)
                )
        else:
            await ctx.message.reply(
                'Aucun quarks à accueillir 😮',
                mention_author=True
            )

    bot.run(os.getenv('TOKEN'))
