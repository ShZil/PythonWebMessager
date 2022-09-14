import os


class FileDict:
    """A dict-like class, but using files to store info, so the data is saved.
    Syntax identical to dictionary, although some features might not work.
    Implemented: `FileDict(path)`, Get/Set: `dict[key]`, `.keys()`, `.values()`, `.items()`, `len(dict)`, `key in dict`, `.clear()`, `key in dict`."""
    # Complete(?) list of implementables can be found here: https://stackoverflow.com/a/23976949
    sep = '~'

    def __init__(self, name):
        os.makedirs('dicts', exist_ok=True)
        self.file = f"dicts\\{name}.txt"
        try:
            open(self.file, "x").close()
        except FileExistsError:
            pass
    
    def __getitem__(self, key):
        try:
            f = open(self.file, 'r', encoding="utf-8")
            lines = f.read().split('\n')
            f.close()
            for line in lines:
                pair = tuple(line.split(FileDict.sep, 1))
                if len(pair) != 2:
                    continue
                if key == pair[0]:
                    return pair[1]
            raise KeyError()
        except (FileNotFoundError, OSError):
            raise

    def __setitem__(self, key, value):
        if FileDict.sep in key:
            raise ValueError("Key cannot contain " + FileDict.sep)
        try:
            _ = self.__getitem__(key)
            update = ""
            with open(self.file, 'r') as f:
                for line in f.readlines():
                    if key == line.split(FileDict.sep)[0]:
                        line = f"{key}{FileDict.sep}{value}\n"
                    update += line
                if not update.endswith('\n'): update += '\n'
            with open(self.file, 'w') as f:
                f.write(update)
        except KeyError:
            with open(self.file, 'a', encoding="utf-8") as f:
                f.write(f"{key}{FileDict.sep}{value}\n")

    def pop(self, key):
        _ = self.__getitem__(key)
        update = ""
        v = None
        with open(self.file, 'r') as f:
            for line in f.readlines():
                key0, value = tuple(line.split(FileDict.sep, 1))
                if key0 == key:
                    line = ""
                    v = value
                update += line
        if not update.endswith('\n'): update += '\n'
        with open(self.file, 'w') as f:
            f.write(update)
        if v is None:
            raise KeyError()
        else:
            return v
    
    def keys(self):
        keys = []
        try:
            f = open(self.file, 'r', encoding="utf-8")
            lines = f.read().split('\n')
            f.close()
            for line in lines:
                pair = tuple(line.split(FileDict.sep, 1))
                if len(pair) != 2:
                    continue
                keys.append(pair[0])
            return keys
        except (FileNotFoundError, OSError):
            raise

    def values(self):
        values = []
        try:
            f = open(self.file, 'r', encoding="utf-8")
            lines = f.read().split('\n')
            f.close()
            for line in lines:
                pair = tuple(line.split(FileDict.sep, 1))
                if len(pair) != 2:
                    continue
                values.append(pair[1])
            return values
        except (FileNotFoundError, OSError):
            raise

    def items(self):
        items = []
        try:
            f = open(self.file, 'r', encoding="utf-8")
            lines = f.read().split('\n')
            f.close()
            for line in lines:
                pair = tuple(line.split(FileDict.sep, 1))
                if len(pair) != 2:
                    continue
                items.append(pair)
            return items
        except (FileNotFoundError, OSError):
            raise
    
    def clear(self):
        open(self.file, 'w').close()

    def __contains__(self, key):
        try:
            _ = self.__getitem__(key)
            return True
        except KeyError:
            return False
    
    def __len__(self):
        return len(self.items())


class HashedFileDict(FileDict):
    def __init__(self, name):
        super().__init__(name)
    
    def __setitem__(self, key, value):
        return super().__setitem__(key, _hashing(value))
    
    def correct(self, key, value) -> bool:
        return self[key] == str(_hashing(value))


def _hashing(value: str) -> int:
    """Returns a simple hash of a `value` in HEX."""
    v = 0
    if len(value) == 0: return v

    for c in value:
        v = ((v << 5) - v) + ord(c)
        v = v & v
    return hex(v)[2:].upper()


__author__ = 'Shaked Dan Zilberman'


if __name__ == '__main__':
    print("This module contains the File Dictionary class I made.")
    print("    - (class) FileDict")
    print("      Implemented: FileDict(name), Get/Set: dict[key], .pop(key), .keys(), .values(), .items(), .clear(), len(dict), key in dict.")
    print("      Saved in ./dicts/{name}.txt")
    print("      If a file already exists there, parse it as a FileDict, so it can be used as a cache.")
    print("    - (class) HashedFileDict : FileDict")
    print("      Implemented: .correct(key, value) -> bool")
    print("      Saves values as hashed versions.")
    print("    - (function) _hashing(value: str) -> int")
