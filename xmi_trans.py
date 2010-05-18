from odl_parser  import OdlParseFile
from odl_extract import GetModel, GetClasses, GetSuperClasses, GetAttributes, \
    GetAssociations, GetEvents, GetStates, GetTransitions
from uuid        import uuid4

directory = "model"
signals   = {}

def GatherSignals(odl_data):
    events = GetEvents(odl_data)

    for event in events:
        signals[event] = (events[event], str(uuid4()))

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
            name = attribute[1][1:]
        else:
            type = "_cD-CwF6WEd-1BtN3LP_f7A"
            name = attribute[1]

        print "    <ownedAttribute xmi:id=\"_" + attribute[0] + "\" " \
            + "name=\"" + name + "\" " \
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
        print "    <ownedReception xmi:id=\"_" + transition.event_id + "\" " \
            + "name=\"Reception_" + str(len(events) - 1) + "\" " \
            + "signal=\"_" + signals[transition.event_id][1] + "\"/>"

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
            + "name=\"" + signals[signal][0] + "\"/>"

def PrintSignalEvents():
    count = 0

    for signal in signals:
        print "  <packagedElement xmi:type=\"uml:SignalEvent\" " \
            + "xmi:id=\"_" + signal + "\" " \
            + "name=\"SignalEvent_" + str(count) + "\" " \
            + "signal=\"_" + signals[signal][1] + "\"/>"
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

    PrintHeader(odl_data)
    PrintClasses(odl_data)
    PrintAssociations(odl_data)
    PrintSignals(odl_data)
    PrintSignalEvents()
    PrintFooter()

main()
