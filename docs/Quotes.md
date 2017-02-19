# Quotes Plugin

## Description

This is a *GOGbot* plugin that allows to store and fetch text snippets
(ie quotes).

## Usage

To trigger the *Quotes* plugin in chat issue one of the following commands.

### `!quote` or `!quote #<number>`
Display the quote with index value `<number>` or display a random quote if no
number provided. Example:
```irc
<<< !quote
>>> #129: "YES! We live to be incompetent another day." - Darksaber2K [Games + Demos] [10.03.2016]

<<< !quote 129
>>> #129: "YES! We live to be incompetent another day." - Darksaber2K [Games + Demos] [10.03.2016]
```

### `!quote add "<text>" -- <streamer>`
This is a privileged command, requires moderator permissions.

Adds a new quote to the database. Replace `<text>` with the quoted text and
`<streamer>` with their Twitch handle. Note that the game name and the current
date will be added automatically to the new quote. Example:
```irc
<<< !quote add 'You made it sad and also dead.' - DeviateFish on MemoriesIn8Bit deeds in
>>> Added quote #216

<<< !quote 216
>>> #216: 'You made it sad and also dead.' - DeviateFish on MemoriesIn8Bit deeds in [Momodora: Reverie Under the Moonlight] [19.02.2017]
```

### `!quote rawadd "<text>" -- <streamer> [<game>] [<date>]`
This is a privileged command, requires moderator permissions.

Adds a new quote to the database as given. This adds the text following
`!quote rawadd` verbatim so you'd generally want to add the game name and
date within brackets so that the new quote will look like an existing quote
added by `!quote add`.

### `!quote del #<number>`
This is a privileged command, requires moderator permissions.

Removes the quote with id `<number>` from the database.
