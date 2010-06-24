"""Odl lexer and parser
"""

# Odl lexer

import ply.lex as lex

reserved = {
    'Configuration' : 'CONFIGURATION',
    'Attribute'     : 'ATTRIBUTE',
    'Version'       : 'VERSION',
    'Object'        : 'OBJECT',
    'Relationship'  : 'RELATIONSHIP',
    'TRUE'          : 'TRUE',
    'FALSE'         : 'FALSE',
    'File'          : 'FILE',
    'Operation'     : 'OPERATION',
    'Copy'          : 'COPY'
}

tokens = ['STRING'] \
    + list(reserved.values())

literals = [ '{', '}', ',', ';' ]

def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID') # Check for reserved words
    return t

def t_STRING(t):
    r'\"([^\"\\]|\\[\"\\])*\"'
    t.value = t.value[1:len(t.value) - 1]
    t.value = t.value.replace("\\\\", "\\")
    t.value = t.value.replace("\\\"", "\"")
    t.value = t.value.replace("\x0c", "")
    return t

t_ignore_COMMENT = r'//.*'

t_ignore = ' \r\t'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += 1

def t_error(t):
    """Error handling rule
    """
    print "Illegal character '" + t.value[0] \
        + "' in odl file on line " + str(t.lexer.lineno)
    t.lexer.skip(1)

odl_lexer = lex.lex()

# Odl parser

import ply.yacc as yacc

def p_top_entries(p):
    """top_entries : top_entries top_entry ';'
                   | top_entry ';'
    """

    if len(p) == 4:
        p[0] = p[1]

        if p[2] != None:
            p[0][p[2][0]] = p[2][1]
    else:
        p[0] = {}

        if p[1] != None:
            p[0][p[1][0]] = p[1][1]

def p_top_entry(p):
    """top_entry : configuration
                 | object
    """

    p[0] = p[1]

def p_configuration(p):
    """configuration : CONFIGURATION STRING STRING details
    """

    p[0] = (p[3], (p[2], p[4]))

def p_object(p):
    """object : OBJECT STRING STRING details
    """

    p[0] = (p[3], (p[2], p[4]))

def p_details(p):
    """details : '{' '}'
               | '{' detail_entries '}'
    """

    if len(p) == 3:
        p[0] = []
    else:
        p[0] = p[2]

def p_detail_entries(p):
    """detail_entries : detail_entries detail ';'
                      | detail ';'
    """

    if len(p) ==  4:
        p[0] = p[1]
        p[0].append(p[2])
    else:
        p[0] = [p[1]]

def p_detail(p):
    """detail : attribute
              | configuration_in
              | version
              | relationship
              | file
    """

    p[0] = p[1]

def p_attribute(p):
    """attribute : ATTRIBUTE STRING attribute_details
    """

    p[0] = ("Attribute", p[2], p[3])

def p_attribute_details(p):
    """attribute_details : TRUE
                         | FALSE
                         | STRING details
                         | string_list
    """

    if len(p) == 3:
        p[0] = (p[1], p[2])
    else:
        p[0] = p[1]

def p_string_list(p):
    """string_list : string_list ',' STRING
                   | STRING
    """

    if len(p) == 4:
        p[0] = p[1]
        p[0].append(p[3])
    else:
        p[0] = [p[1]]

def p_configuration_in(p):
    """configuration_in : CONFIGURATION STRING STRING STRING
    """

    p[0] = ("Configuration", p[2], p[3], p[4])

def p_version(p):
    """version : VERSION STRING details
    """

    p[0] = ("Version", p[2], p[3])

def p_relationship(p):
    """relationship : RELATIONSHIP STRING STRING STRING
    """

    p[0] = ("Relationship", p[2], p[3], p[4])

def p_file(p):
    """file : FILE OPERATION COPY
    """

    p[0] = ("File", None)

def p_error(p):
    """Print syntax error
    """

    print "Syntax error at token " + p.type
    yacc.errok() # Discard the token and tell the parser it is okay

odl_parser = yacc.yacc()

def OdlParseFile(directory):
    """Parse odl description of model
    """

    f    = open(directory + "/Contents.odl", 'r')
    data = f.read()

    # Replace (apparently meaningless) substring that affects lexing
    data = data.replace("\"\\\r\n    \"", "")

    return odl_parser.parse(data, lexer=odl_lexer)
