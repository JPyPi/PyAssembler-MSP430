import sys

def prnt(data,word=2,cols=8):
    col=0
    for i,byte in enumerate(data):
        sys.stdout.write("%02x"%byte)
        if (i+1)%2==0:
            sys.stdout.write(" ")
            col+=1
        if col==cols:
            sys.stdout.write("\n")
            col=0
    print "\n-----------\n"
