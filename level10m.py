#!/usr/bin/python3
# -*- coding: utf-8 -*-
#usb.device_address
import usb.core, usb.util, time

ACTIVE_DPI_LEVEL = 0x00
DPI_X = 0x01
DPI_Y = 0x06

GEN_LIFTOFF = 0x8E


BTN_LEFT = 0x0E
BTN_RIGHT = 0x0F
BTN_SCROLL = 0x10
BTN_LEFT_DOWN = 0x11
BTN_LEFT_UP = 0x12
BTN_3D_SX = 0x13
BTN_3D_DX = 0x14
BTN_RIGHT_DOWN = 0x15
BTN_RIGHT_UP = 0x16
BTN_3D_UP = 0x17
BTN_3D_DOWN = 0x18

colors = [
    "Rosso",
    "Verde",
    "Giallo",
    "Blu",
    "Magenta",
    "Azzurro",
    "Verde Acqua",
]

predef_assign = [
    [[0x01,0x01,0x00,0x00,0x00], "Left click"],
    [[0x01,0x02,0x00,0x00,0x00], "Right click"],
    [[0x01,0x04,0x00,0x00,0x00], "Scroll"],
    [[0x01,0x08,0x00,0x00,0x00], "Back"],
    [[0x01,0x10,0x00,0x00,0x00], "Forward"],

    [[0x02,0x01,0x00,0x00,0x00], "Ctrl"],
    [[0x02,0x02,0x00,0x00,0x00], "Shift"],
    [[0x02,0x04,0x00,0x00,0x00], "Alt"],

    [[0x49,0x00,0x00,0x00,0x00], "OFF"],
    [[0x09,0x00,0x00,0x00,0x00], "Dpi Up"],
    [[0x0A,0x00,0x00,0x00,0x00], "Dpi Down"],
    [[0x11,0x00,0x00,0x00,0x00], "Dpi Cycle Up"],
    [[0x12,0x00,0x00,0x00,0x00], "Dpi Cycle Down"],
    [[0x06,0x00,0x00,0x00,0x00], "Macro"],
    [[0x0F,0x00,0x00,0x00,0x00], "Execute"],
    [[0x04,0x01,0x02,0x06,0x02], "Double Click"],
    [[0x13,0x00,0x00,0x00,0x00], "Next Profile"],
    [[],"Unknow"]
]


