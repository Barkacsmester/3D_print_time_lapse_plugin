# Készítette Reéb Walter a Barkácsműhely nézői számára 2021-ben.
# simonjamain CustomTimelapseCuraPlugin kódját alapul véve
# https://github.com/simonjamain/CustomTimelapseCuraPlugin

from ..Script import Script

class RW_Timelapse(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "RW timelapse",
            "key": "RW_Timelapse",
            "metadata": {},
            "version": 2,
            "settings":
            {
               "activate_plugin":
                {
                    "label": "Plugin aktiválása",
                    "description": "Válaszd a plugin aktiválásához",
                    "type": "bool",
                    "default_value": true
                },
                "first_gcode":
                {
                    "label": "GCODE a tárgyasztal pozíciójához (Y).",
                    "description": "A tárgyasztal pozícionálása a fotózáshoz.",
                    "type": "str",
                    "default_value": "G0 Y220"
                },
                "second_gcode":
                {
                    "label": "GCODE a fej pozícionálásához, megnyomáshoz (X).",
                    "description": "Az elsütőgomb megnyomásának pozíciója.",
                    "type": "str",
                    "default_value": "G0 X220"
                },
                "second_gcode_back":
                {
                    "label": "GCODE a fej pozícionálásához, elengedéshez.",
                    "description": "Az elsütőgomb elengedésének pozíciója.",
                    "type": "str",
                    "default_value": "G0 X215"
                },
                "pause_length_first":
                {
                    "label": "Nyomva tartás időtartama",
                    "description": "Az az időintervallum, ameddig a gombot nyomva tartjuk a fotó elkészítéséhez.",
                    "type": "int",
                    "default_value": 700,
                    "minimum_value": 0,
                    "unit": "ms"
                }, 
                "pause_length_second":
                {
                    "label": "Fotó készítéséek időtartama",
                    "description": "Az az időintervallum, ameddig a tárgy még adott pozícióban marad a fotó elkészítéséhez.",
                    "type": "int",
                    "default_value": 1000,
                    "minimum_value": 0,
                    "unit": "ms"
                },
                "enable_retraction":
                {
                    "label": "Szálvisszahúzás engedélyezése",
                    "description": "",
                    "type": "bool",
                    "default_value": true
                },
                "retraction_distance":
                {
                    "label": "Szálvisszahúzás mértéke",
                    "description": "Milyen hosszúságú szálat húzzon vissza mielőtt elhagyja a tárgyat.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 6,
                    "enabled": "enable_retraction"
                }
            }
        }"""
    # Note : This function and some other bits of code comes from PauseAtHeight.py
    ##  Get the X and Y values for a layer (will be used to get X and Y of the
    #   layer after the pause).
    def getNextXY(self, layer):
        lines = layer.split("\n")
        for line in lines:
            if self.getValue(line, "X") is not None and self.getValue(line, "Y") is not None:
                x = self.getValue(line, "X")
                y = self.getValue(line, "Y")
                return x, y
        return 0, 0

    def execute(self, data):
        activate_plugin = self.getSettingValueByKey("activate_plugin")
        first_gcode = self.getSettingValueByKey("first_gcode")
        second_gcode = self.getSettingValueByKey("second_gcode")
        second_gcode_back = self.getSettingValueByKey("second_gcode_back")
        pause_length_first = self.getSettingValueByKey("pause_length_first")
        pause_length_second = self.getSettingValueByKey("pause_length_second")
        enable_retraction = self.getSettingValueByKey("enable_retraction")
        retraction_distance = self.getSettingValueByKey("retraction_distance")


        for layerIndex, layer in enumerate(data):
            # Check that a layer is being printed
            lines = layer.split("\n")
            for line in lines:
                if ";LAYER:" in line:
                    index = data.index(layer)

                    next_layer = data[layerIndex + 1]
                    x, y = self.getNextXY(next_layer)

                    gcode_to_append = ""

                    if activate_plugin:
                        gcode_to_append += ";CustomTimelapse Begin\n"


                        gcode_to_append += "; STEP 1 : retraction\n"
                        gcode_to_append += self.putValue(M = 83) + " ; switch to relative E values for any needed retraction\n"
                        if enable_retraction:
                            gcode_to_append += self.putValue(G = 1, F = 1800, E = -retraction_distance) + ";Retraction\n"
                        gcode_to_append += self.putValue(M = 82) + ";Switch back to absolute E values\n"

                        gcode_to_append += "; STEP 2 : Move the head up a bit\n"
                        gcode_to_append += self.putValue(G = 91) + ";Switch to relative positioning\n"
                        gcode_to_append += self.putValue(G = 0, Z = 1) + ";Move Z axis up a bit\n"
                        gcode_to_append += self.putValue(G = 90) + ";Switch back to absolute positioning\n"

                        gcode_to_append += "; STEP 3 : Move the head to \"display\" position and wait\n"
                        gcode_to_append += first_gcode + ";GCODE for the first position(display position)\n"
                        gcode_to_append += second_gcode + ";GCODE for the second position(trigger position)\n"
                        gcode_to_append += self.putValue(G = 4, P = pause_length_first) + ";Wait for camera\n"
                        gcode_to_append += second_gcode_back + ";GCODE for the second position(trigger position)\n"
                        gcode_to_append += self.putValue(M = 400) + ";Wait for moves to finish\n"
                        gcode_to_append += self.putValue(G = 4, P = pause_length_second) + ";Wait for camera\n"

                        gcode_to_append += self.putValue(G = 0, X = x, Y = y) + "\n"

                        gcode_to_append += "; STEP 6 : Move the head height back down\n"
                        gcode_to_append += self.putValue(G = 91) + ";Switch to relative positioning\n"
                        gcode_to_append += self.putValue(G = 0, Z = -1) + ";Restore Z axis position\n"
                        gcode_to_append += self.putValue(G = 90) + ";Switch back to absolute positioning\n"

                        gcode_to_append += ";CustomTimelapse End\n"


                    layer += gcode_to_append

                    data[index] = layer
                    break
        return data
