# Copyright (c) 2011, 2012, Jeroen Ketema, University of Twente
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
#  * Neither the name of the University of Twente nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Odl lexer and parser
"""

from os.path import join
from sys     import stderr
from zipfile import ZipFile

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
    stderr.write("Warning: illegal character '" + t.value[0] \
        + "' in odl file on line " + str(t.lexer.lineno) + "\n")
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

    stderr.write("Warning: syntax error at token " + p.type + "\n")
    yacc.errok() # Discard the token and tell the parser it is okay

odl_parser = yacc.yacc()

def OdlParseFile(source):
    """Parse odl description of model
    """

    contents = "Contents.odl"

    if isinstance(source, ZipFile):
        data = source.open(contents).read()
    else:
        f    = open(join(source, contents), 'rb')
        data = f.read()

    # Replace (apparently meaningless) substring that affects lexing
    data = data.replace("\"\\\r\n    \"", "")

    return odl_parser.parse(data, lexer = odl_lexer)
