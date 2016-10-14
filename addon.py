import xbmc
import os
import sys
import xbmcaddon
import xbmcgui
import time
import subprocess
import urllib2

addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )
sys.path.append(os.path.join( addon_dir, 'resources', 'lib' ) )
new_hyperion_config_path = addon_dir+"/hyperion.config.new"
hyperion_installation_path="/storage/hyperion/bin"
settings_cache_path = "/storage/.kodi/userdata/addon_data/plugin.program.hyperion.configurator/settings.xml"
default_config_path="/storage/.config/hyperion.config.json"
run_command="/storage/hyperion/bin/hyperiond.sh /storage/.kodi/addons/plugin.program.hyperion.configurator-master/hyperion.config.new"
gpio_version=False

import HyperPyCon

def _(code):
    return addon.getLocalizedString(code)

line1 = _(30000)
line2 = _(30001)
line3 = _(30002)
xbmcgui.Dialog().ok(addonname, line1, line2 + line3)

#check if hyperion is installed
if not HyperPyCon.HyperPyCon.isHyperionInstalled():
    if HyperPyCon.HyperPyCon.amIonOSMC():
        xbmcgui.Dialog().ok(addonname, _(30010))
        sys.exit()
    else:
        xbmcgui.Dialog().ok(addonname, _(30011))
        sys.exit()

try:
    if HyperPyCon.HyperPyCon.amIonOSMC():
        settings_cache_path = "/home/osmc/.kodi/userdata/addon_data/plugin.program.hyperion.configurator/settings.xml"
        default_config_path="/etc/hyperion.config.json"
        run_command="hyperiond /home/osmc/.kodi/addons/plugin.program.hyperion.configurator-master/hyperion.config.new"
        hyperion_installation_path=""
        subprocess.call(["lsusb"])
        subprocess.call(["killall", "-help"])
        
except Exception, e:
    if xbmcgui.Dialog().yesno(addonname, _(30020)):
        pDialog = xbmcgui.DialogProgress()
        pDialog.create(_(30021), _(30022))
        subprocess.call(["sudo","apt-get","install","-y","psmisc","usbutils"])
        pDialog.close()
    else:
        sys.exit()  

