def split_attribute(input):
    """
properly split apart attribute strings, even when they have sub-attributes declated between [].
:param input:the attribute string to split
:return: dict containing the elements of the top level attribute string.
Sub-attribute strings between '[]'s are appended to their parent, without processing, even if they contain '.'
"""
    ret = []
    # zero means we are not inside square brackets
    squareBrackets = 0
    lastIndex = 0
    for i in range(len(input)):
        if input[i] == '[':
            squareBrackets +=1
        elif input[i] == ']':
            squareBrackets -=1
        elif input[i] == '.' and squareBrackets == 0:
            ret.append(input[lastIndex:i])
            lastIndex =i+1

    #last element
    ret.append(input[lastIndex:])
    return ret