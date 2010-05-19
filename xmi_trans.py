from odl_parser  import OdlParseFile
from odl_extract import GetModel, GetClasses, GetSuperClasses, GetAttributes, \
    GetAssociations, GetEvents, GetStates, GetTransitions
from uuid        import uuid4
from cgi         import escape

directory = "model"
signals   = {}
times     = {}
changes   = {}

def GatherSignals(odl_data):
    events = GetEvents(odl_data)

    for event in events:
        signals[event] = (events[event], str(uuid4()))

def GatherTimesAndChanges(odl_data):
    states      = GetStates(odl_data)
    transitions = GetTransitions(odl_data, directory, states)

    for transition in transitions:
        if transition.event[:7] == "Change/":
            changes[transition.ident] = str(uuid4())

        if transition.event[:5] == "Time/":
            times[transition.ident] = str(uuid4())

def PrintHeader(odl_data):
    (ident, name) = GetModel(odl_data)

    print "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    print "<uml:Model xmi:version=\"2.1\" " \
        + "xmlns:xmi=\"http://schema.omg.org/spec/XMI/2.1\" " \
        + "xmlns:uml=\"http://www.eclipse.org/uml2/2.1.0/UML\" " \
        + "xmi:id=\"_" + ident + "\" name=\"" + name + "\">"

def PrintClassHeader(ident, name):
    print "  <packagedElement xmi:type=\"uml:Class\" " \
        + "xmi:id=\"_" + ident + "\" name=\"" + name + "\" isActive=\"true\">"

def PrintSuperClasses(ident, super_classes):
    for general_ident in super_classes[ident]:
        print "    <generalization xmi:id=\"_" + general_ident + "\" " \
            + "general=\"_" + super_classes[ident][general_ident] + "\"/>"

def PrintAttributes(attributes):
    for attribute in attributes:
        if attribute[1][0] == "/":
            type = "_brobQF6WEd-1BtN3LP_f7A"
        else:
            type = "_cD-CwF6WEd-1BtN3LP_f7A"

        print "    <ownedAttribute xmi:id=\"_" + attribute[0] + "\" " \
            + "name=\"" + attribute[1] + "\" " \
            + "type=\"" + type + "\" " \
            + "isUnique=\"false\"/>"

def PrintValues(upper, lower):
    print "      <upperValue xmi:type=\"uml:LiteralUnlimitedNatural\" " \
        + "xmi:id=\"_" + str(uuid4()) + "\" " \
        + "value=\"" + upper + "\"/>"

    if lower == None:
        print "      <lowerValue xmi:type=\"uml:LiteralInteger\" " \
            + "xmi:id=\"_" + str(uuid4()) + "\"/>"
    else:
        print "      <lowerValue xmi:type=\"uml:LiteralInteger\" " \
            + "xmi:id=\"_" + str(uuid4()) + "\" " \
            + "value=\"" + lower + "\"/>"

def PrintAttributeAssociation(ident, data, index):
    print "    <ownedAttribute xmi:id=\"_" + data.role[index] +"\" " \
        + "name=\"" + data.name[index] +"\" " \
        + "type=\"_" + data.owner[index] + "\" " \
        + "isUnique=\"false\" " \
        + "association=\"_" + ident + "\">"
    PrintValues(data.upper[index], data.lower[index])
    print "    </ownedAttribute>"

def PrintAttributeAssociations(ident, associations):
    for association_ident in associations:
        data = associations[association_ident]

        if data.owner[0] == ident and data.name[1] != "":
            PrintAttributeAssociation(association_ident, data, 1)

        if data.owner[1] == ident and data.name[0] != "":
            PrintAttributeAssociation(association_ident, data, 0)

def PrintOwnedReceptions(ident, odl_data):
    states      = GetStates(odl_data)
    transitions = GetTransitions(odl_data, directory, states)

    events = []

    for transition in transitions:
        if states[transition.source].class_id != ident:
            continue

        if transition.event[:7] != "signal/" \
                and transition.event[:10] != "signal_in/":
            continue

        if transition.event_id in events:
            continue

        events.append(transition.event_id)
        print "    <ownedReception xmi:id=\"_" + str(uuid4()) + "\" " \
            + "name=\"Reception_" + str(len(events) - 1) + "\" " \
            + "signal=\"_" + signals[transition.event_id][1] + "\"/>"

