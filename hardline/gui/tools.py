import configparser
from hardline import daemonconfig
from .. import daemonconfig, hardline


import configparser,logging

from kivy.uix.image import Image
from kivy.uix.widget import Widget

from typing import Sized, Text
from kivy.utils import platform
from kivymd.uix.button import MDFillRoundFlatButton as Button, MDRoundFlatButton
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextFieldRect,MDTextField
from kivymd.uix.label import MDLabel as Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivymd.uix.toolbar import MDToolbar
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout as BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen

import time
import traceback

# Terrible Hacc, because otherwise we cannot iumport hardline on android.
import os
import sys
import re
from .. daemonconfig import makeUserDatabase
from .. import  uihelpers, drayerdb, cidict

from kivymd.uix.picker import MDDatePicker


class ToolsAndSettingsMixin():

    def goToSettings(self, *a):
        self.screenManager.current = "Settings"

    def goToGlobalSettings(self, *a):
        globalConfig = configparser.ConfigParser(dict_type=cidict.CaseInsensitiveDict)
        globalConfig.read(hardline.globalSettingsPath)
        self.localSettingsBox.clear_widgets()

        self.localSettingsBox.add_widget(Label(size_hint=(1, 6), halign="center",
                                               text='OpenDHT Proxies'))
        self.localSettingsBox.add_widget(Label(size_hint=(1, None),
                                               text='Proxies are tried in order from 1-3'))

        self.localSettingsBox.add_widget(
            self.settingButton(globalConfig, "DHTProxy", 'server1'))
        self.localSettingsBox.add_widget(
            self.settingButton(globalConfig, "DHTProxy", 'server2'))
        self.localSettingsBox.add_widget(
            self.settingButton(globalConfig, "DHTProxy", 'server3'))

        self.localSettingsBox.add_widget(Label(size_hint=(1, 6), halign="center",
                                               text='Stream Server'))
        self.localSettingsBox.add_widget(Label(size_hint=(1, None),
                                              text='To allow others to sync to this node as a DrayerDB Stream server, set a server title to expose a service'))
        
        self.localSettingsBox.add_widget(
            self.settingButton(globalConfig, "DrayerDB", 'serverName'))

        btn1 = Button(text='Save',
                      size_hint=(1, None), font_size="14sp")

        def save(*a):
            with open(hardline.globalSettingsPath, 'w') as f:
                globalConfig.write(f)
            if platform == 'android':
                self.stop_service()
                self.start_service()
            else:
                daemonconfig.loadDrayerServerConfig()

            self.screenManager.current = "Main"

        btn1.bind(on_press=save)
        self.localSettingsBox.add_widget(btn1)
        self.screenManager.current = "GlobalSettings"

    def makeGlobalSettingsPage(self):

        screen = Screen(name='GlobalSettings')
        layout = BoxLayout(orientation='vertical', spacing=10)
        screen.add_widget(layout)


        layout.add_widget(self.makeBackButton())

        self.localSettingsScroll = ScrollView(size_hint=(1, 1))
        self.localSettingsBox = BoxLayout(
            orientation='vertical', size_hint=(1, None), spacing=10)
        self.localSettingsBox.bind(
            minimum_height=self.localSettingsBox.setter('height'))

        self.localSettingsScroll.add_widget(self.localSettingsBox)

        layout.add_widget(self.localSettingsScroll)

        return screen

    def makeSettingsPage(self):
        page = Screen(name='Settings')

        layout = BoxLayout(orientation='vertical')
        page.add_widget(layout)
        label = MDToolbar(title="Settings and Tools")
        layout.add_widget(label)

        layout.add_widget(self.makeBackButton())



        log = Button(text='System Logs',
                      size_hint=(1, None), font_size="14sp")

        btn1 = Button(text='Local Services',
                      size_hint=(1, None), font_size="14sp")
        label1 = Label(size_hint=(1, None), halign="center",
                       text='Share a local webservice with the world')

        log.bind(on_release=self.gotoLogs)
        btn1.bind(on_press=self.goToLocalServices)
        layout.add_widget(log)

        layout.add_widget(btn1)
        layout.add_widget(label1)

        btn = Button(text='Global Settings',
                     size_hint=(1, None), font_size="14sp")

        btn.bind(on_press=self.goToGlobalSettings)
        layout.add_widget(btn)

        # Start/Stop
        btn3 = Button(text='Stop', size_hint=(1, None), font_size="14sp")
        btn3.bind(on_press=self.stop_service)
        label3 = Label(size_hint=(1, None), halign="center",
                       text='Stop the background process.  It must be running to acess hardline sites.  Starting may take a few seconds.')
        layout.add_widget(btn3)
        layout.add_widget(label3)

        btn4 = Button(text='Start or Restart.',
                      size_hint=(1, None), font_size="14sp")
        btn4.bind(on_press=self.start_service)
        label4 = Label(size_hint=(1, None), halign="center",
                       text='Restart the process. It will show in your notifications.')
        layout.add_widget(btn4)
        layout.add_widget(label4)

        layout.add_widget(Widget())

        return page


    def makeLogsPage(self):
        screen = Screen(name='Logs')
        self.servicesScreen = screen

        layout = BoxLayout(orientation='vertical', spacing=10)
        screen.add_widget(layout)


        layout.add_widget(MDToolbar(title="System Logs"))

        layout.add_widget(self.makeBackButton())


        self.logsListBoxScroll = ScrollView(size_hint=(1, 1))

        self.logsListBox = BoxLayout(
            orientation='vertical', size_hint=(1, None), spacing=10)
        self.logsListBox.bind(
            minimum_height=self.logsListBox.setter('height'))

        self.logsListBoxScroll.add_widget(self.logsListBox)

        layout.add_widget(self.logsListBoxScroll)

        return screen

    def gotoLogs(self,*a):
        self.logsListBox.clear_widgets()
        try:
            from kivy.logger import LoggerHistory
            for i in LoggerHistory.history:
                self.logsListBox.add_widget(Label(text=str(i.getMessage()), size_hint=(1,None)))

            self.screenManager.current = "Logs"
        except Exception as e:
            logging.info(traceback.format_exc())