try:

    if HyperPyCon.HyperPyCon.amIonWetek() :
        device_versions = [ HyperPyCon.HyperPyCon.adalightapa102 , HyperPyCon.HyperPyCon.adalight ]
    else:
        device_versions = [ HyperPyCon.HyperPyCon.adalightapa102 , HyperPyCon.HyperPyCon.adalight,  HyperPyCon.HyperPyCon.ws2801, HyperPyCon.HyperPyCon.apa102]
    selected_device = xbmcgui.Dialog().select(_(30030) + ':',device_versions)
    if selected_device == -1:
        sys.exit();
    if selected_device == 2 or selected_device == 3:    
        if "spidev" not in subprocess.check_output(['ls','/dev']):
            xbmcgui.Dialog().ok(addonname, _(30031))
        gpio_version=True

    if selected_device == 0 or selected_device == 3:
        suffix = "apa102"
    else:
        suffix = "ws2801"
        
    xbmcgui.Dialog().ok(addonname, _(30040))

    nol_horizontal = xbmcgui.Dialog().input(_(30041),"29",xbmcgui.INPUT_NUMERIC)
    nol_vertical = xbmcgui.Dialog().input(_(30042),"16",xbmcgui.INPUT_NUMERIC)
    if xbmcgui.Dialog().yesno(addonname, _(30043)):
        try:
            settingsxml = urllib2.urlopen("http://img.lightberry.eu/download/settings.xml-"+suffix).read()
            f = open(addon_dir+"/resources/settings.xml","w")
            f.write(settingsxml)
            f.close()
            if os.path.isfile(settings_cache_path):
                os.remove(settings_cache_path)
        except Exception, e:
            xbmcgui.Dialog().ok(addonname, repr(e),_(30044))
    hyperion_configuration = HyperPyCon.HyperPyCon(int(nol_horizontal), int(nol_vertical), 0.08, 0.1) #parameter from plugin settings to be added
    hyperion_configuration.set_device_type(device_versions[selected_device])
    hyperion_configuration.set_device_rate(int(addon.getSetting("rate")))
    if(addon.getSetting("colorOrder") != "Default"):
        hyperion_configuration.set_device_color_order(addon.getSetting("colorOrder").lower())
        
    hyperion_configuration.set_color_values(float(addon.getSetting("redThreshold")), float(addon.getSetting("redGamma")),float(addon.getSetting("redBlacklevel")),float(addon.getSetting("redWhitelevel")),"RED")
    hyperion_configuration.set_color_values(float(addon.getSetting("greenThreshold")), float(addon.getSetting("greenGamma")),float(addon.getSetting("greenBlacklevel")),float(addon.getSetting("greenWhitelevel")),"GREEN")
    hyperion_configuration.set_color_values(float(addon.getSetting("blueThreshold")), float(addon.getSetting("blueGamma")),float(addon.getSetting("blueBlacklevel")),float(addon.getSetting("blueWhitelevel")),"BLUE")
    hyperion_configuration.set_smoothing(addon.getSetting("smoothingType"),int(addon.getSetting("smoothingTime")),int(addon.getSetting("smoothingFreq")))
    hyperion_configuration.set_blackborderdetection((addon.getSetting("bbdEnabled") == "true"), float(addon.getSetting("bbdThreshold")))
    hyperion_configuration.set_grabber_video_standard(addon.getSetting("videoStandard"))
    hyperion_configuration.set_grabber_signal_off(addon.getSetting("colorWhenSourceIsOff"))
    if gpio_version:   
       #turn off unused leds if this is GPIO version of Lightberry
       hyperion_configuration.disable_extra_leds(150-hyperion_configuration.total_number_of_leds)
	
    options = [_(30045),_(30046),_(30047),_(30048)]
    selected_index = xbmcgui.Dialog().select(_(30049),options)

    if selected_index == 1:
        hyperion_configuration.led_chain.reverse_direction()
        hyperion_configuration.led_chain.set_offset(int(nol_horizontal))
    elif selected_index == 2 or selected_index == 3:
        offset = xbmcgui.Dialog().input(_(30050),"15",xbmcgui.INPUT_NUMERIC)
        if selected_index == 2:
            hyperion_configuration.led_chain.set_offset((-1)*int(offset))
        else:
            hyperion_configuration.led_chain.reverse_direction()
            hyperion_configuration.led_chain.set_offset(int(offset))

    grabber = ""
    if not HyperPyCon.HyperPyCon.amIonWetek():
        lsusb_output = subprocess.check_output('lsusb')
        if "1b71:3002" in lsusb_output:
            grabber = "utv007"
        elif "05e1:0408" in lsusb_output:
            grabber = "stk1160"

        if grabber != "":
            if "video0" in subprocess.check_output(['ls','/dev']):
                if xbmcgui.Dialog().yesno(addonname, _(30060)):
                    hyperion_configuration.config_grabber(grabber)
            else:
                xbmcgui.Dialog().ok(addonname, _(30061))
        else:
            xbmcgui.Dialog().ok(addonname, _(30062))
            
    xbmcgui.Dialog().ok(addonname, _(30070))
    hyperion_configuration.save_config_file(hyperion_configuration.create_config(),new_hyperion_config_path)    
    hyperion_configuration.restart_hyperion(new_hyperion_config_path)

    if not xbmcgui.Dialog().yesno(addonname, _(30071)):
        xbmcgui.Dialog().ok(addonname, _(30072))
        sys.exit()
    else:
        xbmcgui.Dialog().ok(addonname, _(30073))
        okno = xbmcgui.WindowDialog(xbmcgui.getCurrentWindowId())
        obrazek = xbmcgui.ControlImage(0,0,1280,720,addon_dir+"/test_picture.png")
        okno.addControl(obrazek)
        okno.show()
        obrazek.setVisible(True)
        hyperion_configuration.show_test_image(addon_dir+"/test_picture.png")
        time.sleep(10)
        okno.close()
        hyperion_configuration.clear_leds()

    if xbmcgui.Dialog().yesno(addonname, _(30080),_(30081)):
        hyperion_configuration.overwrite_default_config()
    elif xbmcgui.Dialog().yesno(addonname, _(30082)):
        hyperion_configuration.restart_hyperion(default_config_path)

    xbmcgui.Dialog().ok(addonname, _(30083), _(30084),_(30085))

except Exception, e:
        xbmcgui.Dialog().ok(addonname, repr(e),_(30086))


