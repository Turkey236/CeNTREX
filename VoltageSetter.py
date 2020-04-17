import pyvisa
import time
import numpy as np
import logging

class VoltageSetter:
    def __init__(self, time_offset, resource_name, channels,  voltageset_in, currentset_in = 2, units = 'V'):
        #I think understanding the below line is pretty important
        #I'm going to start messing around with for loops to get a better idea
        self.channels = [str(ch) for enable, ch in zip(channels['enable'], channels['channel']) if enable == '1']
        self.time_offset = time_offset
        self.rm = pyvisa.ResourceManager()
        self.voltageset_in = voltageset_in
        self.voltageset = 0.0
        self.currentset_in = currentset_in
        self.currentset = 2
        try:
            self.instr = self.rm.open_resource(resource_name)

        except pyvisa.errors.VisaIOError as err:
            logging.warning("VoltageSetter connection error: "+str(err))
            self.verification_string = str(False)
            self.instr = False
            return
        self.instr.parity = pyvisa.constants.Parity.none
        self.instr.data_bits = 8
        self.instr.baud_rate = 9600
        self.instr.term_char = '\n'
        self.instr.read_termination = '\r\n'
        self.instr.timeout = 1000

        # make the verification string
        try:
            self.instr.write("SYSTEM:REM")
            self.instr.write("APPLY 0,3")
            self.instr.write("OUTPUT ON")
            self.instr.query("APPLY?")
        except pyvisa.errors.VisaIOError as err:
            logging.warning("VoltageSeter connection error: "+str(err))
            self.verification_string = str(err)
        self.verification_string = str(True)
        
        self.units = units

        #Gonna have to figure this shit out - I want the shape to be constant, which is nice
        # HDF attributes generated when constructor is run
        self.new_attributes = [
                    ('column_names',", "+", ".join(self.channels)),
                    ("units", "s, "+", ".join([units]*len(self.channels)))
                    ]
        # shape and type of the array of returned data
        self.dtype = tuple(['f'] * (len(self.channels)+1))
        self.shape = (len(self.channels)+1, )

    #Probably keep this one
    def __enter__(self):
        return self

    #Now this turns off the voltage, returns the control to local after hitting 'stop control'
    def __exit__(self, *exc):
        if self.instr:
            self.instr.write("APPLY 0,0")
            self.instr.write("OUTPUT OFF")
            self.instr.write("SYSTEM:LOC")
            self.instr.close()

    #I like the concept, check the execution
    def GetWarnings(self):
        return None

    #This is huge
    def ReadValue(self):
        values = [time.time() - self.time_offset]
        for ch in self.channels:
            values.append(self.GetVoltage(ch))
        return values


    #Getting the voltage is key - also gets the current if that channel is checked too
    def GetVoltage(self, ch):
        if ch == "Voltage":
            voltage = float((self.instr.query("APPLY?").split(",")[0]).strip('"'))
        else:
            voltage = float((self.instr.query("APPLY?").split(",")[1]).strip('"'))
        return voltage

    #Also gonna need to be able to set the voltage and current
    
    def VoltageSetControl(self, setvoltage):
        #check for too high a voltage
        self.setvoltage = setvoltage
        if self.setvoltage > 120:
            raise ValueError("Applied Voltage too high.")
        else:
            pass
        #set voltage
        self.instr.write("VOLT " + str(setvoltage))
        
    def CurrentSetControl(self, setcurrent):
        #check for too high a current
        self.setcurrent = setcurrent
        if self.setcurrent > 4:
            raise ValueError("Max Current too high.")
        else:
            pass
        #set current
        self.instr.write("CURR " + str(setcurrent))