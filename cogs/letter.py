import asyncio
import os
import random
import shutil
import traceback

from discord.ext import commands
from discord import app_commands
import discord

import pdf2image

from fpdf import FPDF

import numpy as np
import cv2

import json

import handwriting
from dotenv import load_dotenv

from pypdf import PdfReader, PdfWriter

import platform

separator = "/"
if platform.system() == "Windows":
    separator = "\\"
if platform.system() == "Linux":
    separator = "/"

load_dotenv()

POPPLER_BIN = os.getenv("POPPLER_BIN_PATH")

if POPPLER_BIN == "NONE":
    POPPLER_BIN = None
else:
    if not os.path.exists(POPPLER_BIN):
        POPPLER_BIN = None
    else:
        POPPLER_BIN.replace("\b", r"\\b")
print(POPPLER_BIN)

try:
    with open("config.json", "r") as s:
        c = json.load(s)
except:
    sample = {"LETTER_CHANNEL": 0}
    with open("config.json", "w") as s:
        json.dump(sample, s)


class LetterBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command("letter")
    async def make_letter(self, ctx: commands.Context, *, letter: str):
        df = await ctx.send("Generating...")
        # PDF CREATION
        with open("config.json", "r") as e:
            config = json.load(e)
        try:
            if config["LETTER_CHANNEL"] == 0:
                channel = ctx.channel
            else:
                channel = await self.bot.fetch_channel(config["LETTER_CHANNEL"])
        except:
            channel = ctx.channel
        if not os.path.exists(f"tmp/"):
            os.mkdir(f"tmp/")
        if not os.path.exists(f"out/"):
            os.mkdir(f"out/")

        class MessageView(discord.ui.View):
            def __init__(self, dir: str, letter: str):
                super().__init__(timeout=None)
                self.dir = dir
                self.letter = letter

            @discord.ui.button(label="Redo", style=discord.ButtonStyle.blurple)
            async def redo(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message("Loading...", ephemeral=True)
                pdf = PDF(orientation='P', unit='mm', format='A4')

                pdf.add_page()
                pdf.set_font(config["FONT"], '', config["FONT_SIZE"])
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(config["HORIZONTAL_SPACING"], config["VERTICAL_SPACING"], letter + "\n", 0, "L", False)

                pdf.output(f"tmp/{ctx.author.id}.pdf", "F")

                if POPPLER_BIN is None:
                    images = pdf2image.convert_from_path(f"tmp/{ctx.author.id}.pdf", )
                else:
                    images = pdf2image.convert_from_path(f"tmp/{ctx.author.id}.pdf", poppler_path=POPPLER_BIN)

                await asyncio.sleep(1)
                if not os.path.exists(f"tmp/{ctx.author.id}/"):
                    os.mkdir(f"tmp/{ctx.author.id}/")
                for i, c in enumerate(images):
                    await asyncio.sleep(1)
                    images[i].save(f"tmp/{ctx.author.id}/{ctx.author.id}-{i}.png")
                ts = int(interaction.created_at.timestamp())
                handwriting.apply([f"tmp/{ctx.author.id}/"], ctx.author.id, ts)

                # APPLY CROPPING
                pdf = PdfWriter()
                for i, dir in enumerate(os.listdir(f"out/{ctx.author.id}/{ts}/")):
                    if ".png" in dir:
                        img = cv2.imread(fr"out/{ctx.author.id}/{ts}/{dir}")
                        # Read in the image and convert to grayscale
                        # img = img[:-20, :-20]  # Perform pre-cropping
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        gray = 255 * (gray < 50).astype(np.uint8)  # To invert the text to white
                        gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, np.ones(
                            (2, 2), dtype=np.uint8))  # Perform noise filtering
                        coords = cv2.findNonZero(gray)  # Find all non-zero points (text)
                        x, y, w, h = cv2.boundingRect(coords)  # Find minimum spanning bounding box
                        # Crop the image - note we do this on the original image
                        rect = img[0:(y + h) * 3, 0:img.shape[1]]
                        # cv2.imwrite(f"out/{ctx.author.id}/{ts}/{dir.replace('.png', '-cropped.png')}", rect)
                        print(x, y, w, h)
                        awa = h
                        tmp_pdf = PdfReader(f"tmp/{ctx.author.id}.pdf")
                        page = tmp_pdf.pages[i]
                        print(h)
                        print(page.mediabox.lower_right[1])
                        page.mediabox.lower_right = (page.mediabox.lower_right[0], ((h / 2) + y))
                        pdf.add_page(page)
                with open(f"tmp/{ctx.author.id}.pdf", "wb") as o:
                    pdf.write(o)

                if POPPLER_BIN is None:
                    images = pdf2image.convert_from_path(f"tmp/{ctx.author.id}.pdf", )
                else:
                    print(repr(POPPLER_BIN))
                    images = pdf2image.convert_from_path(f"tmp/{ctx.author.id}.pdf",
                                                         poppler_path=r"{}".format(POPPLER_BIN))

                await asyncio.sleep(1)
                if not os.path.exists(f"tmp/{ctx.author.id}/"):
                    os.mkdir(f"tmp/{ctx.author.id}/")
                for i, c in enumerate(images):
                    await asyncio.sleep(1)
                    images[i].save(f"tmp/{ctx.author.id}/{ctx.author.id}-{i}.png")
                ts = int(ctx.message.created_at.timestamp())
                handwriting.apply([f"tmp/{ctx.author.id}/"], ctx.author.id, ts, cropped=True)

                files = []
                for dir in os.listdir(f"out/{ctx.author.id}/{ts}/"):
                    if ".png" in dir and "-cropped" in dir:
                        files.append(discord.File(f"out/{ctx.author.id}/{ts}/{dir}", filename=dir))

                r_msg = "\n".join([f"> {sent}" for sent in letter.split("\n")])
                message = f"Letter from {ctx.author.display_name}\n\n{r_msg}"
                view = MessageView(f"out/{ctx.author.id}/{ts}/", letter)
                await interaction.message.edit(content=message[:1999], attachments=files, view=view)
                await interaction.edit_original_response(content="Generated!")
                shutil.rmtree(f"tmp/{ctx.author.id}")

            # @discord.ui.button(label="View Full Image")
            # async def view_full(self, interaction: discord.Interaction, button: discord.ui.Button):
            #     await interaction.response.send_message("Loading...", ephemeral=True)
            #     files = []
            #     for dir in os.listdir(self.dir):
            #         if ".png" in dir and "-cropped" not in dir:
            #             files.append(discord.File(f"out/{ctx.author.id}/{ts}/{dir}", filename=dir))
            #     await interaction.edit_original_response(content="",attachments=files)

        class PDF(FPDF):
            def __init__(self, **kwargs):
                super(PDF, self).__init__(**kwargs)
                for path in os.listdir("Fonts"):
                    self.add_font(path.split(".ttf")[0], "", os.path.abspath(os.path.join(r"Fonts" + separator + path)),
                                  uni=True)

        try:
            pdf = PDF(orientation='P', unit='mm', format='A4')

            pdf.add_page()
            pdf.set_font(config["FONT"], '', config["FONT_SIZE"])
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(config["HORIZONTAL_SPACING"], config["VERTICAL_SPACING"], letter + "\n", 0, "L", False)

            pdf.output(f"tmp/{ctx.author.id}.pdf", "F")
            ts = int(ctx.message.created_at.timestamp())
            ctx.author.id
            if not os.path.exists(f"out/{ctx.author.id}/"):
                os.mkdir(f"out/{ctx.author.id}/")
            if not os.path.exists(f"out/{ctx.author.id}/{ts}/"):
                os.mkdir(f"out/{ctx.author.id}/{ts}/")
            # PDF2IMG
            if POPPLER_BIN is None:
                images = pdf2image.convert_from_path(f"tmp/{ctx.author.id}.pdf", )
            else:
                print(repr(POPPLER_BIN))
                images = pdf2image.convert_from_path(f"tmp/{ctx.author.id}.pdf", poppler_path=r"{}".format(POPPLER_BIN))
            await asyncio.sleep(1)
            if not os.path.exists(f"tmp/{ctx.author.id}/"):
                os.mkdir(f"tmp/{ctx.author.id}/")
            for i, c in enumerate(images):
                await asyncio.sleep(1)
                images[i].save(f"tmp/{ctx.author.id}/{ctx.author.id}-{i}.png")
            for i, c in enumerate(images):
                await asyncio.sleep(1)
                images[i].save(f"out/{ctx.author.id}/{ts}/{i}.png")

            # handwriting.apply([f"tmp/{ctx.author.id}/"], ctx.author.id, ts)

            awa = 0

            # APPLY CROPPING
            if config["CROP"]:
                print("APPLYING CROPPING")
                pdf = PdfWriter()
                for i, dir in enumerate(os.listdir(f"out/{ctx.author.id}/{ts}/")):
                    if ".png" in dir:
                        img = cv2.imread(fr"out/{ctx.author.id}/{ts}/{dir}")
                        # Read in the image and convert to grayscale
                        # img = img[:-20, :-20]  # Perform pre-cropping
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        gray = 255 * (gray < 50).astype(np.uint8)  # To invert the text to white
                        gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, np.ones(
                            (2, 2), dtype=np.uint8))  # Perform noise filtering
                        coords = cv2.findNonZero(gray)  # Find all non-zero points (text)
                        x, y, w, h = cv2.boundingRect(coords)  # Find minimum spanning bounding box
                        # Crop the image - note we do this on the original image
                        rect = img[0:(y + h) * 3, 0:img.shape[1]]
                        # cv2.imwrite(f"out/{ctx.author.id}/{ts}/{dir.replace('.png', '-cropped.png')}", rect)
                        print(x, y, w, h)
                        awa = h
                        tmp_pdf = PdfReader(f"tmp/{ctx.author.id}.pdf")
                        page = tmp_pdf.pages[i]
                        print(h)

                        print(page.mediabox.lower_right)
                        print(page.mediabox.upper_right)
                        print((h - (h - page.mediabox.upper_right[1])))
                        y_cord = page.mediabox.upper_right[1] - (h / 2)
                        if 3000 > h > 1200:
                            y_cord = (h / 12)
                            print("sdasd", y_cord, "\n", (h / 12), "\n\n")
                            if y_cord > 420 or y_cord < 200:
                                y_cord = 0
                        if 200 > h > 30:
                            y_cord = page.mediabox.upper_right[1] - (h * 2)
                        print("ycord =", y_cord)
                        page.mediabox.lower_right = (page.mediabox.lower_right[0], y_cord)
                        pdf.add_page(page)
                with open(f"tmp/{ctx.author.id}.pdf", "wb") as o:
                    pdf.write(o)

            if POPPLER_BIN is None:
                images = pdf2image.convert_from_path(f"tmp/{ctx.author.id}.pdf", )
            else:
                print(repr(POPPLER_BIN))
                images = pdf2image.convert_from_path(f"tmp/{ctx.author.id}.pdf", poppler_path=r"{}".format(POPPLER_BIN))

            await asyncio.sleep(1)
            if not os.path.exists(f"tmp/{ctx.author.id}/"):
                os.mkdir(f"tmp/{ctx.author.id}/")
            for i, c in enumerate(images):
                await asyncio.sleep(1)
                images[i].save(f"tmp/{ctx.author.id}/{ctx.author.id}-{i}.png")
            ts = int(ctx.message.created_at.timestamp())
            handwriting.apply([f"tmp/{ctx.author.id}/"], ctx.author.id, ts, cropped=True)

            files = []
            for dir in os.listdir(f"out/{ctx.author.id}/{ts}/"):
                if ".png" in dir and "-cropped" in dir:
                    files.append(discord.File(f"out/{ctx.author.id}/{ts}/{dir}", filename=dir))

            r_msg = "\n".join([f"> {sent}" for sent in letter.split("\n")])
            message = f"Letter from {ctx.author.display_name}\n\n{r_msg}"
            view = MessageView(f"out/{ctx.author.id}/{ts}/", letter)
            await channel.send(message[:1999], files=files, view=view)
            shutil.rmtree(f"tmp/{ctx.author.id}")
            await df.edit(content="Generated!")
        except Exception as e:
            await df.edit(content=f"**ERROR**\n```{str(traceback.format_exc())[:1700]}```")

    @commands.command(name="set_channel")
    async def set_channel(self, ctx: commands.Context, channel: discord.abc.GuildChannel = None):
        if channel is None: channel = ctx.channel
        try:
            with open("config.json", "r") as e:
                config = json.load(e)
            config["LETTER_CHANNEL"] = channel.id
            with open("config.json", "w") as c:
                json.dump(config, c)
        except Exception as e:
            return await ctx.send(f"**ERROR**:\n```{e}```")
        await ctx.send(f"Generated letter will now be sent to {channel.mention}")

    @commands.command(name="settings")
    async def settings_command(self, ctx: commands.Context, arg1: str = None, arg2=None):
        if arg1 is None:  # if arg1 is None, then arg2 will most probably be None
            with open("config.json", "r") as a:
                config = json.load(a)
            embed = discord.Embed(title="Settings", colour=0xD7D7D7)
            embed.description = "" + "\n".join([f'`{c}` = {e}' for c, e in config.items()])
            embed.set_footer(text="use this command like this to set settings !settings VERTICAL_SPACING 20")
            await ctx.send(embed=embed)
        else:
            allowed_keys = ["LETTER_CHANNEL", "TARGET_CHANNEL", "EMOJI_ID", "VERTICAL_SPACING", "HORIZONTAL_SPACING",
                            "FONT", "FONT_SIZE", "CROP"]
            with open("config.json", "r") as a:
                config = json.load(a)
            if not arg1.upper() in allowed_keys:
                return await ctx.send("This key is not the settings")

            int_vals = ["LETTER_CHANNEL", "TARGET_CHANNEL", "VERTICAL_SPACING", "HORIZONTAL_SPACING", "FONT_SIZE"]
            bool_vals = ["CROP"]

            if arg1.upper() in int_vals:
                config[arg1.upper()] = int(arg2)
            elif arg1.upper() in bool_vals:
                if arg2.lower() in ["false", "False", "True", "true"]:
                    if arg2.lower() in ["false", "False"]:
                        arg2 = False
                    else:
                        arg2 = True
                config[arg1.upper()] = arg2
            else:
                config[arg1.upper()] = arg2

            with open("config.json", "w") as v:
                json.dump(config, v)
            await ctx.send(f"Successfully set `{arg1.upper()}` to `{arg2}`")

    @commands.command(name="fonts")
    async def available_fonts(self, ctx: commands.Context):
        fonts = [path for path in os.listdir("Fonts") if not path.endswith(".pkl")]
        embed = discord.Embed(title="Available Fonts", color=0xD7D7D7)
        embed.description = "Use this font names to set a font using the !settings command\n```!settings FONT [FONT-NAME]```\n" + "\n".join(
            [f'`{font.replace(".ttf", "")}`:\n```!settings FONT {font.replace(".ttf", "")}```' for font in fonts])
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(LetterBot(bot))
