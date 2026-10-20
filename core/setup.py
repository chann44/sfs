
# so we will have a root right
# then each root will have childeren
# so each children either a file or an empty array or a __FILE__ str if 
# first we need a way to construct the path to each file and dir


FILE_IDENTIFIER= "__FILE__"
DIR_EMOJI = "📂"
FILE_EMOJI = "📃"
root = "root"

# CURSOR = "root"



FILE_SYSTEM = {
    "root": {
        "home": [
          {
              "documnet.txt": FILE_IDENTIFIER,
              "dir": [
                  {
                      "hey": FILE_IDENTIFIER,
                      "hello": FILE_IDENTIFIER
                  }
              ]
          }  
        ],
        "usr": [
            {"notes.txt": FILE_IDENTIFIER}
        ]
    }
}

current_file_system = {}

def construct_paths(filesystem:any, indent=0, path=""):
    spacing = " " * indent
    if isinstance(filesystem, dict):

        for key, value in filesystem.items():
            new_path = f"{path}/{key}" if path else key

            if isinstance(value, (dict, list)):
                print(f"{spacing}{DIR_EMOJI} {key}")
                new_path = f"{path}/{key}"
                construct_paths(value, indent=indent+2, path=new_path)
            else:
                print(f"{spacing}{FILE_EMOJI} {key} {value}")
    elif isinstance(filesystem, list):
        for value in filesystem:
            construct_paths(value, indent=indent+2, path=path)
def show_dir(cursor: str, filesystem: any, path=""):
        if isinstance(filesystem, dict):
            for key, value in filesystem.items():
                new_path = f"{path}/{key}" if path else key

                if isinstance(value, (dict, list)):
                    if key == cursor:
                        current_file_system[key] = value # type: ignore
                    new_path = f"{path}/{key}"
                    show_dir(cursor,value, path=new_path)
                    # print(f"{spacing}{FILE_EMOJI} {key} {value}")
        elif isinstance(filesystem, list):
            for value in filesystem:
                show_dir(cursor,value, path=path)


def change_dir(filesystem:any, cursor:str, indent:int=2, path=""):
    spacing = " " * indent
    if isinstance(filesystem, dict):

        for key, value in filesystem.items():
            print(key, value)
            new_path = f"{path}/{key}" if path else key

            if isinstance(value, (dict, list)):
                if key == cursor:
                    print(f"{spacing}{DIR_EMOJI} {key}")
                new_path = f"{path}/{key}"
                change_dir(value, indent=indent+2, path=new_path, cursor=cursor)
                # print(f"{spacing}{FILE_EMOJI} {key} {value}")
    elif isinstance(filesystem, list):
        for value in filesystem:
            change_dir(value, indent=indent+2, path=path, cursor=cursor)


    
            

show_dir(filesystem=FILE_SYSTEM, cursor="home")
construct_paths(current_file_system)

