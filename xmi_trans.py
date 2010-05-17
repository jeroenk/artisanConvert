from odl_parser         import OdlParseFile
from odl_extract        import OdlExtractMachines

def main():
    directory = "model"
    odl_data = OdlParseFile(directory)
    OdlExtractMachines(odl_data, directory)

main()
