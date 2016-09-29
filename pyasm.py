import re
import prettyhex
from binutils import * # This imports LE and bytes

# Regex for stripping comments out
comment_patt=re.compile(";.*")

sample="""
;subc.b  @r4+,   r2
;mov #llo(-32204), r15
main:
mov r1, r4
add #2, r4
    mov #23168, &__WDTCTL
    mov.b   &__CALBC1_1MHZ, r15
    mov.b   r15, &__BCSCTL1
    mov.b   &__CALDCO_1MHZ, r15
    mov.b   r15, &__DCOCTL
    mov.b   #1, &__P1DIR
    mov.b   #1, &__P1OUT
.L3:
    mov.b   &__P1OUT, r15
    xor.b   #1, r15
    mov.b   r15, &__P1OUT
    mov #llo(-32204), r15
.L2:
    dec r15
    cmp #0, r15
    jne .L2
    nop
    nop
    jmp .L3"""


header = [0x7f,0x45,0x4c,0x46,0x01,0x01,0x01,0xff,
          0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
          0x02,0x00,0x69,0x00,0x01,0x00,0x00,0x00,
          0x00,0xc0,0x00,0x00,0x34,0x00,0x00,0x00]
header="".join(map(chr,header))

# useful:
# /Applications/Energia.app/Contents/Resources/Java/hardware/tools/msp430/msp430/lib/ldscripts/msp430g2553
# the above location (in periph.x contains the values to be used for things such as&_P1DIR)
f=open("/Applications/Energia.app/Contents/Resources/Java/hardware/tools/msp430/msp430/lib/ldscripts/msp430g2553/periph.x")
data=f.read()
f.close()
mem_locs=filter(lambda x:len(x)==2,map(lambda x:x.strip("\n ").replace(" ","").split("="),data.split(";")))
for i,variable in enumerate(mem_locs):
    if variable[1].startswith("0x"):
        mem_locs[i][1]=int(variable[1],16)
    else:
        mem_locs[i][1]=int(variable[1])

mem_locs=dict(mem_locs)


def translateEmulated(program):
    program = program.replace("ret","mov @r1+,r0")
    program = re.sub("tst (r[0-9]{1,2})",r"cmp #0, \1",program)
    program = re.sub(r"dec((?:\.b)?)[ ]+(r[0-9]{1,2})",r"sub\1 #1, \2",program)
    program = re.sub(r"#llo\((-?[0-9]+)\)",r"#\1",program)
    return program


# These are the 29 core instructions
op_code_map={'mov' :0x4,
             'add' :0x5,
             'addc':0x6,
             'subc':0x7,
             'sub' :0x8,
             'cmp' :0x9,
             'dadd':0xA,
             'bit' :0xB,
             'bic' :0xC,
             'bis' :0xD,
             'xor' :0xE,
             'and' :0xF,  #End doub op
             'rrc' :0x1,
             'swpb':0x104,
             'rra' :0x11,
             'sxt' :0x118,
             'push':0x12,
             'call':0x128,
             'reti':0x13, #end sing op
             'jne' :0x20,
             'jnz' :0x20,
             'jeq' :0x24,
             'jz'  :0x24,
             'jnc' :0x28,
             'jc'  :0x2C,
             'jn'  :0x30,
             'jge' :0x34,
             'jl'  :0x38,
             'jmp' :0x3C}

def isSingleOp(opname):
    return opname in ('rrc','rra','push','swpb','call','reti','sxt')

def isJump(opname):
    return opname.startswith("j")


class Instruction:
    def __init__(self,label="",opcode="",operands=[],byte_op=0):
        self.label=label
        self.opcode=opcode
        self.operands=operands
        # byte_op 0 means that this is a word opperation
        self.byte_op=byte_op


def ParseLine(line):
    # Initialize an instruction object
    ins = Instruction()

    line=line.strip("\n\t ").split(":",1)
    if len(line)==2:
       ins.label=line.pop(0)
    line=line[-1].split(" ",1)
    opcode=line[0].split(".")
    ins.opcode=opcode[0]
    if len(opcode)==2 and opcode[1]=="b": ins.byte_op=1
    ins.operands=map(lambda x:x.strip("\t "),line[-1].split(","))

    return ins


