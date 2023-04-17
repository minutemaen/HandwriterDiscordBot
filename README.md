# HandwriterDiscordBot
 
sherlockdoyle - Handwriter https://github.com/sherlockdoyle/Handwriter

Ports sherlockdoyle - Handwriter script to a discord bot with some added parameters.

Goes from discord post -> pdf -> .png -> handwriter.py -> output-cropped.png

# Prereqs


# Installation
Included poppler for windows
Extract it somewhere in the computer then navigate to the bin folder inside that folder poppler-23.01.0 > Library > bin

Then select the bin folder and copy its path as text

It should look like this: "E:\Directory\To\The\Bin\poppler-23.01.0\Library\bin"

Go back to the ".env" file and paste path in its place (i.e POPPLER_BIN_PATH="E:\Directory\To\The\Bin\poppler-23.01.0\Library\bin")

Save and close the file and run the bot through a CMD console

 python main.py


# Running in Linux

You only need to install the poppler-utils module for linux for the bot to work

sudo apt install poppler-utils

Make the POPPLER_BIN_PATH in .env "NONE" (i.e POPPLER_BIN_PATH="NONE")

Run the bot      python3 main.py






# Usage

## Commands you can use:
### LetterBot
!letter <Text> -> !letter Sample letter here
Generates handwritten letters


!set_channel <ChannelMentionOrID> -> !set_channel channelID or !set_channel #letters
Sets where the letters will be sent after prompt

!settings
 Bot shows what settings can be customized
Settings
LETTER_CHANNEL = 
TARGET_CHANNEL = 
EMOJI_ID = 
VERTICAL_SPACING = 
HORIZONTAL_SPACING = 
FONT = 
FONT_SIZE = 
CROP = 
Use this command like this to set settings !settings VERTICAL_SPACING 20

!fonts

Put any font you want in the Fonts folder and it can be used if set in the settings
!fonts is just a command that tells you what fonts are usable and how you can set the fonts in the settings





## Todo

Integrate mistakes macro
Add button to change font instead of manually doing it

Optimize code so heartbeat doesnt die.
