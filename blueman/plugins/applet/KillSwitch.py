# Copyright (C) 2008 Valmantas Paliksa <walmis at balticum-tv dot lt>
# Copyright (C) 2008 Tadas Dailyda <tadas at dailyda dot com>
#
# Licensed under the GNU General Public License Version 3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# NMMonitor: Monitors a selected device and emits a signal when it was disconnected via NetworkManager
import gobject
import dbus
from blueman.Functions import *
from blueman.Functions import _

from blueman.main.SignalTracker import SignalTracker
from blueman.plugins.AppletPlugin import AppletPlugin
from blueman.main.KillSwitchNG import KillSwitchNG, RFKillType, RFKillState
import blueman.main.KillSwitch as _KillSwitch

class KillSwitch(AppletPlugin):
	__author__ = "Walmis"
	__description__ = _("Toggles a Bluetooth killswitch when Bluetooth power state changes. Some laptops, mostly Dells have this feature\n<b>Note</b>: This plugin stays on automatically if it detects a killswitch.")
	__depends__ = ["PowerManager", "StatusIcon"]
	__icon__ = "system-shutdown"
	__options__  = {
		"checked" : (bool, False)
	}
	
	def on_load(self, applet):
		self.signal = None
		try:
			self.Manager = KillSwitchNG()
			self.signal = self.Manager.connect("switch-changed", self.on_switch_changed)
			dprint("Using the new killswitch system")
		except OSError, e:
			dprint("Using the old killswitch system", e)
			self.Manager = _KillSwitch.Manager()
		
			if not self.get_option("checked"):
				gobject.timeout_add(1000, self.check)
			
	def on_switch_changed(self, manager, switch):
		if switch.type == RFKillType.BLUETOOTH:
			s = manager.GetGlobalState()
			dprint(s, switch.soft)
			if not s and (switch.soft == 1 or switch.hard == 1):
				self.Applet.Plugins.PowerManager.SetBluetoothStatus(False)
			elif s and (switch.soft == 0 or switch.hard == 0):
				self.Applet.Plugins.PowerManager.SetBluetoothStatus(True)
			
	def check(self):
		try:
			if len(self.Manager.devices) == 0:
				self.set_option("checked", True)
				#this machine does not support bluetooth killswitch, let's unload
				self.Applet.Plugins.SetConfig("KillSwitch", False)
		except:
			pass		

	def on_unload(self):
		if self.signal:
			self.Manager.disconnect(self.signal)
		
	def on_bluetooth_power_state_changed(self, state):
		dprint(state)
		self.Manager.SetGlobalState(state)
		
	def on_query_status_icon_visibility(self):
		if self.Manager.GetGlobalState():
			return 1 #StatusIcon.SHOW
		else:
			#if killswitch removes the bluetooth adapter, dont hide the statusicon,
			#so that the user could turn bluetooth back on.
			return 2 #StatusIcon.FORCE_SHOW
		