class level10_usb():
    dev = 0
    # profile_active = 0
    # active_dpi_level = 0
    reattach = False
    commandQueue = []

    def __init__(self):
        self.dev = usb.core.find(idVendor=0x12cf, idProduct=0x0219)
        if self.dev is None:
            raise ValueError('Device not found')

    def open(self):
        if self.dev.is_kernel_driver_active(0):
            self.dev.detach_kernel_driver(0)
            self.reattach = True

    def close(self):
        if self.reattach:
            self.reattach = False
            usb.util.dispose_resources(self.dev)
            self.dev.attach_kernel_driver(0)

    '''
    TOD: write somenthing here. Add the ending "O"
    '''
    def get_profile_bank(self, profile, address):
        bank = 0x01
        offset = profile
        if profile > 2:
            bank = 0x02
            offset = profile - 3
        final_address = address + (80 * offset)
        return (final_address, bank)

    '''
    get_data(0x01, profile=1)
    get_data(0x01, bank=0x00)
    '''
    def get_data(self, address, profile=None, bank=None):
        if bank is not None and profile is not None:
            return "FUCK YOU"

        if profile is not None:
            address, bank = list(self.get_profile_bank(profile, address))


        msg = [0xDF, address, 0x00, bank, 0x00, 0x00, 0x08, 0x00]
        self.dev.ctrl_transfer(0x21, 0x9, 0x300, 0x0, msg)

        value = self.dev.ctrl_transfer(0xa1, 0x1, 0x300, 0x0, 0x8)
        return value[1]

    '''
    put_data(0x01, value, profile=1)
    put_data(0x01, value, bank=0x00)
    '''
    def put_data(self, address, value, profile=None, bank=None, reset=True):
        if profile is not None:
            address, bank = list(self.get_profile_bank(profile, address))

        msg = [0xDE, address, value, bank, 0x00, 0x00, 0x08, 0x00]
        self.commandQueue.append(msg)


    def commitChanges(self):
        print("Do queue")
        if self.commandQueue:
            print("open")
            self.open()
            for command in self.commandQueue:
                print(str(command))
                self.dev.ctrl_transfer(0x21, 0x9, 0x300, 0x0, command)
                time.sleep(.3)
            self.send_reset()
            del self.commandQueue[:]
            print("close")
            self.close()

    def send_command(self, x1, x2, x3):
        msg = [0xC4, x1, x2, x3, 0x00, 0x00, 0x08, 0x00]
        self.dev.ctrl_transfer(0x21, 0x9, 0x300, 0x0, msg)


    def send_reset(self):
        self.send_command(0x00,0x00,0x00)

    '''
    Return the active mouse profile
    '''
    def get_active_profile(self):
        value = self.get_data(0x8C, bank=0x00)
        value = value - 0x50
        return value

    def set_active_profile(self, profile):
        if 0 >= profile <= 4:
            value = profile + 0x50
            self.put_data(0x8C, value, bank=0x00, reset=False)
            self.send_command(0x07, profile, 0x00)

    '''
    Return the dpi level for the selected profile
    This data also contain the polling rate
    Dpi level start from 0
    Indexed Polling rate, from 0 to 3 (125, 250, 500, 1000)
    Human readable pollign rate (125, 250, 500, 1000)
    '''
    def get_active_dpi_level(self, profile):
        value = self.get_data(ACTIVE_DPI_LEVEL, profile=profile)
        polling_rate = value-128>>3
        dpi_level = value - 128 - 8 * polling_rate
        polling_rate_human = 125*pow(2, 3-polling_rate)

        return [dpi_level, polling_rate, polling_rate_human]

    '''
    Set the active dpi level for the selected profile
    This also set the usb polling rate
    level start from 0 and end to 4
    '''
    def set_active_dpi_level(self, profile, level):
        if 0 >= profile <= 4 and 0 >= level <= 4:
            polling_rate = 0
            level = 0
            value = (128 + level) + (polling_rate *8)
            self.set_profile_data(ACTIVE_DPI_LEVEL, profile, value)
            self.put_data(ACTIVE_DPI_LEVEL, value, profile=profile)

    '''
    Return [x,y] dpi level scale
    level from 0 to 4
    '''
    def get_dpi_value(self, profile, level):
        x_address = DPI_X + level
        y_address = DPI_Y + level

        x_value = self.get_data(x_address, profile=profile)
        y_value = self.get_data(y_address, profile=profile)

        return [x_value, y_value]

    def set_dpi_value(self, profile, level, x, y):
        if 0 <= profile <= 4 and 0 <= level <= 3 and 1 <= x <= 164 and 1 <= y <= 164:
            x_address = DPI_X + level
            y_address = DPI_Y + level

            self.put_data(x_address, x, profile=profile)
            self.put_data(y_address, y, profile=profile)

    '''
    Return the active lift off
    from 0 to 30
    '''
    def get_liftoff(self):
        value = self.get_data(GEN_LIFTOFF, bank=0x00)
        value = value - 33
        return value

    def set_liftoff(self,value):
        if 0 >= value <= 30:
            value = value + 33
            self.put_data(GEN_LIFTOFF, value, bank=0x00)

    def get_button_assign(self, profile=2, button=BTN_LEFT_UP):
        # To find the first "alt" address for the button
        # 0x19 is the start of "alt" function map
        data = []
        data.append(self.get_data(button, profile=profile))

        base_alt = 0x19 + 4* (button - BTN_LEFT)
        alt1_address, bank = list(self.get_profile_bank(profile, base_alt))

        for x in range(alt1_address, alt1_address + 4):
            data.append(self.get_data(x, bank=bank))


        for index, x in enumerate(predef_assign):
            if (x[0] == data):
                return index

        return len(predef_assign)

    def set_button(self, profile=1, buttonIndex=BTN_LEFT_UP, values=[15,0x00,0x00,0x00,0x00]):
        base_alt = 0x19 + 4* (buttonIndex - BTN_LEFT)
        button_address, bank = self.get_profile_bank(profile, buttonIndex)
        alt1_address, bank = list(self.get_profile_bank(profile, base_alt))
        self.put_data(button_address, values[0], bank=bank)

        for idx, address in enumerate(range(alt1_address, alt1_address + 4), 1):
            self.put_data(address, values[idx], bank=bank)

    def get_macro(self, profile=1, button=BTN_LEFT_UP):
        macro_len_address = 4*(button - BTN_LEFT)+44*profile
        macro_len = self.get_data(macro_len_address, bank=0x03)

        macro_bank = 4 + (button - BTN_LEFT) + (11 * profile)

        for idx in range(0x00, macro_len):
            val = self.get_data(idx, bank=macro_bank)

    # DELETE THIS
    def get_lights(self, profile=2):
        sx = self.get_data(0x0C, profile=profile)
        scroll = self.get_data(0x0D, profile=profile)
        logo = self.get_data(0x0B, profile=profile)

        colorIndex = 0b00111 & sx
        isPulsing = 0b100000 & sx
        return [sx,scroll,logo]

    '''
        lightIndex:
            0 = Sx button
            1 = scroll Whell
            2 = bottom logo
    '''
    def getLight(self, profile=1, lightIndex=0):
        index=0x0C
        if lightIndex == 1:
            index=0x0D
        elif lightIndex == 2:
            index=0x0B

        value = self.get_data(index, profile=profile)

        colorIndex =  0b00111 & value
        # 0 = off 1= steady 2= pulsing 3=battle
        effect = (0b110000 & value) >> 4
        print("Profile: " + str(profile) + " index: " + str(lightIndex) + " value: " + str(value) + " eff:" + str(effect))
        return [colorIndex, effect]

    def setLight(self, profile=1, lightIndex=0, color=1, effect=1):
        index=0x0C
        if lightIndex == 1:
            index=0x0D
        elif lightIndex == 2:
            index=0x0B

        value = color | (16 * effect)
        self.put_data(index, value, profile=profile, reset=False)


    def testLight(self):
        profile = 2
        color= 17
        self.put_data(0x0C, 70, profile=profile, reset=False)
        self.put_data(0x0D, 80, profile=profile, reset=False)
        self.put_data(0x0B, 90, profile=profile, reset=True)



def main():
    m10 = level10_usb()

if __name__ == '__main__':
    main()
