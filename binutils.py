# Swap byte order for little endian machine
def LE(word):
    return ((word&0xff)<<8)|((word>>8)&0xff)

def Bytes(word):
    return ((word>>8)&0xff,word&0xff)

def HexPrint(iterable_value):
    for v in iterable_value:
        print "%x"%v,
    print
