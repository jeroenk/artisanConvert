from odl_parser         import OdlParseFile
from odl_extract        import GetModel, GetClasses, GetSuperClasses, \
    GetAttributes

from uuid               import uuid4

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
    classes = super_classes[ident]

    found_new = True

    while found_new:
        found_new = False

        for class_ident in classes:
            new_super_classes = super_classes[class_ident]

            for new_class_ident in new_super_classes:
                if new_class_ident not in classes:
                    classes.append(new_class_ident)
                    found_new = True

    for class_ident in classes:
        print "    <generalization xmi:id=\"_" + str(uuid4()) + "\" " \
            + "general=\"" + class_ident + "\"/>"

def PrintAttributes(attributes):
    for attribute in attributes:
        if attribute[0] == "/":
            type = "_brobQF6WEd-1BtN3LP_f7A"
        else:
            type = "_cD-CwF6WEd-1BtN3LP_f7A"

        print "    <ownedAttribute xmi:id=\"_" + attribute[0] + "\" " \
            + "name=\"" + attribute[1] + "\" " \
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
    PrintFooter()

main()
