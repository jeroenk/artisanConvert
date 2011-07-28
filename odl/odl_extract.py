from pyth.plugins.rtf15.reader     import Rtf15Reader
from pyth.plugins.plaintext.writer import PlaintextWriter

from os.path  import join
from StringIO import StringIO

class OdlExtractException(Exception):
    pass

class PackageData:
    def __init__(self):
        self.name     = None
        self.ident    = None
        self.is_child = False
        self.child_id = []
        self.children = []

class TransitionData:
    def __init__(self):
        self.ident    = None
        self.source   = None
        self.target   = None
        self.event    = None
        self.event_id = None
        self.action   = None
        self.guard    = None
        self.guard_id = None

class AssociationData:
    def __init__(self):
        self.owner = [None, None]
        self.upper = [None, None]
        self.lower = [None, None]
        self.name  = [None, None]
        self.role  = [None, None]

class StateData:
    def __init__(self):
        self.vtype       = "uml:State"
        self.name        = None
        self.class_id    = None
        self.substates   = []
        self.is_parallel = False
        self.superstate  = None

class AttributeData:
    def __init__(self):
        self.name    = None
        self.ident   = None
        self.default = None

def GetVersion(data):
    version = None

    for data_item in data:
        if data_item[0] == "Version":
            if version == None:
                version = data_item
            else:
                raise OdlExtractException("Multiple versions found for item")

    if version == None:
        raise OdlExtractException("No version data found")
    else:
        return version

def GetId(data):
    for item in data:
        if item[0] == "Attribute" \
                and item[1] == "_Art1_Id":
            return item[2][0]

    raise OdlExtractException("No model identifier found")

def GetModel(odl_data):
    for ident in odl_data:
        if odl_data[ident][0] == "_Art1_Model":
            model_id = GetId(odl_data[ident][1])
            name = ident.replace(' ', '_').replace('-', '_').replace('&', "and")
            return (model_id, name)

    raise OdlExtractException("No model name found")

def GetName(data):
    version = GetVersion(data)
    return version[1][6:].replace(' ', '_') \
        .replace('-', '_').replace('&', "and")

def GetNamePlain(data):
    version = GetVersion(data)
    return version[1][6:]

def GetClasses(odl_data, used_classes):
    """Yields dictionary from class identifer to class name
    """

    classes = {}

    for ident in odl_data:
        if odl_data[ident][0] == "_Art1_Class":
            if ident in classes:
                raise OdlExtractException("Class defined multiple times")

            if used_classes != None and ident not in used_classes:
                continue

            classes[ident] = GetName(odl_data[ident][1])

    return classes

def GetGeneralizations(version, general, ident):
    for data in version[2]:
        if data[0] == "Relationship" \
                and data[1] == "_Art1_Class_To_Generalization" \
                and data[2] == "_Art1_Generalization":
            general[data[3]] = ident

    return general

def GetSpecializations(version, special, ident):
    special[ident] = []

    for data in version[2]:
        if data[0] == "Relationship" \
                and data[1] == "_Art1_Class_To_Specialization" \
                and data[2] == "_Art1_Specialization":
            special[ident].append(data[3])

    return special

def GetSpecialInGeneral(version, special_gen, ident):
    for data in version[2]:
        if data[0] == "Relationship" \
                and data[1] == "_Art1_Generalization_To_Specialization" \
                and data[2] == "_Art1_Specialization":
            special_gen[data[3]] = ident

    return special_gen

def GetSuperClasses(odl_data, classes):
    general = {}
    special = {}

    for ident in classes:
        version = GetVersion(odl_data[ident][1])
        general = GetGeneralizations(version, general, ident)
        special = GetSpecializations(version, special, ident)

    special_gen = {}

    for ident in odl_data:
        if odl_data[ident][0] == "_Art1_Generalization":
            version = GetVersion(odl_data[ident][1])
            special_gen = GetSpecialInGeneral(version, special_gen, ident)

    super_classes = {}

    for ident in special:
        super_classes[ident] = {}

        for special_ident in special[ident]:
            super_classes[ident][special_ident] = \
                general[special_gen[special_ident]]

    return super_classes

def GetAttributeIds(version, attrib_ids, ident):
    attrib_ids[ident] = []

    for data in version[2]:
        if data[0] == "Relationship" \
                and data[1] == "_Art1_Class_To_Attribute" \
                and data[2] == "_Art1_Attribute":
            attrib_ids[ident].append(data[3])

    return attrib_ids

def IsDefaultValue(version):
    for data in version[2]:
        if data[0] == "Attribute" \
                and data[1] == "_Art1_CustomPropertyName" \
                and data[2][0] == "Default Value":
            return True

    return False

