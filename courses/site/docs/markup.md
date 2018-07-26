Markup Syntax
=============

You can edit umber pages using [markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet) and [html](https://en.wikipedia.org/wiki/HTML) with snips of [LaTeX](https://en.wikipedia.org/wiki/LaTeX) for math.

The rules are :

* Plain text is wrapped. Blank lines indicate paragraphs.
* Block quotes in which whitespace is unchanged are set by indenting each line four spaces.
* Links are made with brackets and parens :&#91;displayed text&#93;(url)
* Heading and sub-headings are marked with either # or ## or by underlining with == or -- .
* Bullet lists have a * for each a line - and leave a blank line before and after the list.
* Horizontal lines are given by ----- .
* Code blocks with syntax highlights are created with triple ticks, [as on github](https://help.github.com/articles/creating-and-highlighting-code-blocks/).
* Math LaTeX inline expressions are delimited with slash parens, e.g. `\(  e^\pi \)` while equations on their own line should be placed between bracket parens e.g. `\[ x = \frac{1}{1+x} \]`

Below are examples of these rules. 

And you can see the markup which created this page at [markup.txt](markup.txt).

Plain Text
----------

This is text 
on several lines
which is wrapped into one   paragraph. Whitespace is adjusted as needed.

And here is a second paragraph.


Block Quotes
------------

    This is a block    quote
    in which   the whitespace is left unchanged.

Each line of a block quote starts with four spaces.

Links
-----

Here's a link to the [Marlboro College homepage](https://www.marlboro.edu). 

Markdown files end in a ".md" extension which need not be given in in url. 
So [this](this) is a link to "this.md" in the current folder.

Clicking on a link to a file that doesn't exist yet will allow you to 
create that file if you have the rights to edit files in that folder.

As usual, urls can be absolute (i.e. http://amazon.com) or relative 
to the current folder (i.e. subfolder/file.html or ../parent). 

The &#126; character is used to indicate a course's home folder, so 
for example &#126;/home would be the url of a course's home page.

Pages may have attachments, which are placed in a corresponding folder.
For a file "foo.md", its attachments would be put in "foo.attachments/".

Bullet Lists
------------

This markup text

    * one
    * two
       * two and a half
    * three

displays as

* one
* two
  * two and a half
* three

Leave a blank line before and after.

Starting each line with 1. gives a numbered list.

1. one
1. two
1. three


Code Blocks
-----------

Math LaTeX
----------


----------




