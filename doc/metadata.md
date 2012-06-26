---
Title: Metadata
---
In both the Creole and the Markdown files, there is a time when entering metadata can help with the writing process. This information comes as a key/value pair, separated by a colon.

	Title: A Title
	Copyright: 2012, D. Moonfire
	Keywords: Documentation

Metadata can include any of the following information:

* The title of the story, chapter, or novel (collectively "the piece")
* Date of publication
* Copyright
* Byline used to write it
* Keywords/Terms:
  * Categorization of the piece
  * Point of view
  * Time and Location

When possible, the information is placed in the appropriate DocBook element. For the others, they are placed into a DocBook `<subjectset/>`.

Metadata is case-sensitive which means "Author" is not "author" or "aUTHOR".

# Formatting Metadata Tags

There are two ways of formatting the metadata in a document.

## Bullet Metadata

The first is an unordered list right underneath the heading of the file. The first heading will become the title of the document at each of the bullets will be parsed as a metadata key/value pair.

In a Creole document, this would look like:

	= A Title
	* Copyright: 2012, D. Moonfire
	* Keywords: Documentation
	
	It was a dark and stormy resturant...

## Header Metadata

The second is a block of text at the very beginning separated by two horizontal lines. There is no bullet list and the title is given as a key/value pair.

Using Markdown, an example would be:

	---
	Title: A Title
	Copyright: 2012, D. Moonfire
	Keywords: Documentation
	---
	It was a dark and stormy resturant...

# Metadata Tags

The following metadata is considered "known" and is placed into the appropriate element in the resulting DocBook file.

* "Title": The `<title/>` element inside the root-level XML document. This has special rules depending on the style of metadata (see below).
* "Copyright": In the format of "Year, Holder" and is put into the copyright block of the root `<info/>` element.
* "Author": In the format of "Name" or "Last Name, First Name". This is parsed into the `<author/>` element of the `<info/>` element and broken into given and surnames.
* "Date": Given in ISO format ("YYYY-MM-DD") and will be put into the `<date/>` element of the root `<info/>` element.
* "Keywords": These are a comma-separated list of keywords. If there is a semicolon in the line, then it will be semicolon-separated list of keywords. There can be multiple Keywords and they will be combined together.

The remaining metadata tags will be put into subject sets in the resulting DocBook file with the subject set scheme being the name of the metadata and the elements a comma (or semicolon if present) separated values.

# Subjectsets

Subjectsets are a very useful tool when keeping track of information about a chapter or story. It can be used to categorize a piece, such as genre, themes, or setting.

* Genre: Steampunk, Humor
* Setting: Fedran
* Theme: Loss of life, Inspirational, Vampire hamsters

If you are someone who likes to categorize with more specific taxonomies, then you can easily do those with metadata.

* Magic System: Gesture, Spoken
* Scene Type: Campsite, Musical
* Intensity: Fight, Monologue

Likewise, you can use these to keep track of information about the piece.

* Series: Blood of the Moon
* Volume: 2
* Source: Commissioned
* Public: No
* Point of View: Billy Jo
* Location: North of the campsite
* Time: 2 am
* Participants: Billy Jo; Billy Ray; Mo

There are tools for selecting DocBook files with these tags to make it easier to get a list of chapters that have a specific point of view, stories in a genre, or however it works.