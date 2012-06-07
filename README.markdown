# MfGames Writing Toolkit

The writing toolkit is a set of command-line utilities to facilitate
working with a relatively low overhead file format, such as Markdown
or Creole. It focuses mostly on transforming to and from DocBook 5 as
an intermediate format, but also includes some query and formatting
tools.

## Creole

The program `mfgames-creole` is used to convert a Creole file into
DocBook 5. This allows various customizations as part of the parsing,
including encoding document metadata within the Creole file, handling
blockquotes and epigraphs, or making "pretty" quotes.

## DocBook 5

DocBook 5 is a pure XML format of DocBook. `mfgames-docbook` is used
to convert DocBook 5 into other file formats, including Creole and
BBCode. It also includes functions for querying information from
DocBook files or preparing them for parsing/generation.

## OPF and NCX Files

`mfgames-ncx` and `mfgames-opf` are utilities for manipulating and
querying NCX and OPF files respectively.

## Requirements

The following Python libraries are used:

* Creoleparser (easy_install)
* SmartyPants (easy_install)