def CompileOp(instruction,labels,current_bin_size):
    is_single=is_jump=False
    data=[0]

    if instruction.opcode=="nop":
        return Bytes(LE(0x4303))

    # Assign data[0] to be the opcode then shift acording to instruction type
    data[0] = op_code_map[instruction.opcode]
    if isSingleOp(instruction.opcode):
        data[0] <<= 7
        is_single=True
    elif isJump(instruction.opcode):
        data[0] <<= 8
        is_jump=True
        # useful: 0x3ff # 10 pc offset jump mask
    else:
        data[0] <<= 12

    # The byte vs word bit is always in position 6. (thankfully! whew :) (and N/A to jumps)
    data[0] |= instruction.byte_op << 6

    for i,arg in enumerate(instruction.operands):
        if arg.startswith("r"):
            # No need to set addressing modes because "register" is default
            if i==0:
                data[0]|=int(arg[1:]) << 8
            if i==1:
                data[0]|=int(arg[1:])
        elif arg.startswith("#") and i==0: # This is only valid for source operand
            # Handle decimal literals (including constant generation)

            value=int(arg.lstrip("#")) & 0xffff
            if value in (4,8):
                                             # 4,8 are in r2 with 1 and 11
                data[0] |= 2<<8              # register 2 as source
                data[0] |= ((value==5 and 0b10) or (value==8 and 0b11)) << 4
            elif value in (0,1,-1,2):
                                             # 0,1,2,-1 are in r3 with 00,01,10,11
                data[0] |= 3<<8              # register 3 as source
                data[0] |= (value&0b11) << 4 # use the correct source addressing mode
            else:
                data[0] |= 0b11 << 4  # 11 means immediate mode for souce
                data.append(int(arg.lstrip("#"))&0xffff)
        elif arg.startswith("&"):
            if i==0:
                data[0] |= 0b01 << 4 # Set source addressing mode
                data[0] |= 2 << 8    # use r2 as dest to say absolute for dest
            if i==1:
                data[0] |= 1 << 7    # Set destination addressing mode bit
                data[0] |= 2         # Use r2 as the source to say absoulte for source
            data.append(mem_locs[arg[1:]])
        elif arg.startswith("@"):
            if arg.endswith("+"):
                data[0] |= 0b11 << 4 # indirect mode then auto increment
            else:
                data[0] |= 0b10 << 4 # 10 means indirect mode for source
            data[0] |= int(arg[2:].rstrip("+"))<<8
        elif arg.find("(") and arg.endswith(")"):
            arg=arg.rstrip(")").split("(")
            # Add a word of data after the instruction
            data.append(int(arg[0])&0xffff)
            # Set source register to the one in parenthesis
            data[0] |= int(arg[1][1:]) << 8
            # Set addressing mode
            data[0] |= 0b01 << 4
        else:
            if is_jump:
                if instruction.opcode=="jmp":
                    data[0] |= (((labels[arg]-current_bin_size)/2)&0x3ff) - 1
                else:
                    data[0] |= ((labels[arg]-current_bin_size)&0x3ff) + 1
                    # 10 pc offset jump mask (need to +1 because 2's
                    # complement doesn't working right

    # Convert all bytes to little endian style
    data=map(LE,data)
    HexPrint(data)
    bytes_data=[]
    for word in data:
        bytes_data.extend(Bytes(word))
    return bytes_data


def Compile(asm_data):
    output=[]
    labels={}
    asm_data=comment_patt.sub("",asm_data)
    asm_data=translateEmulated(asm_data)
    for line in asm_data.split("\n"):
        if line.strip():
            result=ParseLine(line)
            print result.opcode,result.byte_op,result.operands
            if not result: continue
            if result.label:
                labels[result.label]=len(output)
            # Only parse if there's an instruction and it's not just a label
            if result.opcode:
                output.extend(CompileOp(result,labels,len(output)))
                prettyhex.prnt(output)


if __name__=="__main__":
    print "running..."
    print sample
    #compile("addc.b @r5+,r7")
    #compile("mov.b  17484(r9),r5")
    #compile("cmp    #0, r15")
    Compile(sample)
    #Compile("subc.b  @r4+,   r2  ")
