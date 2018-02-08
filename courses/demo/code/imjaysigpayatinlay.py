"""
 imjayigpayatinlay.py

 Jim's pig latin

 See ./readme.md.  

 Here are tests based on the design constraints, 
 in roughly order of increasing difficulty.

 --- tests --------------------------------------

 >>> text_to_piglatin("apple")     # word starts with vowel
 'appleway'

 >>> text_to_piglatin("cat")       # word starts with consonant
 'atcay'

 >>> text_to_piglatin("strike")    # word starts with consonant cluster
 'ikestray'

 >>> text_to_piglatin("style")     # "y" within word is vowel
 'ylstay'

 >>> text_to_piglatin("yellow")    # "y" starts word is consonant
 'ellowyay'

 >>> text_to_piglatin("quiet")     # "qu" is treated as a single letter
 'ietquay'

 >>> text_to_piglatin("one two three")       # multiple words
 'oneway otway eethreway' 

 >>> text_to_piglatin("one, two, three!")    # puncuation
 'oneway, otway, eethreway!'

 >>> text_to_piglatin("South Bend Indiana")  # capitalization
 'Outhsay Endbay Indianaway'

 >>> text_to_piglatin('The cat said "meow".')  # sentence, more punctuation
 'Ethay atcay aidsay "eowmay".'

 >>> text_to_piglatin("an off-campus apartment")  # hyphenated word
 'anway offway-ampuscay apartmentway'

 >>> text_to_piglatin("(foo) [bar]")  # parens and brackets
 '(oofay) [arbay]'

 >>> text_to_piglatin("It is 7.3 inches high.")    # words and numbers
 'Itway isway 7.3 inchesway ighhay."             

 >>> text_to_piglatin("17 23.2 one2 s78 7th")     # pure and mixed numbers
 '17 23.2 one2way 78say 7thway'

 >>> text_to_piglatin("Célébrons la 10e saison de BIXI en 2018!")  # diacritic
 'Élébronsay laway 10eway aisonsay eday enway 2018!'

 >>> text_to_piglatin("And I can't stand him.")   # contraction
 'Andway Iway an'tcay andstay imhay.'

 >>> text_to_piglatin("His name is Dr. Jones.")   # words with only consonants
 'Ishay amenay isway Adray. Onesjay.'

 >>> text_to_piglatin('He said "Сказки братьев Гримм" on the 12th of month 7.')
 'Ehay aidsay "Сказки братьев Гримм" onway ethay 12thway ofway onthmay 7.'

 ----------------------------------------------------------

 Jim Mahoney | Feb 2018 | cs.marlboro.college | MIT License
"""

vowels = set(['a', 'e', 'i', 'o', 'u'])

def split_word(word):
    """ Return leading consonant cluster (leading) 
        and the rest of the characters
        >>> split_word("scratch")
        ('scr', 'atch')
    """
    leading = ''
    rest = word
    while rest and rest[0] not in vowels:
        leading += rest[0]
        rest = rest[1:]
    return (leading, rest)

def word_to_piglatin(word):
    """ Convert one word to piglatin 
        >>> word_to_piglatin('card')
        'ardcay'
        >>> word_to_piglatin('oops')
        'oopsway'
    """
    if word[0] in vowels:
        return word + 'way'
    else:
        (leading, rest) = split_word(word)
        return rest + leading + 'ay'

def text_to_piglatin(text):
    """ Return text translated to pig latin. """
    # TODO: Handle more than the simplest case ...
    words = text.split(' ')    
    pig_words = map(word_to_piglatin, words)
    pig_text = ' '.join(pig_words)
    return pig_text

if __name__ == "__main__":
    import doctest
    doctest.testmod()
