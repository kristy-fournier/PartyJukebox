from __future__ import annotations
class VersionNumber:
    def __init__(self,major:int,minor:int,patch:int,extra:str=None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.extra = extra
    
    # From String like "x.y.z-extra" or "x.y.z"
    @staticmethod
    def fromString(verString:str) -> VersionNumber:
        numList = verString.split(".")
        major = int(numList[0])
        minor = int(numList[1])
        finalSplit = numList[2].split("-")
        patch = int(finalSplit[0])
        extra = None
        if len(finalSplit) > 1:
            extra = finalSplit[1]
        if extra.strip() == "":
            # IDK if this is technically a rule of semantic versioning but i dont think x.y.z- should be valid 
            extra = None

        return VersionNumber(major,minor,patch,extra)

    
    def clone(verNumIn:VersionNumber) -> VersionNumber:
        return VersionNumber(verNumIn.major,verNumIn.minor,verNumIn.patch,verNumIn.extra)

    def __str__(self) -> str:
        returnStr = f"{self.major}.{self.minor}.{self.patch}"
        if(self.extra):
            returnStr += f"-{self.extra}"
        return returnStr
        
    def __eq__(self,comp) -> bool:
        if type(comp) == VersionNumber:
            return self.major == comp.major and self.minor == comp.minor and self.patch == comp.patch and self.extra == comp.extra
        elif type(comp) == str:
            return self == VersionNumber.fromString(comp)
        elif type(comp) == type(None):
            return False
        else:
            raise TypeError
        
    def __gt__(self,comp):
        if type(comp) == VersionNumber:
            if(self.major > comp.major):
                return True
            elif(self.major == comp.major and self.minor > comp.minor):
                return True
            elif(self.major == comp.major and self.minor == comp.minor and self.patch > comp.patch):
                return True
            return False
        elif type(comp) == str:
            return self > VersionNumber.fromString(comp)
        else:
            raise TypeError
    
    def __ge__(self,comp):
        return self > comp or self == comp
        
if __name__ == "__main__":
    x = VersionNumber(1,2,4,"alpha")
    y = VersionNumber.fromString("1.2.3-beta")
    z = VersionNumber.clone(x)
    print(x)
    print(y)
    print(z)
    print(f"X == Y: {x==y}")
    print(f"X > Y: {x>y}")
    print(f"Y < X: {y<x}")
    print(f"Z >= Y: {z>=y}")
    print(f"Z <= Y: {z<=y}")
    print(f"Z == X: {z==x}")
