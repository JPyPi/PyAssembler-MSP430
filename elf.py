# elf.py is intended to be used for outputing object files which can be used by a linker
# http://en.wikipedia.org/wiki/Executable_and_Linkable_Format
# http://docs.oracle.com/cd/E19683-01/817-3677/6mj8mbtc7/index.html
#   The one below isn't too useful
# http://www.scs.stanford.edu/14wi-cs140/pintos/specs/sysv-abi-update.html/ch4.intro.html
# http://www.linuxjournal.com/article/1060

from binutils import *

MAGIC_NUMBER=[0x7f,0x45,0x4c,0x46]
BIT_32=1
BIT_64=2
BIG_END=2
LIT_END=1

INSTRUCTION_ARCH_MSP430=Bytes(LE(0x0069))
TARGET_MSP430=[0x00,0x00,0x00,0x01]
ABI_MSP430=0xff

OBJ_RELOC=1
OBJ_EXEC=2
OBJ_SHARE=3
OBJ_CORE=4

def GenerateHeader(bit_format=BIT_32,endianness=LIT_END,
                   target_abi=0x00,abi_version=0x00,
                   instruction_arch=INSTRUCTION_ARCH_MSP430,
                   target_specific=TARGET_MSP430):
    header_data=MAGIC_NUMBER[:] # Start with a copy of the magic number list
    header_data.append(bit_format)
    header_data.append(endianness)
    header_data.append(1) # "set to 1 for original version of ELF"
    header_data.append(target_abi) 
    header_data.append(abi_version)
    header_data.extend([0x00]*7) # 7 currently unused bytes
    header_data.extend(Bytes(LE(OBJ_RELOC))) # This is a relocatable object file
    header_data.extend(instruction_arch)
    header_data.extend((0x01,0x00,0x00,0x00)) # Set to 1 for original version of elf
    # The following is the process start entry point
    if bit_format==BIT_32:
        header_data.extend([0x00]*4)
    elif bit_format==BIT_64:
        header_data.extend([0x00]*8)
    # The following points to the start of the program header table
    if bit_format==BIT_32:
        header_data.extend([0x00]*4)
    elif bit_format==BIT_64:
        header_data.extend([0x00]*8)
    # The following points to the start of the section header table
    if bit_format==BIT_32:
        header_data.extend([0x00]*4)
    elif bit_format==BIT_64:
        header_data.extend([0x00]*8)
    
    header_data.extend(target_specific)
    header_data.extend(Bytes(LE((bit_format==BIT_32 and 52) or 64))) #Size of this header
    header_data.extend(Bytes(LE())) # Size of a program header table entry
    header_data.extend(Bytes(LE())) # Number of program header table entries
    header_data.extend(Bytes(LE())) # Size of a section header table entry
    header_data.extend(Bytes(LE())) # Number of section header table entries
    header_data.extend(Bytes(LE())) # Index of section header table entry that contains section names
    

SECTION_TYPE_PROGBITS=1
SECTION_TYPE_NOBITS=8
SECTION_TYPE_RELA=4
SECTION_TYPE_STRTAB=3
SECTION_TYPE_SYMTAB=2
SECTION_TYPE_STRTAB=3

FLAG_WRITE    =0b00000000001
FLAG_ALLOC    =0b00000000010
FLAG_EXECUTE  =0b00000000100
FLAG_MERGE    =0b00000001000
FLAG_STRINGS  =0b00000010000
FLAG_INFO     =0b00000100000
FLAG_LINKORDER=0b00001000000
FLAG_GROUP    =0b00010000000
FLAG_TLS      =0b00100000000
FLAG_EXCLUDE  =0b01000000000
FLAG_UNKNOWN  =0b10000000000

class Section:
    def __init__(self):
        pass

