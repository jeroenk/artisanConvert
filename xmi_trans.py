#!/usr/bin/python

from odl.odl_parser  import OdlParseFile
from odl.odl_extract import GetModel, GetClasses, GetSuperClasses, \
    GetAttributes, GetAssociations, GetEvents, GetParameters, GetStates, \
    GetTransitions, FindPackageClasses, GetPackageHierarchy

from cgi     import escape
from uuid    import uuid4
from sys     import argv, stderr

classes       = None
super_classes = None
attributes    = None
associations  = None
parameters    = None
states        = None
transitions   = None

signals = {}
times   = {}
changes = {}

def GatherSignals(odl_data):
    events = GetEvents(odl_data)

    for event in events:
        signals[event] = [events[event], str(uuid4()), False]

def GatherTimesAndChanges():
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
        + "xmi:id=\"_" + ident + "\" name=\"" + escape(name, True) + "\">"

def PrintClassHeader(ident, name):
    print "  <packagedElement xmi:type=\"uml:Class\" " \
        + "xmi:id=\"_" + ident + "\" " \
        + "name=\"" + escape(name, True) + "\" " \
        + "isActive=\"true\">"

def PrintSuperClasses(ident):
    for general_ident in super_classes[ident]:
        print "    <generalization xmi:id=\"_" + general_ident + "\" " \
            + "general=\"_" + super_classes[ident][general_ident] + "\"/>"

def PrintAttributes(class_attributes):
    for attribute in class_attributes:
        if attribute.name[0] == "/":
            attribute_type = "_brobQF6WEd-1BtN3LP_f7A"
        else:
            attribute_type = "_cD-CwF6WEd-1BtN3LP_f7A"

        string = "    <ownedAttribute xmi:id=\"_" + attribute.ident + "\" " \
            + "name=\"" + attribute.name + "\" " \
            + "type=\"" + attribute_type + "\" " \
            + "isUnique=\"false\""

        if attribute.default == None:
            string += "/>"
            print string
            continue

        string += ">"
        print string

        print "      <defaultValue xmi:type=\"uml:OpaqueExpression\" " \
            + "xmi:id=\"_" + str(uuid4()) + "\">"
        print "        <language>xuml</language>"
        print "        <body>" + attribute.default + "</body>"
        print "      </defaultValue>"
        print "    </ownedAttribute>"

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
        + "name=\"" + escape(data.name[index], True) +"\" " \
        + "type=\"_" + data.owner[index] + "\" " \
        + "isUnique=\"false\" " \
        + "association=\"_" + ident + "\">"
    PrintValues(data.upper[index], data.lower[index])
    print "    </ownedAttribute>"

def PrintAttributeAssociations(ident):
    for association_ident in associations:
        data = associations[association_ident]

        if data.owner[0] == ident and data.name[1] != "":
            PrintAttributeAssociation(association_ident, data, 1)

        if data.owner[1] == ident and data.name[0] != "":
            PrintAttributeAssociation(association_ident, data, 0)

def PrintParameters(event_parameters):
    for parameter in event_parameters:
        print "      <ownedParameter xmi:id=\"_" + str(uuid4()) + "\" " \
            + "name=\"" + escape(parameter, True) + "\" " \
            + "type=\"_cD-CwF6WEd-1BtN3LP_f7A\">"
        print "        <upperValue xmi:type=\"uml:LiteralUnlimitedNatural\" " \
            + "xmi:id=\"_" + str(uuid4()) + "\"/>"
        print "        <lowerValue xmi:type=\"uml:LiteralInteger\" " \
            + "xmi:id=\"_" + str(uuid4()) + "\"/>"
        print "        <defaultValue xmi:type=\"uml:LiteralString\" " \
            + "xmi:id=\"" + str(uuid4()) + "\">"
        print "          <value xsi:nil=\"true\"/>"
        print "        </defaultValue>"
        print "      </ownedParameter>"

