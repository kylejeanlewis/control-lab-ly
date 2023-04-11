__where__ = "Make.Something.Good"                   # Where to register this module to

# ================================================\ Define your plugin classes and functions in this section
class MyClass:
    """This is a summary of my class."""
    @classmethod
    def say(cls, words:str):
        """
        This is a summary of my class method.

        Args:
            words (int): input variable 1
        """
        print(f'Say: {words}')
        return

def my_function():
    """This is a summary of my function."""
    print('Calling my function...')
    return

MY_CONSTANT = 'MY_CONSTANT'
my_variable = 'my_variable'
# ================================================/

from controllably import include_this_module
include_this_module()                               # Registers only the Classes and Functions defined above in this py file