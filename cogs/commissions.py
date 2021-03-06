import discord, asyncio
from discord.ext import commands
from main import main_color, ApprovedRoleID, ArtiFeZGuildIconUrl, TwitterEmoji, InstaEmoji
from utils.MainEmbed import qEmbed
import re, datetime, json
from typing import *


def setup(bot):
    bot.add_cog(Commissions(bot))


class Commissions(commands.Cog):
    """
    Commands related to the commission system in ArtiFeZ.
    """
    """
1st Part:
**Registering your portfolio** (Seller Part)
- every approved vfx/gfx will have the access to a `register` command on the server which will add his entry to a 
sellers/artists list.

- it will include questions like:
drop your port
your payment methods
your minimum commission cost
your best areas, maximum of 2, for example - headers and logos

- once registered, there will be a channel named `verified-sellers` where they can use a command `portfolio`
 which will show all their info which we asked in the questions. Then, we move onto our 2nd part.

2nd Part:
**Making a request** (Buyer part)
- there will be a channel named `make-a-request` or something like that where people can use the `buy` or `request`
command once in a day, where the buyer will be asked some questions like:
your budget
your available payment methods
your order
brief of your order (upto 2000 words)

- this will create an open request from the buyer to all the available servers.
This request will have a unique ID (like #0001)

- Once they place their order,it gets sent to a channel named `requests` which only the verified sellers can access.
The verified sellers then can dm the guy with their offers and the guy chooses the best one, when he
finds the perfect guy, he marks his request by using a command `completed (unique id of request)`
    """
    # Commands List: [all commands are guild-only]
    # Seller Part:
    # register : register the user  ✅
    # profile : view the profile of the user  ✅
    # set : set/change a value in the profile
    # Buyer Part:
    # request : make a "request" from the buyers
    # requset edit <id> : edit a request already made
    # request delete <id> : deletes the request made
    # request history : shows the previous requests made

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def profileEmbed(data, user : discord.Member):
        # print(data)
        e = qEmbed(
            title=data["profession"],
            description=data["bio"]
        ).set_author(
            name=str(user),
            icon_url=user.avatar_url
        ).set_image(
            url=data["banner"]
        )
        twitter = json.loads(data["socials"])["twitter"]
        insta = json.loads(data["socials"])["instagram"]
        uh = '\n'
        if twitter or insta or twitter and insta:
            e.add_field(name="Socials",
                        value=f"{f'[Twitter]({twitter})' if twitter else ''}{uh if insta else ''}"
                              f"{f'[Instagram]({insta})' if insta else ''}")
        e.description = data['bio']
        e.add_field(name="Commissions",
                    value="Open" if data['commissions_open'] else "Closed")
        e.add_field(name="Portfolio",
                    value=data['portfolio'],
                    inline=False)
        return e

    @commands.command(name="profile", help="Sends the profile of the user mentioned.")
    @commands.has_role(ApprovedRoleID)
    @commands.guild_only()
    async def profile(self, ctx: commands.Context, seller: discord.Member = None):
        seller = ctx.author if not seller else seller
        if not seller:
            query = "SELECT * FROM profiles WHERE user_id = $1"
            data = await self.bot.pool.fetch(query, str(seller.id))
            # print(data)
            if data:
                e = self.profileEmbed(data[0], seller)
                return await ctx.send(embed=e)
            if not data:
                return await ctx.send(embed=qEmbed(title=f"{seller.display_name} is not a verified seller"))
        if seller:
            query = "SELECT * FROM profiles WHERE user_id = $1"
            data = await self.bot.pool.fetch(query, str(seller.id))
            if data:
                e = self.profileEmbed(data[0], seller)
                return await ctx.send(embed=e)
            if not data:
                return await ctx.send(embed=qEmbed(title=f"{seller.display_name} is not a verified seller"))

    @commands.command(name="set", help="Edits/Sets various values of your profile.")
    @commands.has_role(ApprovedRoleID)
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def _set(self, ctx: commands.Context, thing: str = None, *, value: str = None):
        help_embed = qEmbed(title=f"❎ Incorrect usage")
        help_embed.add_field(
            name="Correct usage:",
            value=f"`.set <thing> <value>`\n"
                  f"`.set portfolio https://behance.net/vxdro`\n"
                  f"`.set commissions closed`\n"
                  f"`.set banner_url https://ibb.co/whatever`",
            inline=False
        ).add_field(
            name="Available Options:",
            value="bio\n"
                  "profession\n"
                  "twitter\n"
                  "instagram\n",
            inline=True
        ).add_field(
            name="⠀",
            value="portfolio\n"
                  "commissions\n"
                  "banner"
        )
        if not thing:
            return await ctx.send(embed=help_embed)
        if not value:
            return await ctx.send(embed=help_embed)
        if thing and value:
            user_id = str(ctx.author.id)
            valid_things = ["bio", "profession", "twitter", "instagram", "portfolio", "commissions", "banner"]
            if thing.lower() not in valid_things:
                ee = help_embed
                ee.title = "❎ Wrong thing entered!"
                return await ctx.send(embed=ee)
            if thing.lower() == "bio":
                query = "UPDATE profiles SET bio = $1 WHERE user_id = $2"
                await self.bot.pool.execute(query, value, user_id)
                return await ctx.message.add_reaction("✅")
            if thing.lower() == "profession":
                query = "UPDATE profiles SET profession = $1 WHERE user_id = $2"
                await self.bot.pool.execute(query, value, user_id)
                return await ctx.message.add_reaction("✅")
            if thing.lower() == "twitter":
                data = await self.bot.pool.fetch("SELECT * from profiles WHERE user_id = $1", user_id)
                socials = json.loads(data[0]["socials"])
                socials["twitter"] = value
                query = "UPDATE profiles SET socials = $1 WHERE user_id = $2"
                await self.bot.pool.execute(query, json.dumps(socials), user_id)
                return await ctx.message.add_reaction("✅")
            if thing.lower() == "instagram":
                data = await self.bot.pool.fetch("SELECT * from profiles WHERE user_id = $1", user_id)
                socials = json.loads(data[0]["socials"])
                socials["instagram"] = value
                query = "UPDATE profiles SET socials = $1 WHERE user_id = $2"
                await self.bot.pool.execute(query, json.dumps(socials), user_id)
                return await ctx.message.add_reaction("✅")
            if thing.lower() == "portfolio":
                query = "UPDATE profiles SET portfolio = $1 WHERE user_id = $2"
                await self.bot.pool.execute(query, value, user_id)
                return await ctx.message.add_reaction("✅")
            if thing.lower() == "commissions":
                if "close" in value.lower():
                    commissions_open = False
                elif "open" in value.lower():
                    commissions_open = True
                else:
                    commissions_open = False
                query = "UPDATE profiles SET commissions_open = $1 WHERE user_id = $2"
                await self.bot.pool.execute(query, commissions_open, user_id)
                return await ctx.message.add_reaction("✅")
            if thing.lower() == "banner":
                query = "UPDATE profiles SET banner = $1 WHERE user_id = $2"
                await self.bot.pool.execute(query, value, user_id)
                return await ctx.message.add_reaction("✅")
            else:
                pass

    @commands.command(name="register", help="Registers you as a seller on the server.")
    @commands.has_role(ApprovedRoleID)
    @commands.guild_only()
    async def register(self, ctx: commands.Context):
        """Registers a member as a verified seller on the server."""
        """
        Table "profiles"
        user_id : bigint
        bio : str
        profession : str
        socials : jsonb => {str(social_name) : str(social_url)}
        portfolio : str
        commissions_open : bool
        banner : str
        registered_at : datetime
        """
        check = await self.bot.pool.fetch("SELECT * FROM profiles WHERE user_id = $1", str(ctx.author.id))
        if check:
            return await ctx.send(embed=qEmbed(
                title="Already Registered!",
                description="You are already registered. You can type `.profile` to view your profile."
            ))
        try:
            await ctx.message.add_reaction("✉")
            initial_msg = await ctx.author.send(embed=qEmbed(title="Starting the registering process",
                                                             description="Please answer all the questions correctly"
                                                                         "and honestly.").set_author(
                name=str(ctx.author),
                icon_url=ctx.author.avatar_url
            ))
            channel : discord.TextChannel = initial_msg.channel
            await channel.send(embed=qEmbed(
                title="What is your profession?",
                description="**Examples:** Graphic Designer, Visual Editor, Motion Graphics Designer, etc."
            ))
            profession_msg : discord.Message = await self.bot.wait_for(
                'message',
                timeout=240,
                check=lambda m: m.channel.id == channel.id and m.author.id == ctx.author.id and len(m.content) < 60
            )
            profession = profession_msg.content
            # available_socials = ["Twitter", "Instagram", "Behance", "Dribbble", "FaceBook", "ArtStation", "DevianArt"]
            await channel.send(embed=qEmbed(
                title="Reply with a short bio.",
                description="Reply with a bio about yourself for your profile, tell people things like "
                            "the work you do and since you have been doing it, etc."
            ))
            bio_msg: discord.Message = await self.bot.wait_for(
                'message',
                timeout=240,
                check=lambda m: m.channel.id == channel.id and m.author.id == ctx.author.id
            )
            bio = bio_msg.content
            await channel.send(embed=qEmbed(
                title="Are you on Twitter?",
                description="If yes, reply with the **link to your twitter profile**.\n"
                            "If not, reply with **`no`**.",
            ))
            twitter_regex = r"(?:http:\/\/)?(?:www\.)?twitter\.com\/(?:(?:\w)*#!\/)?(?:pages\/)?(?:[\w\-]*\/)*([\w\-]*)"
            twitter_msg : discord.Message = await self.bot.wait_for(
                'message',
                timeout=240,
                check=lambda m: m.channel.id == channel.id and m.author.id == ctx.author.id
            )
            twitter_url = ''
            if twitter_msg.content.lower().startswith("no"):
                twitter_url = None

            twitter_url2 = re.findall(twitter_regex, twitter_msg.content)
            if twitter_url == '':
                if not twitter_url2:
                    twitter_url = None
                elif twitter_url2[0] == '':
                    twitter_url = None
                else:
                    twitter_url = twitter_url2[0]
            # print(twitter_url)
            await channel.send(embed=qEmbed(
                title="Are you on Instagram?",
                description="If yes, reply with the **link to your instagram profile**.\n"
                            "If not, reply with **`no`**.",
            ))
            insta_regex = r"(?:(?:http|https):\/\/)?(?:www\.)?(?:instagram\.com|instagr\.am)\/([A-Za-z0-9-_\.]+)"
            insta_msg: discord.Message = await self.bot.wait_for(
                'message',
                timeout=240,
                check=lambda m: m.channel.id == channel.id and m.author.id == ctx.author.id
            )
            insta_url = ''
            if insta_msg.content.lower().startswith("no"):
                insta_url = None

            insta_url2 = re.findall(insta_regex, insta_msg.content)
            if insta_url == '':
                if not insta_url2:
                    insta_url = None
                elif insta_url2[0] == '':
                    insta_url = None
                else:
                    insta_url = insta_url2[0]
            await channel.send(embed=qEmbed(
                title="Please link your portfolio",
                description="**Recommended:** Behance, YouTube Playlist, Dribbble, etc."
            ))
            url_regex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
            port_msg: discord.Message = await self.bot.wait_for(
                'message',
                timeout=240,
                check=lambda m: m.channel.id == channel.id and m.author.id == ctx.author.id and len(
                    re.findall(url_regex, m.content.lower())) == 1
            )
            portfolio = port_msg.content
            await channel.send(embed=qEmbed(title="Are your commissions open?",
                                        description="If yes, reply with **`yes`**.\n"
                                                    "If not, reply with **`no`**."))
            open_msg: discord.Message = await self.bot.wait_for(
                'message',
                timeout=240,
                check=lambda m: m.channel.id == channel.id and m.author.id == ctx.author.id and m.content.lower() in ["yes", "no"]
            )
            open = bool
            if open_msg.content.lower() == "yes":
                open = True
            else:
                open = False
            await channel.send(embed=qEmbed(title="Please reply with a profile banner",
                                            description="Reply with **__a web link__** to your profile banner**.\n"
                                                        "Ideal aspect ratio is 2:1."))
            banner_msg: discord.Message = await self.bot.wait_for(
                'message',
                timeout=240,
                check=lambda m: m.channel.id == channel.id and m.author.id == ctx.author.id and len(
                    re.findall(url_regex, m.content.lower())) == 1
            )
            banner_url = banner_msg.content
            Twitter = ("https://twitter.com/" + twitter_url) if twitter_url is not None else None
            Insta = ("https://instagram.com/" + insta_url) if insta_url is not None else None
            socials = json.dumps({"twitter" : Twitter, "instagram" : Insta})
            # await channel.send(f"Socials:\n"
            #                    f"{socials}\n"
            #                    f"Banner:\n"
            #                    f"{banner_url}\n"
            #                    f"Portfolio:\n"
            #                    f"{portfolio}\n"
            #                    f"Profession:\n"
            #                    f"{profession}\n"
            #                    f"Commissions Open:\n"
            #                    f"{open}")

            query = "INSERT INTO profiles (user_id, socials, profession, portfolio, commissions_open, banner, registered_at, bio)" \
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"
            await self.bot.pool.execute(query, str(ctx.author.id), socials, profession, portfolio, open, banner_url, datetime.datetime.utcnow(), bio)
            await banner_msg.add_reaction("✅")
            await ctx.message.add_reaction("✅")
            await channel.send(embed=qEmbed(title="Successfully registered your profile!",
                                            description="To view the profile, type `.profile`.\n"
                                                        "To edit the profile, type `.help set`."))

        except Exception as e:
            if isinstance(e, asyncio.TimeoutError):
                await ctx.author.send(embed=qEmbed(
                    title="You did not answer in time!",
                    description="You can still retry by running the command again.",
                    # color=discord.Color.red()
                ))
            elif isinstance(e, discord.Forbidden):
                await ctx.send(embed=qEmbed(
                    title="Please open your DMs and try again",
                    # color=discord.Color.red()
                ))
            else:
                raise e
        # return await ctx.send("Under development.")
