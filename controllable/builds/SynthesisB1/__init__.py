from collections import namedtuple

def create_named_tuple(func):
    def wrapper():
        setup_dict = func()
        field_list = []
        object_list = []
        for k,v in setup_dict.items():
            field_list.append(k)
            object_list.append(v)
        
        Setup = namedtuple('Setup', field_list)
        print(f"Objects created: {', '.join(field_list)}")
        return Setup(*object_list)
    return wrapper