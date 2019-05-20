import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, filedialog
from tkinter.messagebox import showinfo, askyesno, askokcancel
from time import time
from datetime import datetime
import threading
from random import randint, uniform
from statistics import mean
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import xlsxwriter
from openpyxl import load_workbook

try:
    from winsound import Beep
except:
    import pyaudio

    class Beep():
        def __init__(self, freq, duration, volume):
            self.fs = 44100  # sampling rate, Hz, must be integer
            self.volume = volume
            self.freq = freq
            self.duration = duration/300  # in seconds. es.: 1500ms/300 = 5s

            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=pyaudio.paFloat32,
                                      channels=1,
                                      rate=self.fs,
                                      output=True)

            # generate samples, note conversion to float32 array
            # for paFloat32 sample values must be in range [-1.0, 1.0]

            self.samples = (np.sin(
                2*np.pi*np.arange(self.fs*self.duration)*self.freq/self.fs)).astype(np.float32)

            # play. May repeat with different volume values (if done interactively)

            self.stream.write(self.volume*self.samples)
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()


class Timer(threading.Thread):
    def __init__(self, mainapp, max_beep):
        threading.Thread.__init__(self)
        self.interval = threading.Event()
        self.max_beep = max_beep
        self.mainapp = mainapp
        self.count = self.mainapp.stopped

    def playSound(self):

        def func():
            # Beep(500, 1500) # 1500 ms with winsound
            Beep(500, 1500, 1.)  # 5s with pyaudio

        self.start_time = time()
        self.mainapp.start = self.start_time  # self.start
        self.count += 1
        self.mainapp.tests += 1  # self.tests
        self.mainapp.listbox.insert(tk.END, '')
        self.mainapp.listbox.insert(tk.END, 'Test '+str(self.mainapp.tests)+' started at ' +
                                    datetime.fromtimestamp(self.mainapp.start).strftime('%H:%M:%S.%f'))
        self.mainapp.listbox.see("end")
        self.mainapp.tests_summary['Test '+str(self.mainapp.tests)+' start'] = datetime.fromtimestamp(
            self.mainapp.start).strftime('%H:%M:%S.%f')
        threading.Thread(target=func).start()

    def run(self):
        while not self.interval.wait(uniform(2.9, 3.6)):
            if self.count < self.max_beep and self.mainapp.pause == False:
                self.playSound()
            elif self.mainapp.pause == True:
                self.interval.set()
                self.mainapp.stopped = self.count
            else:
                self.interval.set()


