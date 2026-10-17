
# so we will have a root right
# then each root will have childeren
# so each children either a file or an empty array or a __FILE__ str if 
# first we need a way to construct the path to each file and dir


FILE_IDENTIFIER= "__FILE__"
DIR_EMOJI = "📂"
FILE_EMOJI = "📃"

CURSOR = "root"


FILE_SYSTEM = {
    "root": {
        "home": [
          {
              "documnet.txt": FILE_IDENTIFIER
          }  
        ],
        "usr": [
            {"notes.txt": FILE_IDENTIFIER}
        ]
    }
}

def construct_paths(filesystem:any, indent=0, path=""):
    spacing = " " * indent
    if isinstance(filesystem, dict):

        for key, value in filesystem.items():
            new_path = f"{path}/{key}" if path else key

            if isinstance(value, (dict, list)):
                print(f"{spacing}{DIR_EMOJI} {key}")
                new_path = f"{path}/{key}"
                print(new_path)
                construct_paths(value, indent=indent+2, path=new_path)
            else:
                print(f"{spacing}{FILE_EMOJI} {key} {value}")
                print(new_path)
    elif isinstance(filesystem, list):
        for value in filesystem:
            construct_paths(value, indent=indent+2, path=path)

def show_file(cursor: str, data: any):
    pass


    
            

construct_paths(FILE_SYSTEM)


