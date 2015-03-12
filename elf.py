from binutils import * 

MAGIC_NUMBER=[0x7f,0x45,0x4c,0x46]
BIT_32=1
BIT_64=2
BIG_END=2
LIT_END=1

INSTRUCTION_ARCH_MSP430=[0x69,0x00]
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
