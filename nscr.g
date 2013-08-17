parser Nscr:
    ignore:             "\\s+"
    # comments
    ignore:             ";.*"

    token END:          "$"  # end of string
    
    token RAWNAME:      "[_a-zA-Z][_a-zA-Z0-9]*"
    token RAWNUM:       "-?[0-9]+"
    
    token RAWSTR:          '("|`)[^\\1]*?\\1'
    token COLOR:        '#[0-9a-fA-F]{6}'

    # Currently text mode doesn't exit even if another ` is encountered.
    # This is against the standard, but it's good enough for me.
    token TXTSTART:     '`'
    token TXT:          '[^@\\\\]+'
    #token TXTSPEC:      '[@\\\\]'

    token SPEC_CMD:     '!s|!d|!w'

    token BOOL_AND:     '&&?'
    token BOOL_CMP:     '>=|<=|==|!=|<>|>|<|='


    rule goal:          stmt END    {{ return stmt }}

    rule stmt:                          {{ return [] }}
                    |   sentence        {{ return sentence }}
                    |   LABEL           {{ return [[LABEL]] }}
                    |   TEXT            {{ return TEXT }}

    rule sentence:      cmd             {{ v = [cmd] }}
                        ( ":" cmd       {{ v.append(cmd) }}
                        |   BREAK_CMD   {{ v.append(BREAK_CMD) }}
                        )*              {{ return v }}

    rule cmd:           NAME args       {{ return [NAME, args] }}
                    |   "!sd"           {{ return ["!sd", []] }}
                    |   SPEC_CMD NUM    {{ return [SPEC_CMD, [NUM]] }}
                    |   BREAK_CMD       {{ return BREAK_CMD }}
                    |   if_stmt         {{ return if_stmt }}
                    |   notif_stmt         {{ return notif_stmt }}

    rule args:                          {{ return [] }}
                    |   arg             {{ v = [arg] }}
                        ( "," arg       {{ v.append(arg) }}
                        )*              {{ return v }}

    rule arg:           NUM             {{ return NUM }}
                    |   NAME            {{ return NAME }}
                    |   STR             {{ return STR }}
                    |   LABEL           {{ return LABEL }}
                    |   COLOR           {{ return COLOR }}

    rule if_stmt:       "if" conditions sentence {{ return ["if", [conditions, sentence]] }}

    rule notif_stmt:    "notif" conditions sentence {{ return ["notif", [conditions, sentence]] }}

    rule conditions:    cond            {{ v = [cond] }}
                        ( BOOL_AND cond {{ [].append(cond) }}
                        )*              {{ return v }}

    rule cond:          NUM             {{ first_num = NUM }}
                        BOOL_CMP
                        NUM             {{ return [BOOL_CMP, first_num, NUM] }}
                    |   "fchk" STR      {{ return ["fchk", STR] }}

    rule LABEL:         "\\*" NAME      {{ return "*"+NAME }}

    rule NAME:          RAWNAME         {{ return RAWNAME.lower() }}

    rule NUM:           RAWNUM          {{ return int(RAWNUM) }}
                    |   NUMVAR          {{ return NUMVAR }}

    rule STR:           RAWSTR          {{ return RAWSTR }}
                    |   STRVAR          {{ return STRVAR }}
    rule TEXT:          TXTSTART        {{ v = [] }}
                        ( TXT           {{ v.append( ["text", [TXT]] ) }}
                        | BREAK_CMD     {{ v.extend( [BREAK_CMD] ) }}
                        )*              {{ return v+[ ["br", []] ] }}

    rule BREAK_CMD:     "@"             {{ return ["click", []] }}
                    |   "\\\\"          {{ return ["EOP", []] }}

    rule NUMVAR:        "%" VARID       {{ return ["%", VARID] }}

    rule STRVAR:        "\\$" VARID     {{ return ["$", VARID] }}

    # Variable identifier
    rule VARID:         NUM             {{ return NUM }}
                    |   NAME            {{ return NAME }}

