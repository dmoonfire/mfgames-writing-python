---
Title: Purpose
---
Even though most open-source projects don't have one, it is sometimes useful to have a mission statement to guide development:

> The purpose of this set of utilities is to facilitate writing stories and novels using text-based files and provide the tools needed to transform those files into other usable formats.

# Text Files

The purpose of MfGames Writing is centered around using text files to write stories and novels. There are text editors for every known operating system in the world, from VAX to Apple to Windows 7. It is a format that has the highest interoperability of all known writing formats.

The drawback of text documents is that they don't include a lot of presentation information. With a text file, there aren't margins to deal with, fonts to choose from, or even clip art to obsess about. For pure writing, novels and stories, this is usually acceptable since most writers don't use any additional formatting beyond the occasional **bold** or *italic* phrase or text.

There are markup formats that include the basic formatting most stories (we'll combine stories and novels in here along with most other narrative formats). These tools is designed to work with many of them, mainly to fit with the needs of the writer, not the tool.

# Source Control

A critical part of writing is keeping old revisions. From impromptu surveys, one of the most common methods is "copy revisions". This can be something as simple as creating a copying and appending "r1" to the end of it to completely directory copies.

Another approach is to take ideas from software development and use source control management (SCM). These are programs that work on source files to keep track of revisions and allow the ability to test out new ideas, roll back to previous versions, and more importantly, see the changes over time.

Binary files (Microsoft Word, Oasis Document Format) are difficult to show changes over time unless you use the application itself. When a binary file changes, most SCM will keep a full copy of the change. However, with text files, SCM will only save the differences from the previous version. This means that it is faster to review changes but also to store over time.

SCM also allow merging from multiple sources. For example, say your primary writing environment is a desktop. You work on stuff as you go. But, then you happen to get inspiration for a chapter and bang it out on your laptop. It might be the same chapter on the desktop. If done improperly, one of those files could be lose when merging the results. With source control, there are tools not only to guide merging the changes but also allowing you to look through the history and recover the changes that were accidentally overwritten.

# Other Formats

Using text files and source control helps with the writing process, but rarely do editors, beta eaders, and publishers take unformatted text files. An serivce may require Microsoft Word so they can comment or you may want to put it on your Kindle to change how you read it.

One part of MfGames Writing is to be able to turn text files into other file formats for that purpose. When possible, going in the reverse is also useful to pull changes back into the text files.