def PrintOwnedReceptions(ident):
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
        string = "    <ownedReception xmi:id=\"_" + str(uuid4()) + "\" " \
            + "name=\"Reception_" + str(len(events) - 1) + "\" " \
            + "signal=\"_" + signals[transition.event_id][1] + "\""

        signals[transition.event_id][2] = True

        if parameters[transition.event_id] == []:
            string += "/>"
            print string
        else:
            string += ">"
            print string
            PrintParameters(parameters[transition.event_id])
            print "    </ownedReception>"

def PrintTransition(transition, indent, count):
    if transition.event == "Entry/" \
            or transition.event == "Exit/":
        return

    string = indent \
        + "        <transition xmi:id=\"_" + transition.ident + "\" " \
        + "name=\"From_" + escape(states[transition.source].name, True) \
            + "_to_" \
            + escape(states[transition.target].name, True) + "_Transition_" \
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

def PrintRegion(ident, indent):
    print indent \
        + "        <region xmi:id=\"_" + str(uuid4()) + "\" " \
        + "name=\"" + escape(states[ident].name, True) + "\">"

    for state_ident in states[ident].substates:
        PrintState(state_ident, indent + "  ")

    count = 0

    for transition in transitions:
        if transition.source in states[ident].substates:
            PrintTransition(transition, indent + "  ", count)
            count += 1

    print indent + "        </region>"

def PrintSubregions(ident, indent):
    for state_ident in states[ident].substates:
        PrintRegion(state_ident, indent)

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

def PrintState(ident, indent):
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
        + "name=\"" + escape(states[ident].name, True) + "\""

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
            PrintSubregions(ident, indent + "  ")
        else:
            PrintRegion(ident, indent + "  ")

        PrintEntryExit(entry_exit, indent)

        print indent + "        </subvertex>"

def PrintStateMachines(ident, class_name):
    outer_states = []

    for state_ident in states:
        state = states[state_ident]

        if state.class_id == ident and state.superstate == None:
            outer_states.append(state_ident)

    if outer_states == []:
        return

    print "    <ownedBehavior xmi:type=\"uml:StateMachine\" " \
        + "xmi:id=\"_" + str(uuid4()) + "\" " \
        + "name=\"" + escape(class_name, True) + "\">"
    print "      <region xmi:id=\"_" + str(uuid4()) + "\" " \
        + "name=\"" + escape(class_name, True) + "\">"

    for state_ident in outer_states:
        PrintState(state_ident, "")

    count = 0

    for transition in transitions:
        if transition.source in outer_states:
            PrintTransition(transition, "", count)
            count += 1

    print "      </region>"
    print "    </ownedBehavior>"

def PrintClassFooter():
    print "  </packagedElement>"

def PrintClasses():
    for ident in classes:
        PrintClassHeader(ident, classes[ident])
        PrintSuperClasses(ident)
        PrintAttributes(attributes[ident])
        PrintAttributeAssociations(ident)
        PrintOwnedReceptions(ident)
        PrintStateMachines(ident, classes[ident])
        PrintClassFooter()

def PrintOwnedEnds(data, ident):
    if data.name[0] == "":
        print "    <ownedEnd xmi:id=\"_" + data.role[0] + "\" " \
            + "name=\"" + escape(classes[data.owner[0]], True) + "\" " \
            + "type=\"_" + data.owner[0] + "\" " \
            + "isUnique=\"false\" " \
            + "association=\"_" + ident + "\">"
        PrintValues(data.upper[0], data.lower[0])
        print "    </ownedEnd>"

    if data.name[1] == "":
        print "    <ownedEnd xmi:id=\"_" + data.role[1] + "\" " \
            + "name=\"" + escape(classes[data.owner[1]], True) + "\" " \
            + "type=\"_" + data.owner[1] + "\" " \
            + "isUnique=\"false\" " \
            + "association=\"_" + ident + "\">"
        PrintValues(data.upper[1], data.lower[1])
        print "    </ownedEnd>"