def GetDefaultValue(ident, odl_data, directory):
    version = GetVersion(odl_data[ident][1])

    for data in version[2]:
        if data[0] == "Relationship" \
                and data[1] == "_Art1_ModelObject_To_CustomPropertyTextObject" \
                and data[2] == "_Art1_CustomPropertyTextObject":
            custom_version = GetVersion(odl_data[data[3]][1])

            if IsDefaultValue(custom_version):
                return GetExternal(custom_version, odl_data, directory)

    return None

def GetAttributes(odl_data, classes, directory):
    """Yields dictionary from class identifer to attribute data
    """

    attrib_ids = {}

    for ident in classes:
        version    = GetVersion(odl_data[ident][1])
        attrib_ids = GetAttributeIds(version, attrib_ids, ident)

    names = {}

    for ident in odl_data:
        if odl_data[ident][0] == "_Art1_Attribute":
            names[ident] = GetName(odl_data[ident][1])

    attributes = {}

    for ident in attrib_ids:
        attributes[ident] = []

        for attrib_id in attrib_ids[ident]:
            data         = AttributeData()
            data.name    = names[attrib_id]
            data.ident   = attrib_id
            data.default = GetDefaultValue(attrib_id, odl_data, directory)
            attributes[ident].append(data)

    return attributes

def ParseMultiplicity(index, multiplicity, association):
    if multiplicity == "*":
        association.upper[index] = "*"
    elif multiplicity == "1":
        association.upper[index] = "1"
        association.lower[index] = "1"
    elif multiplicity == "2":
        association.upper[index] = "2"
        association.lower[index] = "2"
    elif multiplicity == "0..1":
        association.upper[index] = "1"
        association.lower[index] = "0"
    elif multiplicity == "1..*":
        association.upper[index] = "*"
        association.lower[index] = "1"
    elif multiplicity == "":
        association.upper[index] = "*"
    else:
        raise OdlExtractException("Unknown multiplicity " + multiplicity \
                                      + " found in association")

def GetAssociations(odl_data, classes):
    associations = {}

    for ident in odl_data:
        if odl_data[ident][0] != "_Art1_Association":
            continue

        association = AssociationData()
        version = GetVersion(odl_data[ident][1])

        for item in version[2]:
            if item[0] == "Attribute":
                if item[1] == "_Art1_EndMultiplicityUml":
                    ParseMultiplicity(0, item[2][0], association)
                elif item[1] == "_Art1_StartMultiplicityUml":
                    ParseMultiplicity(1, item[2][0], association)

        if association.upper[0] == None:
            association.upper[0] = "1"
            association.lower[0] = "0"

        if association.upper[1] == None:
            association.upper[1] = "*"

        associations[ident] = association

    roles = {}

    for ident in odl_data:
        if odl_data[ident][0] != "_Art1_Role":
            continue

        version = GetVersion(odl_data[ident][1])
        name    = None
        index   = None
        assoc   = None

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_Role_To_Association" \
                    and item[2] == "_Art1_Association":
                assoc = item[3]
                name  = GetName(odl_data[ident][1])
            elif item[0] == "Attribute" \
                    and item[1] == "_Art1_AssociationEnd":
                index = int(item[2][0])

        if index == None:
            index = 0

        roles[ident] = (assoc, index)
        associations[assoc].name[index] = name
        associations[assoc].role[index] = ident

    for ident in classes:
        version = GetVersion(odl_data[ident][1])

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_Class_To_Role" \
                    and item[2] == "_Art1_Role":
                associations[roles[item[3]][0]].owner[roles[item[3]][1]] = ident

    associations_used = {}

    for ident in associations:
        if associations[ident].owner[0] in classes \
                and associations[ident].owner[1] in classes:
            associations_used[ident] = associations[ident]

    return associations_used

def GetEvents(odl_data):
    events = {}

    for ident in odl_data:
        if odl_data[ident][0] != "_Art1_Event":
            continue

        events[ident] = GetName(odl_data[ident][1])

    return events

def GetParameters(odl_data):
    parameters = {}

    for ident in odl_data:
        if odl_data[ident][0] != "_Art1_Event":
            continue

        version = GetVersion(odl_data[ident][1])
        parameters[ident] = []

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_Event_To_Parameter" \
                    and item[2] == "_Art1_Parameter":
                parameters[ident].append(GetName(odl_data[item[3]][1]))

    return parameters