def PrintTransition(transition, states, indent, count):
    if transition.event == "Entry/" \
            or transition.event == "Exit/":
        return

    string = indent \
        + "        <transition xmi:id=\"_" + transition.ident + "\" " \
        + "name=\"From_" + states[transition.source].name + "_to_" \
            + states[transition.target].name + "_Transition_" \
            + str(count) + "\" " \
        + "target=\"_" + transition.target + "\" " \
        + "source=\"_" + transition.source + "\""

    if transition.event == "None" \
            and transition.guard == "" \
            and transition.action == "":
        string += "/>"
        print string
        return

    if transition.guard != "":
        string += " guard=\"_" + transition.guard_id + "\""

    if transition.event[:10] == "signal_in/":
        string += " kind=\"internal\""

    string += ">"
    print string

    if transition.event[:5] == "Time/":
        transition.event_id = times[transition.ident]

    if transition.event[:7] == "Change/":
        transition.event_id = changes[transition.ident]

    if transition.event_id != None:
        print indent \
            + "          <trigger xmi:id=\"_" + str(uuid4()) + "\" " \
            + "name=\"Trigger_0\" " \
            + "event=\"_" + transition.event_id + "\"/>"

    if transition.guard != "":
        print indent \
            + "          <ownedRule xmi:id=\"_" + transition.guard_id + "\" " \
            + "name=\"Guard\">"
        print indent \
            + "            <specification xmi:type=\"uml:LiteralString\" " \
            + "xmi:id=\"_" + str(uuid4()) + "\" " \
            + "value=\"" + escape(transition.guard, True) + "\"/>"
        print indent + "          </ownedRule>"

    if transition.action != "":
        print indent \
            + "          <effect xmi:type=\"uml:OpaqueBehavior\" " \
            + "xmi:id=\"_" + str(uuid4()) + "\" " \
            + "name=\"Effect\">"
        print indent + "            <language>xuml</language>"
        print indent \
            + "            <body>" \
            + escape(transition.action, True) \
            + "</body>"
        print indent \
            + "          </effect>"

    print indent + "        </transition>"

def PrintRegion(ident, states, transitions, indent):
    print indent \
        + "        <region xmi:id=\"_" + str(uuid4()) + "\" " \
        + "name=\"" + states[ident].name + "\">"

    for state_ident in states[ident].substates:
        PrintState(state_ident, states, transitions, indent + "  ")

    count = 0

    for transition in transitions:
        if transition.source in states[ident].substates:
            PrintTransition(transition, states, indent + "  ", count)
            count += 1

    print indent + "        </region>"

def PrintSubregions(ident, states, transitions, indent):
    for state_ident in states[ident].substates:
        PrintRegion(state_ident, states, transitions, indent)

def PrintEntryExit(entry_exit, indent):
    if entry_exit == []:
        return

    for transition in entry_exit:
        if transition.event[:6] == "Entry/":
            print indent \
                + "          <entry xmi:type=\"uml:OpaqueBehavior\" " \
                + "xmi:id=\"_" + transition.ident + "\" " \
                + "name=\"Entry\">"
        elif transition.event[:5] == "Exit/":
            print indent \
                + "          <exit xmi:type=\"uml:OpaqueBehavior\" " \
                + "xmi:id=\"_" + transition.ident + "\" " \
                + "name=\"Exit\">"

        print indent + "            <language>xuml</language>"
        print indent + "            <body>" \
            + escape(transition.action, True) + "</body>"

        if transition.event[:6] == "Entry/":
            print indent + "          </entry>"
        elif transition.event[:5] == "Exit/":
            print indent + "          </exit>"

def PrintState(ident, states, transitions, indent):
    entry_exit = []

    for transition in transitions:
        if transition.source != ident:
            continue

        if transition.event[:6] != "Entry/" \
                and transition.event[:5] != "Exit/":
            continue

        entry_exit.append(transition)

    string = indent \
        + "        <subvertex xmi:type=\"" + states[ident].vtype + "\" " \
        + "xmi:id=\"_" + ident + "\" " \
        + "name=\"" + states[ident].name + "\""

    if states[ident].substates == [] and entry_exit == []:
        string += "/>"
        print string
    elif states[ident].substates == [] and entry_exit != []:
        string += ">"
        print string

        PrintEntryExit(entry_exit, indent)

        print indent + "        </subvertex>"
    else:
        string += ">"
        print string

        if states[ident].is_parallel:
            PrintSubregions(ident, states, transitions, indent + "  ")
        else:
            PrintRegion(ident, states, transitions, indent + "  ")

        PrintEntryExit(entry_exit, indent)

        print indent + "        </subvertex>"

def PrintStateMachines(ident, class_name, odl_data):
    states      = GetStates(odl_data)
    transitions = GetTransitions(odl_data, directory, states)

    outer_states = []

    for state_ident in states:
        state = states[state_ident]

        if state.class_id == ident and state.superstate == None:
            outer_states.append(state_ident)

    if outer_states == []:
        return

    print "    <ownedBehavior xmi:type=\"uml:StateMachine\" " \
        + "xmi:id=\"_" + str(uuid4()) + "\" " \
        + "name=\"" + class_name + "\">"
    print "      <region xmi:id=\"_" + str(uuid4()) + "\" " \
        + "name=\"" + class_name + "\">"

    for state_ident in outer_states:
        PrintState(state_ident, states, transitions, "")

    count = 0

    for transition in transitions:
        if transition.source in outer_states:
            PrintTransition(transition, states, "", count)
            count += 1

    print "      </region>"
    print "    </ownedBehavior>"

def PrintClassFooter():
    print "  </packagedElement>"

