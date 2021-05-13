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
from .. import  drayerdb, cidict, libnacl

from kivymd.uix.picker import MDDatePicker


class StreamsMixin():


    #Reuse the same panel for editStream, the main hub for accessing the stream,
    #and it's core settings
    def editStream(self, name):
        if not  name in daemonconfig.userDatabases:
            self.goToStreams()
        db = daemonconfig.userDatabases[name]
        c = db.config
        try:
            c.add_section("Service")
        except:
            pass
        try:
            c.add_section("Info")
        except:
            pass

        self.streamEditPanel.clear_widgets()

        self.streamEditPanel.add_widget(Label(size_hint=(
            1, None), halign="center", text=name))

        def upOne(*a):
            self.goToStreams()

        btn1 = Button(text='Up',
                size_hint=(1, None), font_size="14sp")

        btn1.bind(on_press=upOne)

        self.streamEditPanel.add_widget(btn1)

        self.streamEditPanel.add_widget(self.makeBackButton())
        
        def goHere():
            self.editStream( name)
        self.backStack.append(goHere)
        self.backStack = self.backStack[-50:]



        btn2 = Button(text='View Feed',
                size_hint=(1, None), font_size="14sp")
        def goPosts(*a):
            self.gotoStreamPosts(name)
        btn2.bind(on_press=goPosts)
        self.streamEditPanel.add_widget(btn2)



        btn2 = Button(text='Stream Settings',
                size_hint=(1, None), font_size="14sp")
        def goSettings(*a):
            self.editStreamSettings(name)
        btn2.bind(on_press=goSettings)
        self.streamEditPanel.add_widget(btn2)


        if name.startswith('file:'):
            btn2 = Button(text='Close Stream',
            size_hint=(1, None), font_size="14sp")
            def close(*a):
                daemonconfig.closeUserDatabase(name)
                self.goToStreams()
            btn2.bind(on_press=close)
            self.streamEditPanel.add_widget(btn2)



        importData = Button(size_hint=(1,None), text="Import Data File")

        def promptSet(*a):
            def f(selection):
                if selection:
                    def f2(x):
                        if x:
                            import json
                            with open(selection) as f:
                                for i in json.loads(f.read()):
                                    with  daemonconfig.userDatabases[name]:
                                        daemonconfig.userDatabases[name].setDocument(i[0])
                                    daemonconfig.userDatabases[name].commit()
                    self.askQuestion("Really import?","yes",cb=f2)
                self.openFM.close()

            from .kivymdfmfork import MDFileManager
            from . import directories
            self.openFM= MDFileManager(select_path=f)
            self.openFM.show(directories.externalStorageDir or directories.settings_path)

            
            
        importData.bind(on_release=promptSet)
        self.streamEditPanel.add_widget(importData)


        self.screenManager.current = "EditStream"

    
    def showSharingCode(self,name,c,wp=True):
        if daemonconfig.ddbservice[0]:
            try:
                localServer = daemonconfig.ddbservice[0].getSharableURL()
            except:
                logging.exception("wtf")
        else:
            localServer=''

        d = {
            'sv':c['Sync'].get('server','') or localServer,
            'vk':c['Sync'].get("syncKey",''),
            'n':name[:24]

        }
        if wp:
            d['sk']=c['Sync'].get('writePassword','')
        else:
            d['sk']=''

        import json
        d=json.dumps(d,indent=0,separators=(',',':'))
        if wp:
            self.showQR(d, "Stream Code(full access)")
        else:
            self.showQR(d, "Stream Code(readonly)")

    def editStreamSettings(self, name):
        db = daemonconfig.userDatabases[name]
        c = db.config


        self.streamEditPanel.clear_widgets()

        self.streamEditPanel.add_widget(Label(size_hint=(
            1, None), halign="center", text=name))
        self.streamEditPanel.add_widget(Label(size_hint=(
            1, None), halign="center", text="file:"+db.filename))


       
        self.streamEditPanel.add_widget(self.makeBackButton())

      

        def save(*a):
            logging.info("SAVE BUTTON WAS PRESSED")
            # On android this is the bg service's job
            db.saveConfig()

            if platform == 'android':
                self.stop_service()
                self.start_service()

        def delete(*a):
            def f(n):
                if n and n == name:
                    daemonconfig.delDatabase(None, n)
                    if platform == 'android':
                        self.stop_service()
                        self.start_service()
                    self.goToStreams()

            self.askQuestion("Really delete?", name, f)

        self.streamEditPanel.add_widget(Label(size_hint=(1, None), halign="center", font_size="24sp",
                                              text='Sync'))

        self.streamEditPanel.add_widget(
            keyBox :=self.settingButton(c, "Sync", "syncKey"))

        self.streamEditPanel.add_widget(
            pBox :=self.settingButton(c, "Sync", "writePassword"))

        self.streamEditPanel.add_widget(Label(size_hint=(1, None), halign="center", font_size="12sp",
                                              text='Keys have a special format, you must use the generator to change them.'))

        def promptNewKeys(*a,**k):
            def makeKeys(a):
                if a=='yes':
                    
                    vk, sk = libnacl.crypto_sign_keypair()
                    vk= base64.b64encode(vk).decode()
                    sk= base64.b64encode(sk).decode()
                    keyBox.text=vk
                    pBox.text=sk
            self.askQuestion("Overwrite with random keys?",'yes',makeKeys)
        
        keyButton = Button(text='Generate New Keys',
                      size_hint=(1, None), font_size="14sp")
        keyButton.bind(on_press=promptNewKeys)
        self.streamEditPanel.add_widget(keyButton)

        self.streamEditPanel.add_widget(
            serverBox:=self.settingButton(c, "Sync", "server"))

        self.streamEditPanel.add_widget(Label(size_hint=(1, None), halign="center", font_size="14sp",
                                              text='Do not include the http:// '))

        self.streamEditPanel.add_widget(
            self.settingButton(c, "Sync", "serve",'yes'))


        self.streamEditPanel.add_widget(Label(size_hint=(1, None), halign="center", font_size="14sp",
                                              text='Set serve=no to forbid clients to sync'))

        self.streamEditPanel.add_widget(Label(size_hint=(1, None), halign="center", font_size="24sp",
                                              text='Application'))

        self.streamEditPanel.add_widget(
            self.settingButton(c, "Application", "notifications",'no'))




        def f(*a):
            def g(a):
                try:
                    import json
                    a = json.loads(a)
                    serverBox.text= c['Sync']['server']= a['sv'] or c['Sync']['server']
                    keyBox.text= c['Sync']['syncKey']= a['vk']
                    pBox.text= c['Sync']['writePassword']= a['sk']

                except:
                    pass
            self.askQuestion("Enter Sharing Code",cb=g,multiline=True)


        keyButton = Button(text='Load from Code',
                    size_hint=(1, None), font_size="14sp")
        keyButton.bind(on_press=f)
        self.streamEditPanel.add_widget(keyButton)



        def f(*a):
            self.showSharingCode(name,c)

        keyButton = Button(text='Show Sharing Code',
                      size_hint=(1, None), font_size="14sp")
        keyButton.bind(on_press=f)
        self.streamEditPanel.add_widget(keyButton)

        def f(*a):
            self.showSharingCode(name,c,wp=False)

        keyButton = Button(text='Readonly Sharing Code',
                      size_hint=(1, None), font_size="14sp")
        keyButton.bind(on_press=f)
        self.streamEditPanel.add_widget(keyButton)

        btn1 = Button(text='Save Changes',
                      size_hint=(1, None), font_size="14sp")

        btn1.bind(on_press=save)
        self.streamEditPanel.add_widget(btn1)

        btn2 = Button(text='Delete this stream',
                      size_hint=(1, None), font_size="14sp")

        btn2.bind(on_press=delete)
        self.streamEditPanel.add_widget(btn2)



        def gotoOrphans(*a,**k):
            self.gotoStreamPosts(name,orphansMode=True)

        oButton = Button(text='Show Unreachable Garbage',
                        size_hint=(1, None), font_size="14sp")
        oButton.bind(on_press=gotoOrphans)
        self.streamEditPanel.add_widget(oButton)



        self.screenManager.current = "EditStream"

    def makeStreamsPage(self):
        screen = Screen(name='Streams')
        self.servicesScreen = screen

        layout = BoxLayout(orientation='vertical', spacing=10)
        screen.add_widget(layout)



        layout.add_widget(MDToolbar(title="My Streams"))

        def upOne(*a):
            self.gotoMainScreen()

        btn1 = Button(text='Up',
                size_hint=(1, None), font_size="14sp")

        btn1.bind(on_press=upOne)

        layout.add_widget(btn1)

        layout.add_widget(self.makeBackButton())

        btn2 = Button(text='Create a Stream',
                      size_hint=(1, None), font_size="14sp")


        btn2.bind(on_press=self.promptAddStream)
        layout.add_widget(btn2)


        def f(selection):
            if selection:
                dn = 'file:'+os.path.basename(selection)
                while dn in daemonconfig.userDatabases:
                    dn=dn+'2'
                try:
                    daemonconfig.loadUserDatabase(selection,dn)
                    self.editStream(dn)
                except:
                    logging.exception(dn)

            self.openFM.close()

        #This lets us view notebook files that aren't installed.
        def promptOpen(*a):

            from .kivymdfmfork import MDFileManager
            from . import directories
            self.openFM= MDFileManager(select_path=f)
            self.openFM.show(directories.externalStorageDir or directories.settings_path)

            

        btn1 = Button(text='Open Book File',
                size_hint=(1, None), font_size="14sp")

        btn1.bind(on_press=promptOpen)

        layout.add_widget(btn1)




        self.streamsListBoxScroll = ScrollView(size_hint=(1, 1))

        self.streamsListBox = BoxLayout(
            orientation='vertical', size_hint=(1, None), spacing=10)
        self.streamsListBox.bind(
            minimum_height=self.streamsListBox.setter('height'))

        self.streamsListBoxScroll.add_widget(self.streamsListBox)

        layout.add_widget(self.streamsListBoxScroll)

        return screen

    def goToStreams(self, *a):
        "Go to a page wherein we can list user-modifiable services."
        self.streamsListBox.clear_widgets()

        def goHere():
            self.screenManager.current = "Streams"
        self.backStack.append(goHere)
        self.backStack=self.backStack[-50:]

        self.streamsListBox.add_widget(MDToolbar(title="Open Streams:"))

        try:
            s = daemonconfig.userDatabases
            time.sleep(0.5)
            for i in s:
                self.streamsListBox.add_widget(
                    self.makeButtonForStream(i))

        except Exception:
            logging.info(traceback.format_exc())

        self.screenManager.current = "Streams"

    def makeButtonForStream(self, name):
        "Make a button that, when pressed, edits the stream in the title"

        btn = Button(text=name,
                     font_size="14", size_hint=(1, None))

        def f(*a):
            self.editStream(name)
        btn.bind(on_press=f)
        return btn

    def promptAddStream(self, *a, **k):
        def f(v):
            if v:
                daemonconfig.makeUserDatabase(None, v)
                self.editStream(v)

        self.askQuestion("New Stream Name?", cb=f)



    def makeStreamEditPage(self):
        "Prettu much just an empty page filled in by the specific goto functions"

        screen = Screen(name='EditStream')
        self.servicesScreen = screen



        self.streamEditPanelScroll = ScrollView(size_hint=(1, 1))

        self.streamEditPanel = BoxLayout(
            orientation='vertical',adaptive_height= True, spacing=5)
        self.streamEditPanel.bind(
            minimum_height=self.streamEditPanel.setter('height'))

        self.streamEditPanelScroll.add_widget(self.streamEditPanel)

        screen.add_widget(self.streamEditPanelScroll)

        return screen