def GetStates(odl_data, classes):
    states = {}

    for ident in odl_data:
        if odl_data[ident][0] != "_Art1_State":
            continue

        version   = GetVersion(odl_data[ident][1])
        data      = StateData()
        data.name = GetName(odl_data[ident][1])

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_States_To_Class" \
                    and item[2] == "_Art1_Class":
                data.class_id = item[3]
            elif item[0] == "Attribute" \
                    and item[1] =="_Art1_StateType":
                if item[2][0] == "0":
                    data.vtype = "uml:Pseudostate"
                elif item[2][0] == "1":
                    data.vtype = "uml:FinalState"
            elif item[0] == "Relationship" \
                    and item[1] == "_Art1_SuperState_To_SubStates" \
                    and item[2] == "_Art1_State":
                data.substates.append(item[3])

        states[ident] = data

    for ident in states:
        for substate_id in states[ident].substates:
            states[substate_id].superstate = ident

    for ident in states:
        version = GetVersion(odl_data[ident][1])

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_ConcurrentStates_To_CompositeState" \
                    and item[2] == "_Art1_State":
                states[item[3]].substates.append(ident)
                states[item[3]].is_parallel = True
                states[ident].superstate = item[3]

    used_states = {}

    for ident in states:
        if states[ident].class_id in classes:
            used_states[ident] = states[ident]

    return used_states

def GetReplaceData(version, odl_data):
    start = None
    name  = None
    obj   = None

    for data in version[2]:
        if data[0] == "Attribute" \
                and data[1] == "_Art1_TokenStart":
            start = int(data[2][0])
        elif data[0] == "Attribute" \
                and data[1] == "_Art1_LastNameText":
            name = data[2][0]
            name = name[:len(name) - 1]
        elif data[0] == "Relationship" \
                and data[1] == "_Art1_ModelObjectToken_To_ModelObject":
            obj = GetName(odl_data[data[3]][1])

    return (start, name, obj)

def ReplaceTextNames(external, version, odl_data):
    old_external = external
    replacements = {}

    for data in version[2]:
        if data[0] == "Relationship" \
                and data[1] == "_Art1_TextObject_To_ModelObjectToken" \
                and data[2] == "_Art1_ModelObjectToken":
            replace = GetReplaceData(GetVersion(odl_data[data[3]][1]), odl_data)
            replacements[replace[0]] = replace

    i = len(external) - 1

    while i >= 0:
        if i in replacements:
            length = len(replacements[i][1])
            if external[i - 1:i + length - 1] == replacements[i][1]:
                external = external[:i - 1] + replacements[i][2] \
                    + external[i + length - 1:]
            elif external[i:i + length] == replacements[i][1]:
                external = external[:i] + replacements[i][2] \
                    + external[i + length:]
            else:
                raise OdlExtractException("Cannot replace string \"" \
                                              + replacements[i][1] \
                                              + "\" at position " \
                                              + str(i) + " in:\n" \
                                              + old_external)

        i -= 1

    return external

def GetExternal(version, odl_data, directory):
    external = ""

    for item in version[2]:
        if item[0] == "Attribute" \
                and item[1] == "_Art1_RTF":

            if len(item[2]) == 2:
                file_name = join(directory, item[2][0])
                f = open(file_name)
                data = f.read()
                data = data.replace("\x0c", "")
                f.close()
            elif len(item[2]) == 1:
                data = item[2][0]

            if data == "":
                return ""

            f = StringIO()
            f.write(data)
            doc = Rtf15Reader.read(f, clean_paragraphs = False)
            external = PlaintextWriter.write(doc).getvalue()
            external = external.replace("\n\n", "\n")

    return ReplaceTextNames(external, version, odl_data)

def GetType(version):
    for item in version[2]:
        if item[0] == "Attribute" \
                and item[1] == "_Art1_EventType":
            return int(item[2][0])

    return None

def FillTransitionDetails(odl_data, directory, transitions):
    for ident in odl_data:
        if odl_data[ident][0] != "_Art1_EventActionBlock":
            continue

        trans_ident = ident
        version     = GetVersion(odl_data[ident][1])
        etype       = GetType(version)
        event       = None
        event_id    = None

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_EventActionBlock_To_Transition" \
                    and item[2] == "_Art1_Transition":
                trans_ident = item[3]
            elif item[0] == "Relationship" \
                    and item[1] == "_Art1_EventActionBlock_To_SignalEvent" \
                    and item[2] == "_Art1_Event" \
                    and etype == 0:
                event    = "signal/" + GetName(odl_data[item[3]][1])
                event_id = item[3]
            elif item[0] == "Relationship" \
                    and item[1] == "_Art1_EventActionBlock_To_ChangeEvent" \
                    and item[2] == "_Art1_ChangeEvent":
                change_version = GetVersion(odl_data[item[3]][1])

                if etype == 2:
                    event = "Time/" + GetExternal(change_version, odl_data, \
                                                      directory)
                elif etype == 3:
                    event = "Change/" + GetExternal(change_version, odl_data, \
                                                        directory)

            elif item[0] == "Relationship" \
                    and item[1] == "_Art1_EventActionBlock_To_GuardCondition" \
                    and item[2] == "_Art1_GuardCondition":
                guard_version = GetVersion(odl_data[item[3]][1])
                guard    = GetExternal(guard_version, odl_data, directory)
                guard_id = item[3]

        if trans_ident not in transitions:
            continue

        if etype == 4:
            event = "Entry/"
        elif etype == 5:
            event = "Exit/"
        elif etype == None:
            event = "None"
        elif etype == 8: # Apparently also represents the absence of a signal
            event = "None"

        if event == None:
            raise OdlExtractException("Found unknown event type: " + str(etype))

        if etype == 0 and trans_ident == ident:
            event = "signal_in/" + event[7:]

        transitions[trans_ident].action   = GetExternal(version, odl_data, \
                                                            directory)
        transitions[trans_ident].event    = event
        transitions[trans_ident].event_id = event_id
        transitions[trans_ident].guard    = guard
        transitions[trans_ident].guard_id = guard_id

    return transitions

