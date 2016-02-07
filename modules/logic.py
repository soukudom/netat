#!/usr/vin/env python3

import getpass
import sys
import os
import modules.factory as factory
import importlib
import modules.connect as connect

class Orchestrate:    
    def __init__(self, deviceFile, configFile, settingsFile ):

        self.deviceFile = deviceFile #nazev konfiguracniho souboru pro zarizeni
        self.configFile = configFile #nazev konfiguracniho souboru pro nastaveni
        self.settingsFile = settingsFile #nazev konfiguracniho souboru pro globalni parametry
        self.factory = factory.Factory() # vytvoreni objektu tovarny
        self.configuration = {} # slovnik obsahujici konfiguraci, ktera se bude volat

        self.globalSettings = self.factory.getSettingsProcessing(self.settingsFile) #vytvoreni objektu pro parsovani globalniho nastaveni
        self.globalSettings.parse("")
        
        #ulozeni nazvu konfiguranich souboru; prednost maji prepinace pred konfiguracnim souborem
        if not self.configFile: 
            try:
                self.configFile = globalSetting.settingsData[config_file]
            except KeyError as e:
                print("Config file has not been inserted")
                sys.exit(1)

        if not self.deviceFile:
            try:
                self.deviceFile = globalSetting.settingsData[device_file]
            except KeyError as e:
                print("Config file has not been inserted")
                sys.exit(1)
        
        #username = input("Type your username:") #username pro prihlaseni na zarizeni
        #password = getpass.getpass("Type your password:") #password pro prihlaseni
        #self.credentials = [username,password]
        self.setCredentials()
        
        
        self.device = self.factory.getDeviceProcessing(self.deviceFile) #vytvoreni objektu pro parsovani konfiguracniho souboru zarizeni
        self.config = self.factory.getConfigProcessing(self.configFile) #vytvoreni objektu pro parsovani konfiguracniho souboru pro nastaveni

    def setCredentials(self):
        username = input("Type your username:") #username pro prihlaseni na zarizeni
        password = getpass.getpass("Type your password:") #password pro prihlaseni
        self.credentials = [username,password]
        
    def buildConfiguration(self):
        
        methods = self.config.parse("") # parsovani konfiguraniho souboru

        for method in methods:
           # print("metoda k nastaveni:",method)
            hosts = self.device.parse(method[0]) # zjisti zarizeni, ktere se budou nastavovat         
            #print("zarizeni k nastaveni",hosts)
            for vendor in hosts: # zjisti nazev zarizeni, ktery je potrebny pro dynamickou praci
             #   print("vendor je ", vendor)
                for host in hosts[vendor]:
                    manufactor = self.device.getManufactor(host,self.globalSettings.settingsData["community_string"],vendor)
                    #pokud snmp neziskal data tak se pokracuje dal
                    if manufactor == None:
                        print("Getting manufactor name of '{}' no success".format(host))
                        option = input("Would you like to continue? [Y/n]")
                        if option == "Y":
                            continue
                        else:
                            print("Closing netat configuration")
                            sys.exit(1)
                        
                    #podarilo se ziskat vyrobce, uklada se do slovniku    
                    manufactor.append(host)
                    manufactor = tuple(manufactor)
                    try:
                        self.configuration[manufactor].append(method)
                    except:
                        self.configuration[manufactor] = [method]

              #      print("vyrobce:",manufactor)
                    continue