def PrintClasses(odl_data):
    classes       = GetClasses(odl_data)
    super_classes = GetSuperClasses(odl_data, classes)
    attributes    = GetAttributes(odl_data, classes)
    associations  = GetAssociations(odl_data, classes)

    for ident in classes:
        PrintClassHeader(ident, classes[ident])
        PrintSuperClasses(ident, super_classes)
        PrintAttributes(attributes[ident])
        PrintAttributeAssociations(ident, associations)
        PrintOwnedReceptions(ident, odl_data)
        PrintStateMachines(ident, classes[ident], odl_data)
        PrintClassFooter()

def PrintOwnedEnds(data, ident, classes):
    if data.name[0] == "":
        print "    <ownedEnd xmi:id=\"_" + data.role[0] + "\" " \
            + "name=\"" + classes[data.owner[0]] + "\" " \
            + "type=\"_" + data.owner[0] + "\" " \
            + "isUnique=\"false\" " \
            + "association=\"_" + ident + "\">"
        PrintValues(data.upper[0], data.lower[0])
        print "    </ownedEnd>"

    if data.name[1] == "":
        print "    <ownedEnd xmi:id=\"_" + data.role[1] + "\" " \
            + "name=\"" + classes[data.owner[1]] + "\" " \
            + "type=\"_" + data.owner[1] + "\" " \
            + "isUnique=\"false\" " \
            + "association=\"_" + ident + "\">"
        PrintValues(data.upper[1], data.lower[1])
        print "    </ownedEnd>"

def PrintAssociations(odl_data):
    classes      = GetClasses(odl_data)
    associations = GetAssociations(odl_data, classes)

    for ident in associations:
        data = associations[ident]

        string = "  <packagedElement xmi:type=\"uml:Association\" " \
            + "xmi:id=\"_" + ident + "\" " \
            + "name=\"A_" + classes[data.owner[0]] + "_" \
                    + classes[data.owner[1]] + "\" " \
            + "memberEnd=\"_" + data.role[1] + " _" + data.role[0] + "\""

        if data.name[0] != "" and data.name[1] != "":
            print string + "/>"
        else:
            print string + ">"

        PrintOwnedEnds(data, ident, classes)

        if data.name[0] == "" or data.name[1] == "":
            print "  </packagedElement>"

def PrintSignals(odl_data):
    for signal in signals:
        print "  <packagedElement xmi:type=\"uml:Signal\" " \
            + "xmi:id=\"_" + signals[signal][1] + "\" " \
            + "name=\"" + escape(signals[signal][0], True) + "\"/>"

def PrintSignalEvents():
    count = 0

    for signal in signals:
        print "  <packagedElement xmi:type=\"uml:SignalEvent\" " \
            + "xmi:id=\"_" + signal + "\" " \
            + "name=\"SignalEvent_" + str(count) + "\" " \
            + "signal=\"_" + signals[signal][1] + "\"/>"
        count += 1

def PrintTimeEvents(odl_data):
    states      = GetStates(odl_data)
    transitions = GetTransitions(odl_data, directory, states)

    count = 0

    for transition in transitions:
        if transition.event[:5] != "Time/":
            continue

        print "  <packagedElement xmi:type=\"uml:TimeEvent\" " \
            + "xmi:id=\"_" + times[transition.ident] + "\" " \
            + "name=\"TimeEvent_" + str(count) + "\">"

        print "    <when xmi:type=\"uml:LiteralString\" " \
            + "xmi:id=\"_" + str(uuid4()) + "\" " \
            + "value=\"after( " + transition.event[5:] + " )\"/>"

        print "  </packagedElement>"

        count += 1

def PrintChangeEvents(odl_data):
    states      = GetStates(odl_data)
    transitions = GetTransitions(odl_data, directory, states)

    count = 1

    for transition in transitions:
        if transition.event[:7] != "Change/":
            continue

        print "  <packagedElement xmi:type=\"uml:ChangeEvent\" " \
            + "xmi:id=\"_" + changes[transition.ident] + "\" " \
            + "name=\"ChangeEvent_" + str(count) + "\">"

        print "    <changeExpression xmi:type=\"uml:LiteralString\" " \
            + "xmi:id=\"_" + str(uuid4()) + "\" " \
            + "value=\"" + escape(transition.event[7:], True) + "\"/>"

        print "  </packagedElement>"

        count += 1

def PrintFooter():
    print "  <packagedElement xmi:type=\"uml:PrimitiveType\" " \
        + "xmi:id=\"_brobQF6WEd-1BtN3LP_f7A\" name=\"DerivedAttribute\"/>"
    print "  <packagedElement xmi:type=\"uml:PrimitiveType\" " \
        + "xmi:id=\"_cD-CwF6WEd-1BtN3LP_f7A\" name=\"Integer\"/>"
    print "</uml:Model>"

def main():
    odl_data = OdlParseFile(directory)

    GatherSignals(odl_data)
    GatherTimesAndChanges(odl_data)

    PrintHeader(odl_data)
    PrintClasses(odl_data)
    PrintAssociations(odl_data)
    PrintSignals(odl_data)
    PrintSignalEvents()
    PrintTimeEvents(odl_data)
    PrintChangeEvents(odl_data)
    PrintFooter()

main()
