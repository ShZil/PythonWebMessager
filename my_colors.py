from settings import COLORS
import os

__author__ = "Shaked Dan Zilberman"

red = str("\u001b[31m")
orange = str("\u001b[31;1m")
yellow = str("\u001b[33m")
green = str("\u001b[32m")
blue = str("\u001b[34m")
magenta = str("\u001b[35m")
cyan = str("\u001b[36m")
gray = str("\u001b[30;1m")
underline = str("\u001b[4m")
bold = str("\u001b[1m")
end = str("\u001b[0m")

def _uncolor() -> None:
    """Disables ANSI coloring."""
    global red, orange, yellow, green, blue, magenta, cyan, gray, underline, bold, end
    red = orange = yellow = green = blue = magenta = cyan = gray = underline = bold = end = str("")

if COLORS:
    os.system('color')
else: 
    _uncolor()


if __name__ == '__main__':
    print("This is a module enabling easy implementation of ANSI colouring.")
    print("\nIf you set COLORS to True,\nand the weird character sequences oddly still appear with everything monochrome,\nrun this:")
    print("(Windows10) In Admin Powershell, use: `Set-ItemProperty HKCU:\Console VirtualTerminalLevel -Type DWORD 1`\n\n")
    print("    - (constant) red: str")
    print("    - (constant) orange: str")
    print("    - (constant) yellow: str")
    print("    - (constant) green: str")
    print("    - (constant) blue: str")
    print("    - (constant) magenta: str")
    print("    - (constant) cyan: str")
    print("    - (constant) gray: str")
    print("    - (constant) underline: str")
    print("    - (constant) bold: str")
    print("    - (constant) end: str")
    print("    - (function) _uncolor() -> None\n                 Automatic execution according to settings.COLORS")