class ReactionTimeApp(tk.Tk):

    ''' 
    A multi-class desktop application built in Python with tkinter 
    to measure the reaction time to audio stimuli.
    '''

    def __init__(self):
        tk.Tk.__init__(self)

        self.data = {
            "First Name": tk.StringVar(),
            "Last Name": tk.StringVar(),
            "Version": tk.StringVar(),
            # "Max Tests": tk.IntVar(),
            "Experiment start": tk.StringVar(),
            "Experiment end": tk.StringVar(),
            "Experiment time": tk.DoubleVar(),
            "Tests": tk.IntVar(),
            "Errors": tk.IntVar(),
            "Anticipations": tk.IntVar(),
            "Missing records": tk.IntVar(),
            "AVG reaction time": tk.DoubleVar(),
        }

        self.saved = False

        self.title('Reaction Time App')
        self.configure()
        self.geometry("700x500")

        self.protocol("WM_DELETE_WINDOW", self.popup_destroy)

        #self.bind_all('<Escape>', lambda x: self.popup_destroy())
        #tk.Label(self, text="Press Esc to close the window", font=('Verdena', 8)).pack(side='bottom')

        # , weight="bold", slant="italic")
        self.title_font = tkfont.Font(family='Verdena', size=14)

        # the container is where we'll stack a bunch of frames on top of each other,
        # then the one we want visible will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # MENU
        self.menubar = tk.Menu(self)
        # create a pulldown menu, and add it to the menu bar
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Open", command=self.open_data)
        self.filemenu.add_command(label="Save", command=self.save_data)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.popup_destroy)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        # create more pulldown menus
        self.editmenu = tk.Menu(self.menubar, tearoff=0)
        self.editmenu.add_command(label="Cut")
        self.editmenu.add_command(label="Copy")
        self.editmenu.add_command(label="Paste")
        self.menubar.add_cascade(label="Edit", menu=self.editmenu)
        # create more pulldown menus
        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="About", command=self.popup_about)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        # display the menu
        self.config(menu=self.menubar)

        self.frames = {}
        for F in (StartPage, EntryName, EntryTests, Experiment, HardReactionTest, SoftReactionTest):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()
        frame.focus_set()

    def save_data(self):
        #self.now = datetime.now().strftime("%d-%m-%Y-%H:%M")
        #self.registration_name = str(sel.data['First Name'].get())+str(sel.data['Last Name'].get())
        self.date = datetime.now().strftime("%d-%m-%Y")
        self.name = str(self.data['First Name'].get())
        self.last_name = str(self.data['Last Name'].get())
        self.file_name = self.name+'-' + \
            self.last_name+'-'+str(self.date)+'.xlsx'

        if filedialog.asksaveasfilename(initialfile=self.file_name):

            self.get_data = {}
            for k in self.data.keys():
                self.get_data[k] = self.data[k].get()

            self.df = pd.DataFrame(
                [self.get_data], columns=list(self.get_data.keys()))

            for column in [column for column in list(self.df.columns) if 'elapsed' in column]:
                self.df[column] = self.df[column].replace(
                    0.0, np.nan).replace(0, np.nan)

            #self.df.to_csv('data.csv', index=False)
            self.writer = pd.ExcelWriter(self.file_name, engine='xlsxwriter')
            self.df.to_excel(self.writer, sheet_name=self.name +
                             ' '+self.last_name+' '+str(self.date), index=False)
            self.writer.save()
            self.writer.close()
            self.saved = True

    def popup_about(self):
        showinfo(
            "About", "This s my Reaction Time App. Try it to measure your reaction time to auditory stimuli!")

    def popup_destroy(self):
        # if askyesno('Esc', 'You are about to close the app. Any unsaved results will be lost!'):
        if self.saved == False:
            # if askokcancel('Esc', 'Are you sure you want to close the program without save the results?'):
            if askyesno('Esc', 'Are you sure you want to close the program without save the results?'):
                self.destroy()
            else:
                self.save_data()
        else:
            self.destroy()

    def create_plot(self):

        self.window.df = self.window.dati[[column for column in list(self.window.dati.columns) if 'elapsed' in column]]\
            .rename(columns={column: int(column.replace("Test ", "").replace(" elapsed", "")) for column in list(self.window.dati.columns) if 'elapsed' in column})\
            .T.rename(columns={0: 'Reaction Time'})

        self.window.df = self.window.df.replace(0.0, np.nan).replace(0, np.nan)

        self.window.figure = plt.Figure(dpi=100)
        self.window.ax = self.window.figure.add_subplot(111)

        self.window.line = FigureCanvasTkAgg(self.window.figure, self.window)
        self.window.line.get_tk_widget().pack(side='top', fill='both', expand=True)
        self.window.df.plot(kind='line', legend=True, ax=self.window.ax, color='b',
                            marker='o', fontsize=10).set_xlim(0, self.window.df.shape[0]+1)
        self.window.ax.set_xticks(self.window.df.index)
        self.window.ax.set_xlabel('Tests')
        self.window.ax.set_ylabel('Ms')
        self.window.ax.set_title('Reaction Time over Tests')

        # mean line
        # missing records will be ignored as NaN
        #self.window.mean = self.window.df['Reaction Time'].mean()
        self.window.mean = self.data['AVG reaction time'].get()
        self.window.ax.axhline(
            y=self.window.mean, label='AVG Reaction Time', linestyle='--', color='red')
        self.window.ax.legend()

    def open_data(self):
        try:
            self.file_path = filedialog.askopenfilename()
            self.window = tk.Toplevel(self)
            self.window.geometry("600x400")

            # until window isn't closed, the user can interact only with the window
            self.window.grab_set()

            #self.window.dati = pd.read_csv(self.file_path)
            self.window.dati = pd.read_excel(self.file_path)

            self.create_plot()

        except:
            self.window.destroy()
            showinfo('Error', "Cannot open the file '" +
                     str(os.path.basename(self.file_path))+"'!")

    def show_graph(self):
        self.window = tk.Toplevel(self)
        self.window.geometry("600x400")

        self.window.grab_set()

        self.plot_data = {}
        for k in self.data.keys():
            self.plot_data[k] = self.data[k].get()

        self.window.dati = pd.DataFrame(
            [self.plot_data], columns=list(self.plot_data.keys()))

        self.create_plot()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(
            self, text="\nWelcome to my Reaction Time App!\n\n Let's start the experiment!", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        ttk.Button(self, text="Start!",
                   command=lambda: controller.show_frame("EntryName")).pack()


class EntryName(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text='\nPlease, input your name\n',
                         font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        self.entry1 = ttk.Entry(self)
        self.entry2 = ttk.Entry(self)
        self.button = ttk.Button(self, text='Click me!', command=self.saveName)
        tk.Label(self, text='First Name:', font=('Verdena', 8)).pack()
        self.entry1.pack()
        tk.Label(self, text='Last Name', font=('Verdena', 8)).pack()
        self.entry2.pack()
        self.button.pack()

    def saveName(self):
        if len(self.entry1.get()) > 0:
            if len(self.entry2.get()) > 0:
                self.controller.show_frame('EntryTests')
                self.controller.data['First Name'].set(self.entry1.get())
                self.controller.data['Last Name'].set(self.entry2.get())
                # print(self.controller.data['Name'].get())
                # return self.controller.data['Name']
        else:
            pass


class EntryTests(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        #tk.Label(self, textvariable=controller.data['Name'], font=controller.title_font).pack()
        label = tk.Label(
            self, text='\nHow many tests do you want to perform?\n', font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = ttk.Button(self, text="Go back",
                            command=lambda: controller.show_frame("EntryName"))
        button.pack(side='bottom')

        #self.entry = ttk.Entry(self)
        # self.entry.pack()
        tk.Label(self, text='Number of tests:', font=('Verdena', 8)).pack()
        self.default = tk.IntVar()
        self.default.set(1)
        self.spinbox = ttk.Spinbox(
            self, from_=1, to=100, textvariable=self.default)
        self.spinbox.pack()
        self.button = ttk.Button(
            self, text='Click me!', command=self.saveTests)
        self.button.pack()

    def saveTests(self):
        # if len(self.spinbox.get()) > 0 and self.spinbox.get().isdigit():
        if len(self.spinbox.get()) > 0:
            self.controller.show_frame('Experiment')
            #self.controller.data['Max Tests'].set(self.spinbox.get())
            self.controller.data['Tests'].set(self.spinbox.get())
        # return self.controller.data['Max Tests']
        # else:
            # pass

        # for i in range(1,int(self.controller.data['Max Tests'].get())+1):
        for i in range(1, int(self.controller.data['Tests'].get())+1):
            self.controller.data['Test '+str(i)+' start'] = tk.StringVar()
            self.controller.data['Test '+str(i)+' end'] = tk.StringVar()
            self.controller.data['Test '+str(i)+' elapsed'] = tk.DoubleVar()


class Experiment(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        #label = tk.Label(self, text="\nOK, It's all set!\nYou are going to perform "+str(self.controller.data['Max Tests'])+" tests\n\nAre you ready?", font=controller.title_font)
        label = tk.Label(
            self, text="\nOK, it's all set!\nAre you ready?", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        ttk.Button(self, text="Ready for the simple version!",
                   command=lambda: controller.show_frame("SoftReactionTest")).pack()
        ttk.Button(self, text="Ready for the difficult version!",
                   command=lambda: controller.show_frame("HardReactionTest")).pack()
        button2 = ttk.Button(
            self, text="Go back", command=lambda: controller.show_frame("EntryTests"))
        button2.pack(side='bottom')


class HardReactionTest(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.controller.data['Version'].set('Difficult')

        self.results = []
        self.tests_summary = {}
        self.tests = 0
        self.errors = 0
        self.anticipations = 0
        self.start = None
        self.end = None
        self.start_exp = None
        self.end_exp = None
        self.first_input = 0
        self.stopped = 0
        self.pause = False

        self.bind('<Escape>', lambda x: self.stop_save())
        tk.Label(self, text="Press Esc to stop the experiment",
                 font=('Verdena', 8)).pack(side='bottom')

        label = tk.Label(self, text="\nReaction Time Test\n\nPress Enter to start the test.\nPress the Spacebar as soon as you hear the beep!\nPress the 's' key to pause the experiment.\nPress the 'r' key to resume the experiment.\n", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        ttk.Button(self, text="View graph",
                   command=self.controller.show_graph).pack()
        self.data = {}
        tk.Label(self, text='\nResults:\n', font=('Verdena', 10)).pack()

        # results in a listbox with scrollbar
        list_font = tkfont.Font(size=12)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.listbox = tk.Listbox(
            self, font=list_font, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side='left', fill='both', expand=1)

        # bind works just on this frame due to -> frame.focus_set()
        self.bind('<KeyPress>', self.reaction_test)

    def stop_save(self):
        if askyesno('Stop', 'You stopped the experiment. Are you sure you want to close the program without save the results?'):
            self.destroy()
        else:
            self.end_exp = time()
            self.validate_results = [
                value for value in self.results if value > 0.15]
            for k, v in self.tests_summary.items():
                self.controller.data[k].set(v)
            self.controller.data['Experiment end'].set(
                datetime.fromtimestamp(self.end_exp).strftime('%H:%M:%S.%f'))
            self.controller.data['Experiment time'].set(
                round(self.end_exp - self.start_exp, 3))
            self.controller.data['Errors'].set(self.errors)
            self.controller.data['Anticipations'].set(self.anticipations)
            self.controller.data['Missing records'].set(
                self.tests-len(self.results))
            self.controller.data['AVG reaction time'].set(
                round(mean(self.validate_results)*1000, 3))
            self.controller.save_data()
            self.controller.destroy()

    def pause_popup(self):
        showinfo("Pause", "Experiment on pause!")

    def game(self):

        def anticipation():
            Beep(250, 1500, 7.)

        self.end = time()
        self.elapsed = self.end - self.start

        if self.elapsed > 0.15:
            #self.listbox.insert(tk.END, 'Test '+str(self.tests)+' started at '+datetime.fromtimestamp(self.start).strftime('%H:%M:%S.%f'))
            self.listbox.insert(tk.END, 'Test '+str(self.tests)+' ended at ' +
                                datetime.fromtimestamp(self.end).strftime('%H:%M:%S.%f'))
            self.listbox.insert(tk.END, 'Reaction time: ' +
                                str(round(self.elapsed*1000, 3))+' milliseconds')
            #self.listbox.insert(tk.END, '')
            self.listbox.see("end")
            #self.tests_summary['Test '+str(self.tests)+' start'] = datetime.fromtimestamp(self.start).strftime('%H:%M:%S.%f')
        else:
            threading.Thread(target=anticipation).start()
            self.anticipations += 1
            self.listbox.insert(tk.END, 'Test '+str(self.tests)+' ended at ' +
                                datetime.fromtimestamp(self.end).strftime('%H:%M:%S.%f'))
            self.listbox.insert(tk.END, 'Reaction time: ' +
                                str(round(self.elapsed*1000, 3))+' milliseconds')
            self.listbox.insert(
                tk.END, 'You were too fast and anticipated the sound!')
            self.listbox.see("end")

        self.tests_summary['Test '+str(self.tests)+' end'] = datetime.fromtimestamp(
            self.end).strftime('%H:%M:%S.%f')
        self.tests_summary['Test '+str(self.tests) +
                           ' elapsed'] = round(self.elapsed*1000, 3)
        self.results.append(self.elapsed)
        self.start = None

    def reaction_test(self, event):

        def press_error():
            Beep(250, 300, 7.)

        if event.keysym == 'Return':
            if self.tests == 0 and self.start_exp == None:
                #self.tests += 1
                #self.timer = Timer(self, self.controller.data['Max Tests'].get())
                self.timer = Timer(self, self.controller.data['Tests'].get())
                self.timer.start()
                self.start_exp = time()
                #self.after(randint(2000, 7000), self.playSound)
                self.listbox.insert(tk.END, 'Experiment started at '+str(
                    datetime.fromtimestamp(self.start_exp).strftime('%H:%M:%S.%f')))
                #self.listbox.insert(tk.END, '')

                self.controller.data['Experiment start'].set(
                    datetime.fromtimestamp(self.start_exp).strftime('%H:%M:%S.%f'))
            else:
                pass
        elif event.keysym == 'space':
            # if self.tests == 0:
            if self.start_exp == None and self.pause == False:
                if self.first_input == 0:
                    self.first_input += 1
                    self.listbox.insert(
                        tk.END, 'Press Enter to start the test!')
                    self.listbox.insert(tk.END, '')
                else:
                    pass
            elif self.tests < self.controller.data['Tests'].get() and self.pause == False:
                try:
                    self.game()
                    #self.after(randint(2000, 7000), self.playSound)
                    #self.tests +=1
                except:
                    threading.Thread(target=press_error).start()
                    self.errors += 1
                    self.listbox.insert(tk.END, '')
                    self.listbox.insert(
                        tk.END, 'You pressed the Spacebar before the beep! Be patient!')
                    self.listbox.see("end")
            # elif self.tests == self.controller.data['Max Tests'].get():
            elif self.tests == self.controller.data['Tests'].get():
                try:
                    self.game()

                    # SUMMARY
                    self.end_exp = time()
                    # excluding anticipations from avg reaction time
                    self.validate_results = [
                        value for value in self.results if value > 0.15]

                    self.listbox.insert(tk.END, '')
                    self.listbox.insert(tk.END, 'Experiment concluded at ' +
                                        datetime.fromtimestamp(self.end_exp).strftime('%H:%M:%S.%f'))
                    self.listbox.insert(
                        tk.END, 'Experiment time: '+str(round(self.end_exp - self.start_exp, 3))+' seconds')
                    self.listbox.insert(
                        tk.END, 'Number of tests: '+str(self.tests))
                    self.listbox.insert(
                        tk.END, 'Number of errors: '+str(self.errors))
                    self.listbox.insert(
                        tk.END, 'Number of anticipations: '+str(self.anticipations))
                    self.listbox.insert(
                        tk.END, 'Missing records: '+str(self.tests-len(self.results)))
                    self.listbox.insert(tk.END, 'AVG reaction time: '+str(
                        round(mean(self.validate_results)*1000, 3))+' milliseconds')
                    self.listbox.see("end")
                    for k, v in self.tests_summary.items():
                        self.controller.data[k].set(v)

                    self.controller.data['Experiment end'].set(
                        datetime.fromtimestamp(self.end_exp).strftime('%H:%M:%S.%f'))
                    self.controller.data['Experiment time'].set(
                        round(self.end_exp - self.start_exp, 3))
                    # self.controller.data['Tests'].set(self.tests)
                    self.controller.data['Errors'].set(self.errors)
                    self.controller.data['Anticipations'].set(
                        self.anticipations)
                    self.controller.data['Missing records'].set(
                        self.tests-len(self.results))
                    self.controller.data['AVG reaction time'].set(
                        round(mean(self.validate_results)*1000, 3))

                    self.tests += 1
                except:
                    threading.Thread(target=press_error).start()
                    self.errors += 1
                    self.listbox.insert(tk.END, '')
                    self.listbox.insert(
                        tk.END, 'You pressed the Spacebar before the beep! Be patient!')
                    self.listbox.see("end")
        elif event.keysym == 's':
            self.pause = True
            self.pause_popup()
        elif event.keysym == 'r':
            self.pause = False
            self.timer = Timer(self, self.controller.data['Tests'].get())
            self.timer.start()
        else:
            pass


class SoftReactionTest(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.controller.data['Version'].set('Simple')

        self.results = []
        self.tests_summary = {}
        self.tests = 0
        self.errors = 0
        self.anticipations = 0
        self.start = None
        self.end = None
        self.start_exp = None
        self.end_exp = None

        label = tk.Label(
            self, text="\nReaction Time Test\n\nPress Enter to start the test.\nPress the Spacebar as soon as you hear the beep!", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        ttk.Button(self, text="View graph",
                   command=self.controller.show_graph).pack()
        self.data = {}
        tk.Label(self, text='\nResults:\n', font=('Verdena', 10)).pack()

        # results in a listbox with scrollbar
        list_font = tkfont.Font(size=12)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.listbox = tk.Listbox(
            self, font=list_font, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side='left', fill='both', expand=1)

        self.bind('<KeyPress>', self.reaction_test)

    def playSound(self):
        self.start = time()

        def func():
            Beep(500, 1500, 1.)
        threading.Thread(target=func).start()

    def game(self):

        def anticipation():
            Beep(250, 1500, 7.)

        self.end = time()
        self.elapsed = self.end - self.start

        if self.elapsed > 0.15:
            self.listbox.insert(tk.END, 'Test '+str(self.tests)+' started at ' +
                                datetime.fromtimestamp(self.start).strftime('%H:%M:%S.%f'))
            self.listbox.insert(tk.END, 'Test '+str(self.tests)+' ended at ' +
                                datetime.fromtimestamp(self.end).strftime('%H:%M:%S.%f'))
            self.listbox.insert(tk.END, 'Reaction time: ' +
                                str(round(self.elapsed*1000, 3))+' milliseconds')
            self.listbox.insert(tk.END, '')
            self.listbox.see("end")
        else:
            threading.Thread(target=anticipation).start()
            self.anticipations += 1
            self.listbox.insert(tk.END, 'Test '+str(self.tests)+' ended at ' +
                                datetime.fromtimestamp(self.end).strftime('%H:%M:%S.%f'))
            self.listbox.insert(tk.END, 'Reaction time: ' +
                                str(round(self.elapsed*1000, 3))+' milliseconds')
            self.listbox.insert(
                tk.END, 'You were too fast and anticipated the sound!')
            self.listbox.insert(tk.END, '')
            self.listbox.see("end")

        self.tests_summary['Test '+str(self.tests)+' start'] = datetime.fromtimestamp(
            self.start).strftime('%H:%M:%S.%f')
        self.tests_summary['Test '+str(self.tests)+' end'] = datetime.fromtimestamp(
            self.end).strftime('%H:%M:%S.%f')
        self.tests_summary['Test '+str(self.tests) +
                           ' elapsed'] = round(self.elapsed*1000, 3)
        self.results.append(self.elapsed)
        self.start = None

    def reaction_test(self, event):

        def press_error():
            Beep(250, 300, 7.)

        if event.keysym == 'Return':
            if self.tests == 0:
                self.start_exp = time()
                self.tests += 1
                self.after(randint(2900, 3600), self.playSound)
                self.listbox.insert(tk.END, 'Experiment started at '+str(
                    datetime.fromtimestamp(self.start_exp).strftime('%H:%M:%S.%f')))
                self.listbox.insert(tk.END, '')

                self.controller.data['Experiment start'].set(
                    datetime.fromtimestamp(self.start_exp).strftime('%H:%M:%S.%f'))
            else:
                pass
        elif event.keysym == 'space':
            if self.tests == 0:
                self.listbox.insert(tk.END, 'Press Enter to start the test!')
                self.listbox.insert(tk.END, '')
                #tk.Label(self, text ='Press 1 to start a new test.\n', bg='red', font=('Verdena', 12, 'bold italic')).pack()
            elif self.tests < self.controller.data['Tests'].get():
                try:
                    self.game()
                    self.after(randint(2900, 3600), self.playSound)
                    self.tests += 1
                except:
                    threading.Thread(target=press_error).start()
                    self.errors += 1
                    #tk.Label(self, text ='You pressed 2 before the beep! Be patient!\n', bg='red', font=('Verdena', 12, 'bold italic')).pack()
                    self.listbox.insert(
                        tk.END, 'You pressed the Spacebar before the beep! Be patient!')
                    self.listbox.insert(tk.END, '')
            elif self.tests == self.controller.data['Tests'].get():
                try:
                    self.game()
                    # SUMMARY
                    self.end_exp = time()

                    # excluding anticipations from avg reaction time
                    self.validate_results = [
                        value for value in self.results if value > 0.15]

                    self.listbox.insert(tk.END, 'Experiment concluded at ' +
                                        datetime.fromtimestamp(self.end_exp).strftime('%H:%M:%S.%f'))
                    self.listbox.insert(
                        tk.END, 'Experiment time: '+str(round(self.end_exp - self.start_exp, 3))+' seconds')
                    self.listbox.insert(
                        tk.END, 'Number of tests: '+str(self.tests))
                    self.listbox.insert(
                        tk.END, 'Number of errors: '+str(self.errors))
                    self.listbox.insert(
                        tk.END, 'Number of anticipations: '+str(self.anticipations))
                    self.listbox.insert(tk.END, 'AVG reaction time: '+str(
                        round(mean(self.validate_results)*1000, 3))+' milliseconds')

                    for k, v in self.tests_summary.items():
                        self.controller.data[k].set(v)

                    self.controller.data['Experiment end'].set(
                        datetime.fromtimestamp(self.end_exp).strftime('%H:%M:%S.%f'))
                    self.controller.data['Experiment time'].set(
                        round(self.end_exp - self.start_exp, 3))
                    self.controller.data['Tests'].set(self.tests)
                    self.controller.data['Errors'].set(self.errors)
                    self.controller.data['Anticipations'].set(
                        self.anticipations)
                    self.controller.data['AVG reaction time'].set(
                        round(mean(self.validate_results)*1000, 3))

                    self.tests += 1

                except:
                    threading.Thread(target=press_error).start()
                    self.errors += 1
                    self.listbox.insert(
                        tk.END, 'You pressed the Spacebar before the beep! Be patient!')
                    self.listbox.insert(tk.END, '')
        else:
            pass


if __name__ == "__main__":
    app = ReactionTimeApp()
    app.mainloop()
