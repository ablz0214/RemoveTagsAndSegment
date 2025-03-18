# coding:utf-8
def removethink(rep:str)->str:
    if "</think>" in rep:
        nothink = rep.split("</think>")
        return nothink[1].strip()
    elif "<think>" in rep:
        nothink = rep.split("<think>")
        return nothink[1].strip()
    else:
        return rep