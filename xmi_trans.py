from odl_parser  import OdlParseFile
from odl_extract import GetModel, GetClasses, GetSuperClasses, GetAttributes, \
    GetAssociations

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

def PrintClassFooter():
    print "  </packagedElement>"

def PrintClasses(odl_data):
    classes       = GetClasses(odl_data)
    super_classes = GetSuperClasses(odl_data, classes)
    attributes    = GetAttributes(odl_data, classes)

    for ident in classes:
        PrintClassHeader(ident, classes[ident])
        PrintSuperClasses(ident, super_classes)
        PrintAttributes(attributes[ident])
        PrintClassFooter()

def PrintAssociations(odl_data):
    classes      = GetClasses(odl_data)
    associations = GetAssociations(odl_data, classes)

    for ident in associations:
        data = associations[ident]

        print "  <packagedElement xmi:type=\"uml:Association\" " \
            + "xmi:id=\"_" + ident + "\" " \
            + "name=\"A_" + classes[data.owner[0]] + "_" \
                    + classes[data.owner[1]] + "\" " \
            + "memberEnd=\"_" + data.role[0] + " _" + data.role[1] + "\">"

        #print data.name[0]
        #print data.name[1]

        print "  </packagedElement>"

def PrintFooter():
    print "  <packagedElement xmi:type=\"uml:PrimitiveType\" " \
        + "xmi:id=\"_brobQF6WEd-1BtN3LP_f7A\" name=\"DerivedAttribute\"/>"
    print "  <packagedElement xmi:type=\"uml:PrimitiveType\" " \
        + "xmi:id=\"_cD-CwF6WEd-1BtN3LP_f7A\" name=\"Integer\"/>"
    print "</uml:Model>"

def main():
    directory = "model"
    odl_data = OdlParseFile(directory)

    PrintHeader(odl_data)
    PrintClasses(odl_data)
    PrintAssociations(odl_data)
    PrintFooter()

main()