def GetTransitions(odl_data, directory, states):
    transitions = {}

    for ident in odl_data:
        if odl_data[ident][0] != "_Art1_Transition":
            continue

        version    = GetVersion(odl_data[ident][1])
        data       = TransitionData()
        data.ident = ident

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_TransitionEnd_To_EndState" \
                    and item[2] == "_Art1_State":
                data.target = item[3]

        transitions[ident] = data

    for ident in states:
        version = GetVersion(odl_data[ident][1])

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_StartState_To_TransitionStart" \
                    and item[2] == "_Art1_Transition":
                transitions[item[3]].source = ident
            elif item[0] == "Relationship" \
                    and item[1] == "_Art1_State_To_EventActionBlock" \
                    and item[2] == "_Art1_EventActionBlock":
                data = TransitionData()
                data.ident    = item[3]
                data.source   = ident
                data.target   = ident
                transitions[item[3]] = data

    used_transitions = {}

    for ident in transitions:
        if transitions[ident].source != None \
                and transitions[ident].target != None:
            used_transitions[ident] = transitions[ident]

    return FillTransitionDetails(odl_data, directory, used_transitions).values()

def FindSubpackageOf(ident, path, odl_data):
    version = GetVersion(odl_data[ident][1])

    for item in version[2]:
        if item[0] == "Relationship" \
                and item[1] == "_Art1_Package_To_PackageItem" \
                and item[2] == "_Art1_Package" \
                and GetName(odl_data[item[3]][1]) == path[0]:
            if len(path) == 1:
                return item[3]
            else:
                return FindSubpackageOf(item[3], path[1:], odl_data)

    raise Exception("Subpackage " + path[0] + " not found")

def FindPackage(path, odl_data):
    for ident in odl_data:
        if odl_data[ident][0] != "_Art1_Package":
            continue

        if GetName(odl_data[ident][1]) == path[0]:
            if len(path) == 1:
                return ident
            else:
                return FindSubpackageOf(ident, path[1:], odl_data)

    raise Exception("Package " + path[0] + " not found")

def FindAllSubpackages(ident, odl_data):
    version = GetVersion(odl_data[ident][1])

    subpackages = [ident]

    for item in version[2]:
        if item[0] == "Relationship" \
                and item[1] == "_Art1_Package_To_PackageItem" \
                and item[2] == "_Art1_Package":
            subpackages += FindAllSubpackages(item[3], odl_data)

    return subpackages

def FindClassesInPackages(packages, odl_data):
    used_classes = []

    for ident in packages:
        version = GetVersion(odl_data[ident][1])

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_Package_To_PackageItem" \
                    and item[2] == "_Art1_Class":
                used_classes.append(item[3])

    return used_classes

def FindPackageClasses(path, odl_data):
    path_list = path.replace(' ', '_').replace('-', '_').replace('&', "and") \
        .rsplit('/')
    ident     = FindPackage(path_list, odl_data)
    packages  = FindAllSubpackages(ident, odl_data)

    return FindClassesInPackages(packages, odl_data)

def GetPackageHierarchy(odl_data):
    packages = {}

    for ident in odl_data:
        if odl_data[ident][0] != "_Art1_Package":
            continue

        package = PackageData()
        package.name  = GetNamePlain(odl_data[ident][1])
        package.ident = ident

        version = GetVersion(odl_data[ident][1])

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_Package_To_PackageItem" \
                    and item[2] == "_Art1_Package":
                package.child_id.append(item[3])

        packages[ident] = package

    for ident in packages:
        for child_id in packages[ident].child_id:
            if child_id not in packages:
                raise Exception("Subpackage " + child_id + " not_found")

            packages[ident].children.append(packages[child_id])
            packages[child_id].is_child = True

    top_packages = []

    for ident in packages:
        if not packages[ident].is_child:
            top_packages.append(packages[ident])

    return top_packages