def PrintAssociations():
    for ident in associations:
        data = associations[ident]

        string = "  <packagedElement xmi:type=\"uml:Association\" " \
            + "xmi:id=\"_" + ident + "\" " \
            + "name=\"A_" + escape(classes[data.owner[0]], True) + "_" \
                    + escape(classes[data.owner[1]], True) + "\" " \
            + "memberEnd=\"_" + data.role[1] + " _" + data.role[0] + "\""

        if data.name[0] != "" and data.name[1] != "":
            print string + "/>"
        else:
            print string + ">"

        PrintOwnedEnds(data, ident)

        if data.name[0] == "" or data.name[1] == "":
            print "  </packagedElement>"

def PrintSignals():
    for signal in signals:
        if not signals[signal][2]:
            continue

        print "  <packagedElement xmi:type=\"uml:Signal\" " \
            + "xmi:id=\"_" + signals[signal][1] + "\" " \
            + "name=\"" + escape(signals[signal][0], True) + "\"/>"

def PrintSignalEvents():
    count = 0

    for signal in signals:
        if not signals[signal][2]:
            continue

        print "  <packagedElement xmi:type=\"uml:SignalEvent\" " \
            + "xmi:id=\"_" + signal + "\" " \
            + "name=\"SignalEvent_" + str(count) + "\" " \
            + "signal=\"_" + signals[signal][1] + "\"/>"
        count += 1

def PrintTimeEvents():
    count = 0

    for transition in transitions:
        if transition.event[:5] != "Time/":
            continue

        when_id = str(uuid4())

        print "  <packagedElement xmi:type=\"uml:TimeEvent\" " \
            + "xmi:id=\"_" + times[transition.ident] + "\" " \
            + "name=\"TimeEvent_" + str(count) + "\">"

        print "    <when xmi:id=\"_" + when_id + "\">"

        print "      <expr xmi:type=\"uml:LiteralString\" " \
            + "xmi:id=\"_" + when_id +"\" " \
            + "value=\"after( " + transition.event[5:].strip("\n\r") + " )\"/>"

        print "    </when>"

        print "  </packagedElement>"

        count += 1

def PrintChangeEvents():
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

def generate(odl_data, used_classes, directory):
    global classes, super_classes, attributes, associations, parameters, \
        states, transitions

    classes       = GetClasses(odl_data, used_classes)
    super_classes = GetSuperClasses(odl_data, classes)
    attributes    = GetAttributes(odl_data, classes, directory)
    associations  = GetAssociations(odl_data, classes)
    parameters    = GetParameters(odl_data)
    states        = GetStates(odl_data, classes)
    transitions   = GetTransitions(odl_data, directory, states)

    stderr.write("Writing output\n")
    GatherSignals(odl_data)
    GatherTimesAndChanges()

    PrintHeader(odl_data)
    PrintClasses()
    PrintAssociations()
    PrintSignals()
    PrintSignalEvents()
    PrintTimeEvents()
    PrintChangeEvents()
    PrintFooter()
    stderr.write("Done!\n")

def print_packages(packages, name):
    for package in packages:
        print name + package.name

        new_name = name[:] + package.name + "/"
        print_packages(package.children, new_name)

def usage():
    stderr.write("Usage: python <generate|list>" + argv[0] + \
                     " <input directory> " + "[package path]\n")
    exit(1)

def main():
    if len(argv) < 3 or len(argv) > 4:
        usage()

    directory = argv[2]

    stderr.write("Parsing input\n")
    odl_data = OdlParseFile(directory)

    stderr.write("Finding relevant data\n")

    if argv[1] == "list":
        packages = GetPackageHierarchy(odl_data)
        print_packages(packages, "")
    elif argv[1] == "generate":
        if len(argv) == 4:
            used_classes = FindPackageClasses(argv[3], odl_data)
            stderr.write("Using package " + argv[3] + "\n")
        else:
            used_classes = None

        generate(odl_data, used_classes, directory)
    else:
        usage()

main()
