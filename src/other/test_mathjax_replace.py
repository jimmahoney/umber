# python2

import random, re

def make_marker(bits=64):
    """ Return a unique string that , for marking boundaries in text """
    #  i.e. ' |-b1dda1c7f14cd89e-| '
    # In python2, hex() on big numbers gives i.e. '0x3333333333L'.
    # I'll drop the 1st two and last chars with [2:-1].
    return ' |-'+hex(random.getrandbits(64))[2:-1]+'-| '

def mathjax_replace(text):
    """ Replace substrings of text between several boundaries
        $$...$$ ,  \(...\) , \[...\] with unique-ish boundary markers.
        Return new text and dictionary of markers and replaced substrings.
    """
    replacements = {}
    for expr in (r'\$\$.*?\$\$',       #   $$ ... $$
                 r'\\\(.*?\\\)',       #   \( ... \)
                 r'\\\[.*?\\\]'):      #   \[ ... \]
        pattern = re.compile(expr)
        while True:
            match = re.search(pattern, text)
            if not match:
                break
            substring = match.group(0)
            m = make_marker()
            replacements[m] = substring
            text = text.replace(substring, m)
    return (text, replacements)

def undo_mathjax_replace(text, replacements):
    for mark in replacements:
        text = text.replace(mark, replacements[mark])
    return text

text1 = r'prelude stuff $$ middle stuff $$ last stuff'
text2 = r'prelude stuff \( middle stuff \) last stuff'
text3 = r'prelude stuff \[ middle stuff \] last stuff'
text4 = r'Stuff for \(all\) $$three types$$ with \(repeats\) \[so\] $$there$$.'

for text in (text1, text2, text3, text4):
    (newtext, lookup) = mathjax_replace(text)
    print "text = '{}'".format(text)
    print "newtext = '{}'".format(newtext)
    for m in lookup:
        print "(mark, substring) = ('{}', '{}')".format(m, lookup[m])
    original = undo_mathjax_replace(text, lookup)
    print "original = '{}'".format(original)
    print