## >>>>>>>>>>>>>>>>>

    def doConfiguration(self):
        for dev in self.configuration:
            #sestaveni modulu pro import
            module = "device_modules.{}.{}".format(dev[0],dev[1])
            importObj = importlib.import_module(module)
            obj = getattr(importObj,"DefaultConnection") #!!! osetrit pokud trida DefaultConnection nebude existovat  
            objInst = obj()
            conn_method = objInst.method
            
            #pripoj se na zarizeni
            conn = getattr(connect, conn_method)            
            conn = conn()
            #conn._connect(dev[2],self.username,self.password)
            while True:
                try:
                    conn.connect(dev[2],self.credentials)
                    break;
                except Exception as e:
                    print(e)
                    option = input("Would you like to try it again?[Y/n]")
                    if option == "Y":
                        self.setCredentials()
                        continue
                    else:
                        print("Closing netat configuration")
                        sys.exit(1)
                                                                
            print("nastavuju device", dev)
            for method in self.configuration[dev]:
                print("vstupni method je",method)
                #zavolani tridy
                obj = getattr(importObj,method[1])
                objInst = obj()

                #zjisteni protokolu spojeni
                conn_method = objInst.method
    
                #pokud se nastavuje submethod
                if method[3]:
                    inst = getattr(objInst,method[3])
                    deviceSet = inst(**method[-1])
                #pouze method
                else:
                    #print("volam method",method[2])
                    #inst = getattr(objInst,method[2])
                    inst = getattr(objInst,method[2].strip())
                    #print("volam instanci", method[-1])
                    deviceSet = inst(**method[-1])

                #zavolani propojovaciho module a vykonani prikazu
                #conn = getattr(connect, conn_method)
                #conn = conn()
                #conn._connect(dev[2],self.username,self.password)
           #     print("nastav", deviceSet)
                conn.doCommand(deviceSet)
            conn.disconnect()

                    #sestaveni modulu pro import
#                    module = "device_modules.{}.{}".format(manufactor[0],manufactor[1])
#                    importObj = importlib.import_module(module)
#                    #zavolani tridy
#                    obj = getattr(importObj,method[1])
#                    objInst = obj() #do objektu pridat atribut check, kterej bude kontrovat zda byla proveda kontrolna na pritomnost prikazu nebo ne

                  
                    #zjisteni metody spojeni
#                    conn_method = objInst.method
#                    #pokud se nastavuje submethod
#                    if method[3]:
#                        inst = getattr(objInst,method[3])
#                        deviceSet = inst(**method[-1])
#                    #pouze method
#                    else:
#                        inst = getattr(objInst,method[2])
#                        deviceSet = inst(**method[-1])
#                    
#                    #zavolani propojovaciho modulue a vykonani prikazu
#                    conn = getattr(connect, conn_method)                     
#
#
#                    conn = conn()
#                    conn._connect(host,self.username,self.password)
#                    conn._execCmd(deviceSet)

########-----------END------------------------------------------------------------------------------

#                    #dynamicke vytvoreni skriptu pro nastaveni
#                    try:
#                        with open(manufactor[1]+".py", encoding="utf-8", mode="w") as f:
#                            print("#!/usr/bin/env python3", file=f)
#                            print("import device_modules.{}.{} as {}".format(manufactor[0],manufactor[1],manufactor[1]), file=f) 
#                            
#                            #vytvoreni objektu tridy
#                            print("{} = {}.{}()".format(instance,manufactor[1],method[1]),file=f)
#                            #pokud je definovana submethod
#                            if method[3]:
#                                print("{} = {}.{}(**{})".format(returned,instacen,method[3],method[-1]),file=f)
#                            #pokud je definovano prouze method
#                            else:
#                                print("{} = {}.{}(**{})".format(returned,instance,method[2],method[-1]),file=f)
#                            #vrati vysledek operace
#                            print("print({},{}.method)".format(returned,instance),file=f)
#                            
#                    except Exception as e:
#                        print(e)
#                    #zavolani pomocneho souboru    
#                    p = subprocess.Popen(["python3", manufactor[1]+".py"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
#                    output, error = p.communicate()
#                    
#                    #print("ot:", output)
#                    deviceSet = output.decode("utf-8").rsplit(" ",1)
#                    deviceSet[0] = deviceSet[0].strip("][").split(",")
#                    if deviceSet[1].strip() == "ssh":
#                        conn = connect.ssh()
#                        conn._connect(host,self.username, self.password)
#                        conn._execCmd(deviceSet[0])
                                

        #name =  parseDevice(self.deviceFile)._getManufactor("10.10.110.232") 
        #print(name)

        #par = parseSettings(settingsFile)
        #par._parse()
        #print(par.network,par.networkMask,par.community,par.deviceFile,par.configFile)
        
        #obj = ssh("10.10.110.230",self.username,self.password)    
        #obj._execCmd("show run")

    # vhodne zde paralelizovat / advance
