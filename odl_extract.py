from pyth.plugins.rtf15.reader     import Rtf15Reader
from pyth.plugins.plaintext.writer import PlaintextWriter

class OdlExtractException(Exception):
    pass

class TransitionData:
    def __init__(self):
        self.ident  = None
        self.source = None
        self.target = None
        self.event  = None
        self.action = None
        self.guard  = None

class AssociationData:
    def __init__(self):
        self.owner = [None, None]
        self.upper = [None, None]
        self.lower = [None, None]
        self.name  = [None, None]

class StateData:
    def __init__(self):
        self.vtype       = "uml:State"
        self.name        = None
        self.class_id    = None
        self.substates   = []
        self.is_parallel = False
        self.superstate  = None
        self.state_class = None

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

def GetName(data):
    version = GetVersion(data)
    return version[1][6:]

def GetClasses(odl_data):
    """Yields dictionary from class identifer to class name
    """

    classes = {}

    for ident in odl_data:
        if odl_data[ident][0] == "_Art1_Class":
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
    """Yields a dictionary from class identifier to a list of identifiers
    """

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
        super_classes[ident] = []

        for special_ident in special[ident]:
            super_classes[ident].append(general[special_gen[special_ident]])

    return super_classes

def GetAttributeIds(version, attrib_ids, ident):
    attrib_ids[ident] = []

    for data in version[2]:
        if data[0] == "Relationship" \
                and data[1] == "_Art1_Class_To_Attribute" \
                and data[2] == "_Art1_Attribute":
            attrib_ids[ident].append(data[3])

    return attrib_ids

def GetAttributes(odl_data, classes):
    """Yields dictionary from class identifer to attribute names
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
            attributes[ident].append(names[attrib_id])

    return attributes

def ParseMultiplicity(index, multiplicity, association):
    if multiplicity == "*":
        association.upper[index] = "*"
    elif multiplicity == "1":
        association.upper[index] = "1"
        association.lower[index] = "1"
    elif multiplicity == "0..1":
        association.upper[index] = "1"
        association.lower[index] = "0"
    else:
        raise OdlExtractException("Unknown multiplicity " + multiplicity \
                                      + " found in association")

def GetAssociations(odl_data, classes):
    associations = {}

    for ident in odl_data:
        if odl_data[ident][0] != "_Art1_Association":
            continue

        version = GetVersion(odl_data[ident][1])
        associations[ident] = AssociationData()

        for item in version[2]:
            if item[0] == "Attribute":
                if item[1] == "_Art1_EndMultiplicityUml":
                    ParseMultiplicity(0, item[2][0], associations[ident])
                elif item[1] == "_Art1_StartMultiplicityUml":
                    ParseMultiplicity(1, item[2][0], associations[ident])

        if associations[ident].upper[0] == None:
            associations[ident].upper[0] = "*"

        if associations[ident].upper[1] == None:
            associations[ident].upper[1] = "*"

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

        roles[ident] = (assoc, index)
        associations[assoc].name[index] = name

    for ident in classes:
        version = GetVersion(odl_data[ident][1])

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_Class_To_Role" \
                    and item[2] == "_Art1_Role":
                associations[roles[item[3]][0]].owner[roles[item[3]][1]] = ident

    return associations.values()

def GetStates(odl_data):
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
                    and item[1] =="_Art1_StateType" \
                    and item[2][0] == "0":
                data.vtype = "uml:Pseudostate"
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

    return states

def GetExternal(version, directory):
    external = ""

    for item in version[2]:
        if item[0] == "Attribute" \
                and item[1] == "_Art1_RTF":

            doc = Rtf15Reader.read(open(directory + "/" + item[2][0]))
            external = PlaintextWriter.write(doc).getvalue()
            external = external.replace("\n\n", "\n")

    return external

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

        for item in version[2]:
            if item[0] == "Relationship" \
                    and item[1] == "_Art1_EventActionBlock_To_Transition" \
                    and item[2] == "_Art1_Transition":
                trans_ident = item[3]
            elif item[0] == "Relationship" \
                    and item[1] == "_Art1_EventActionBlock_To_SignalEvent" \
                    and item[2] == "_Art1_Event" \
                    and etype == 0:
                event = "signal/" + GetName(odl_data[item[3]][1])
            elif item[0] == "Relationship" \
                    and item[1] == "_Art1_EventActionBlock_To_ChangeEvent" \
                    and item[2] == "_Art1_ChangeEvent":
                change_version = GetVersion(odl_data[item[3]][1])

                if etype == 2:
                    event = "Time/" + GetExternal(change_version, directory)
                elif etype == 3:
                    event = "Change/" + GetExternal(change_version, directory)

            elif item[0] == "Relationship" \
                    and item[1] == "_Art1_EventActionBlock_To_GuardCondition" \
                    and item[2] == "_Art1_GuardCondition":
                guard_version = GetVersion(odl_data[item[3]][1])
                guard = GetExternal(guard_version, directory)

        if etype == 4:
            event = "Entry/"
        elif etype == 5:
            event = "Exit/"
        elif etype == None:
            event = "None"

        if etype == 0 and trans_ident == ident:
            event = "signal_in/" + event[7:]

        transitions[trans_ident].action = GetExternal(version, directory)
        transitions[trans_ident].event  = event
        transitions[trans_ident].guard  = guard

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
                data.ident  = item[3]
                data.source = ident
                data.target = ident
                transitions[item[3]] = data

    return FillTransitionDetails(odl_data, directory, transitions).values()

def OdlExtractMachines(odl_data, directory):
    classes       = GetClasses(odl_data)
    super_classes = GetSuperClasses(odl_data, classes)
    attributes    = GetAttributes(odl_data, classes)
    associations  = GetAssociations(odl_data, classes)
    states        = GetStates(odl_data)
    transitions   = GetTransitions(odl_data, directory, states)
