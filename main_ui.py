"""Lightweight native interface. All Tk operations run on the main thread."""
import ctypes
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('HololiveDreams.HighLowAuto.Personal')
except (AttributeError, OSError):
    pass

import contextlib
import json
import queue
import threading
import tkinter as tk
from tkinter import font, ttk, messagebox
from PIL import Image, ImageTk
from fluent_theme import FluentTheme, Tooltip, BG, TEXT, MUTED, ACCENT
from app_locale import APP_VERSION, LANGUAGES, text, error_message
from daily_accounting import net_profit, record_day
from global_hotkey import GlobalHotkey
from hotkey_settings import captured_hotkey, parse_stop_hotkey
from user_storage import USER_DATA_DIR, prepare_user_data
import auto_bot

SETTINGS_FILE = USER_DATA_DIR / 'settings.json'

class NullOutput:
    def write(self, _message): pass
    def flush(self): pass

class HololiveBotUI:
    BG, TEXT, MUTED = BG, TEXT, MUTED
    def __init__(self, root, *, hotkey_factory=GlobalHotkey, runner=auto_bot.auto_play_loop):
        self.root, self.runner = root, runner
        self.worker = None
        self.messages = queue.Queue(maxsize=256)
        self.closing = self.running = self.stopping = self.has_error = False
        self.reset_confirming = False
        self.help_dialog = None
        self.capture_target = None
        self.generation = 0
        self.state_key = 'ready'
        self.history = []
        self.stats = self.read_stats()
        self.ledger_day = self.stats['day']
        settings = self.load_settings()
        self.language = tk.StringVar(root, settings['language'])
        self.strategy = tk.IntVar(root, settings['strategy'])
        self.start_key, self.stop_key = settings['start_key'], settings['stop_key']
        self.start_display = tk.StringVar(root, self.start_key)
        self.stop_display = tk.StringVar(root, self.stop_key)
        try:
            self.scale = (ctypes.windll.user32.GetDpiForWindow(root.winfo_id()) or 96)/96
        except (AttributeError, OSError):
            self.scale = root.winfo_fpixels('1i')/96
        # Keep the full form visible on smaller screens and high-DPI displays.
        self.scale = min(self.scale,(root.winfo_screenwidth()-60)/450,
                         (root.winfo_screenheight()-100)/800)
        root.tk.call('tk', 'scaling', self.scale*96/72)
        for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont'):
            font.nametofont(name).configure(family='Segoe UI', size=10)
        root.configure(bg=self.BG)
        root.geometry(f'{self.px(450)}x{self.px(800)}')
        root.minsize(self.px(360), self.px(640))
        root.protocol('WM_DELETE_WINDOW', self.close)
        try:
            png_icon = auto_bot.RESOURCE_DIR/'icon_transparent.png'
            if png_icon.exists():
                with Image.open(png_icon) as image:
                    self._app_icons = [ImageTk.PhotoImage(image.resize((size,size),Image.Resampling.LANCZOS),master=root)
                                       for size in (256,48,32,16)]
                root.iconphoto(True, *self._app_icons)
            else:
                root.iconbitmap(str(auto_bot.RESOURCE_DIR/'icon.ico'))
        except tk.TclError: pass
        self.build()
        self.apply_language()
        self.start_hotkey = hotkey_factory(lambda:self.post('start_hotkey', generation=self.generation),
            lambda key,ok,error:self.post('hotkey_status', key=key, ok=ok), value=self.start_key)
        self.stop_hotkey = hotkey_factory(lambda:self.post('stop_hotkey', generation=self.generation),
            lambda key,ok,error:self.post('hotkey_status', key=key, ok=ok), value=self.stop_key)
        self.start_hotkey.start()
        self.stop_hotkey.start()
        root.bind('<Button-1>', self.cancel_capture, add='+')
        root.after(50, self.poll)

    def px(self, value): return round(value*self.scale)
    def tr(self, key, **values): return text(LANGUAGES[self.language.get()], key, **values)

    @staticmethod
    def read_stats():
        day = record_day()
        auto_bot.ensure_daily_data(day)
        coins, fails = auto_bot.load_daily_data(day)
        wins, complete = auto_bot.load_daily_wins(day)
        return dict(coins=coins, fails=fails, wins=wins, complete=complete,
                    profit=net_profit(coins, fails, wins, complete), day=day)

    @staticmethod
    def load_settings():
        defaults = dict(language='繁體中文', start_key='F8', stop_key='INSERT', strategy=0)
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding='utf-8'))
            if not isinstance(saved,dict): return defaults
            if saved.get('language') not in LANGUAGES or saved.get('strategy') not in (0,1): return defaults
            sm,sk = parse_stop_hotkey(saved['start_key'])
            tm,tk = parse_stop_hotkey(saved['stop_key'])
            if sk==tk and set(sm)==set(tm): return defaults
            return {key:saved[key] for key in defaults}
        except (OSError, ValueError, KeyError, TypeError): return defaults

    def save_settings(self):
        data = dict(language=self.language.get(), start_key=self.start_key,
                    stop_key=self.stop_key, strategy=self.strategy.get())
        try:
            temporary = SETTINGS_FILE.with_suffix('.tmp')
            temporary.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
            temporary.replace(SETTINGS_FILE)
        except OSError: pass

    def build(self):
        self.theme=FluentTheme(self.root,self.px)
        self.compact=None
        self._resize_job=None
        self._wrap_width=None
        self._strategies_stacked=False
        self.main=main=ttk.Frame(self.root,padding=self.px(24))
        main.pack(fill='both',expand=True)
        main.columnconfigure(0,weight=1)
        main.rowconfigure(6,weight=1)
        heading=ttk.Frame(main)
        heading.grid(row=0,column=0,sticky='ew')
        heading.columnconfigure(1,weight=1)
        with Image.open(auto_bot.RESOURCE_DIR/'assets'/'high-low-title.png') as image:
            image=image.convert('RGBA')
            image.thumbnail((self.px(84),self.px(50)),Image.Resampling.LANCZOS)
            self._game_icon=ImageTk.PhotoImage(image,master=self.root)
        self.game_logo=ttk.Label(heading,image=self._game_icon)
        self.game_logo.grid(row=0,column=0,padx=(0,self.px(12)))
        self.title_label=ttk.Label(heading,style='Title.TLabel',justify='left')
        self.title_label.grid(row=0,column=1,sticky='ew')
        self.instructions=ttk.Label(main,style='Muted.TLabel',justify='left')
        self.instructions.grid(row=1,column=0,sticky='ew',pady=(self.px(8),self.px(12)))
        self.status=ttk.Label(main,style='Muted.TLabel')
        self.status.grid(row=2,column=0,sticky='w',pady=(0,self.px(12)))
        self.summary=ttk.Frame(main,style='Card.TFrame',padding=self.px(16))
        self.summary.grid(row=3,column=0,sticky='ew',pady=(0,self.px(12)))
        self.summary.columnconfigure(0,weight=1)
        self.coins_label=ttk.Label(self.summary,style='Count.TLabel')
        self.coins_label.grid(row=0,column=0,sticky='ew')
        self.profit_label=ttk.Label(self.summary,style='Profit.TLabel',justify='left')
        self.profit_label.grid(row=1,column=0,sticky='ew',pady=(self.px(8),0))
        self.counts_label=ttk.Label(self.summary,style='CardMuted.TLabel')
        self.counts_label.grid(row=2,column=0,sticky='ew',pady=(self.px(4),0))
        self.form=form=ttk.Frame(main,style='Card.TFrame',padding=self.px(16))
        form.grid(row=4,column=0,sticky='ew',pady=(0,self.px(16)))
        form.columnconfigure(1,weight=1)
        self.form_rows=[]
        for row,name in enumerate(('language_label','strategy_label','start_key_label','stop_key_label')):
            parent=form
            if name=='strategy_label':
                parent=ttk.Frame(form,style='Surface.TFrame')
                parent.grid(row=row,column=0,sticky='w',padx=(0,self.px(12)))
                widget=ttk.Label(parent,style='Card.TLabel')
                widget.pack(side='left')
                self.strategy_help=ttk.Button(parent,text='?',image=self.theme.help_icon,
                    style='Info.TButton',command=self.show_strategy_help,takefocus=True)
                self.strategy_help.pack(side='left',padx=(self.px(4),0))
                self.help_tooltip=Tooltip(self.strategy_help,lambda:self.tr('strategy_help'),self.px)
                self.form_rows.append(parent)
            else:
                widget=ttk.Label(parent,style='Card.TLabel')
                widget.grid(row=row,column=0,sticky='w',padx=(0,self.px(12)))
                self.form_rows.append(widget)
            setattr(self,name,widget)
        self.language_choice=ttk.Combobox(form,textvariable=self.language,values=tuple(LANGUAGES),
                                          state='readonly',width=12)
        self.language_choice.grid(row=0,column=1,sticky='ew')
        self.language_choice.bind('<<ComboboxSelected>>',self.change_language)
        self.form_rows.append(self.language_choice)
        strategy_row=ttk.Frame(form,style='Surface.TFrame')
        strategy_row.grid(row=1,column=1,sticky='ew')
        self.form_rows.append(strategy_row)
        self.strategy_buttons=[ttk.Radiobutton(strategy_row,variable=self.strategy,value=value,
                                              command=self.save_settings) for value in (0,1)]
        self.strategy_buttons[0].grid(row=0,column=0,sticky='w')
        self.strategy_buttons[1].grid(row=0,column=1,sticky='w',padx=(self.px(12),0))
        strategy_row.bind('<Configure>',self.layout_strategies)
        self.field_frames={}
        for row,kind,variable in ((2,'start',self.start_display),(3,'stop',self.stop_display)):
            field=ttk.Frame(form,style='Field.TFrame',padding=(self.px(8),self.px(5)))
            field.grid(row=row,column=1,sticky='ew')
            entry=tk.Entry(field,textvariable=variable,state='readonly',width=12,
                           background='white',readonlybackground='white',foreground=self.TEXT,
                           disabledbackground='#f0f0f0',disabledforeground='#a0a0a0',
                           relief='flat',borderwidth=0,highlightthickness=0,cursor='hand2')
            entry.pack(fill='x',expand=True)
            entry.bind('<Button-1>',lambda event,target=kind:self.begin_capture(target))
            field.bind('<Button-1>',lambda event,target=kind:self.begin_capture(target))
            entry.bind('<FocusIn>',lambda event,target=kind:self.field_frames[target].configure(style='FocusField.TFrame'))
            entry.bind('<FocusOut>',self.capture_focus_out)
            entry.bind('<FocusOut>',lambda event,target=kind:self.field_frames[target].configure(
                style='DisabledField.TFrame' if self.running else 'Field.TFrame'),add='+')
            entry.bind('<KeyPress>',self.capture_key)
            setattr(self,kind+'_entry',entry)
            self.field_frames[kind]=field
            self.form_rows.append(field)
        self.controls=controls=ttk.Frame(main)
        controls.grid(row=5,column=0,sticky='ew',pady=(0,self.px(16)))
        controls.columnconfigure((0,1),weight=1,uniform='actions')
        self.start_button=ttk.Button(controls,style='Primary.TButton',command=self.start,
                                     image=(self.theme.play_icons['normal'],'disabled',self.theme.play_icons['disabled']),compound='left')
        self.stop_button=ttk.Button(controls,style='Secondary.TButton',command=self.stop,state='disabled',
                                    image=(self.theme.stop_icons['normal'],'disabled',self.theme.stop_icons['disabled']),compound='left')
        self.start_button.grid(row=0,column=0,sticky='ew',padx=(0,self.px(6)))
        self.stop_button.grid(row=0,column=1,sticky='ew',padx=(self.px(6),0))
        self.activity=activity=ttk.Frame(main,style='Card.TFrame',padding=self.px(12))
        activity.grid(row=6,column=0,sticky='nsew')
        self.log=tk.Text(activity,wrap='word',state='disabled',width=1,height=1,bg='white',fg=self.TEXT,
                         relief='flat',bd=0,padx=self.px(4),pady=self.px(4),spacing3=self.px(4))
        scroll=ttk.Scrollbar(activity,command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y',padx=(self.px(8),0))
        self.log.pack(fill='both',expand=True)
        footer=ttk.Frame(main)
        footer.grid(row=7,column=0,sticky='ew',pady=(self.px(8),0))
        footer.columnconfigure(0,weight=1)
        self.version_label=ttk.Label(footer,text=f'v{APP_VERSION}',style='Muted.TLabel')
        self.version_label.grid(row=0,column=0,sticky='w')
        self.reset_button=ttk.Button(footer,text=self.tr('reset'),style='Subtle.TButton',command=self.reset_daily_stats)
        self.reset_button.grid(row=0,column=1,sticky='e')
        main.bind('<Configure>',self.schedule_resize)
        self.resize_text(type('Size',(),dict(width=self.px(450),height=self.px(800)))())

    def schedule_resize(self,_event):
        if self._resize_job is None:
            self._resize_job=self.root.after_idle(self.apply_resize)

    def apply_resize(self):
        self._resize_job=None
        if not self.closing:
            self.resize_text(type('Size',(),dict(width=self.main.winfo_width(),
                                               height=self.main.winfo_height()))())

    def resize_text(self,event):
        compact=event.height < self.px(720)
        if compact != self.compact:
            self.compact=compact
            outer,gap,padding=(16,8,8) if compact else (24,12,16)
            self.main.configure(padding=self.px(outer))
            for card in (self.summary,self.form): card.configure(padding=self.px(padding))
            for widget in self.form_rows: widget.grid_configure(pady=self.px(3 if compact else 6))
            for field in self.field_frames.values():
                field.configure(padding=(self.px(8),self.px(3 if compact else 5)))
            self.language_choice.configure(style='Compact.TCombobox' if compact else 'TCombobox')
            for widget in (self.status,self.summary,self.form,self.controls):
                widget.grid_configure(pady=(0,self.px(gap)))
            self.instructions.grid_configure(pady=(self.px(8),self.px(gap)))
            self.theme.style.configure('Title.TLabel',font=('Segoe UI',16 if compact else 18,'bold'))
            self.theme.style.configure('Count.TLabel',font=('Segoe UI',16 if compact else 20,'bold'))
            for name in ('Primary','Secondary'):
                self.theme.style.configure(name+'.TButton',padding=(self.px(10),self.px(3 if compact else 5)))
        width=max(self.px(200),event.width-self.px(32 if compact else 48))
        if (width,compact)==self._wrap_width: return
        self._wrap_width=(width,compact)
        self.title_label.configure(wraplength=max(self.px(130),width-self.px(96)))
        self.instructions.configure(wraplength=width)
        for label in (self.coins_label,self.profit_label,self.counts_label):
            label.configure(wraplength=width-self.px(16 if compact else 32))

    def layout_strategies(self,event):
        first,second=self.strategy_buttons
        stacked=event.width < first.winfo_reqwidth()+second.winfo_reqwidth()+self.px(12)
        if stacked==self._strategies_stacked: return
        self._strategies_stacked=stacked
        second.grid_configure(row=1 if stacked else 0,column=0 if stacked else 1,
                              padx=0 if stacked else (self.px(12),0))

    def show_strategy_help(self):
        if self.closing: return
        self.help_tooltip.hide()
        if self.help_dialog is not None and self.help_dialog.winfo_exists():
            self.help_dialog.lift()
            return
        self.end_capture()
        dialog=tk.Toplevel(self.root)
        dialog.withdraw()
        self.help_dialog=dialog
        dialog.title(self.tr('strategy_help'))
        dialog.transient(self.root)
        dialog.resizable(False,False)
        dialog.configure(bg=self.BG)
        panel=ttk.Frame(dialog,padding=self.px(20))
        panel.pack(fill='both',expand=True)
        wrap=min(self.px(420),self.root.winfo_screenwidth()-self.px(80))
        for heading,body in (('legacy','legacy_help'),('phased','phased_help')):
            card=ttk.Frame(panel,style='Card.TFrame',padding=self.px(16))
            card.pack(fill='x',pady=(0,self.px(12)))
            ttk.Label(card,text=self.tr(heading),style='Card.TLabel',font=('Segoe UI',11,'bold')).pack(anchor='w')
            ttk.Label(card,text=self.tr(body),style='CardMuted.TLabel',wraplength=wrap,justify='left').pack(
                anchor='w',pady=(self.px(8),0))
        ttk.Button(panel,text=self.tr('close'),style='Primary.TButton',command=self.close_strategy_help).pack(anchor='e')
        dialog.protocol('WM_DELETE_WINDOW',self.close_strategy_help)
        dialog.bind('<Escape>',lambda _:self.close_strategy_help())
        self.center_dialog(dialog)
        self.set_controls()

    def center_dialog(self,dialog):
        dialog.update_idletasks()
        width,height=dialog.winfo_reqwidth(),dialog.winfo_reqheight()
        x=self.root.winfo_rootx()+(self.root.winfo_width()-width)//2
        y=self.root.winfo_rooty()+(self.root.winfo_height()-height)//2
        dialog.geometry(f'{width}x{height}{x:+}{y:+}')
        dialog.deiconify()
        dialog.update_idletasks()
        try:
            from ctypes import wintypes
            user32=ctypes.windll.user32
            class MonitorInfo(ctypes.Structure):
                _fields_=[('size',wintypes.DWORD),('monitor',wintypes.RECT),
                          ('work',wintypes.RECT),('flags',wintypes.DWORD)]
            user32.MonitorFromWindow.argtypes=[wintypes.HWND,wintypes.DWORD]
            user32.MonitorFromWindow.restype=wintypes.HANDLE
            user32.GetMonitorInfoW.argtypes=[wintypes.HANDLE,ctypes.POINTER(MonitorInfo)]
            user32.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
            user32.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,
                                        ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
            parent=int(self.root.tk.call('wm','frame',self.root._w),0)
            child=int(dialog.tk.call('wm','frame',dialog._w),0)
            info=MonitorInfo(size=ctypes.sizeof(MonitorInfo))
            parent_rect,child_rect=wintypes.RECT(),wintypes.RECT()
            if (user32.GetMonitorInfoW(user32.MonitorFromWindow(parent,2),ctypes.byref(info))
                    and user32.GetWindowRect(parent,ctypes.byref(parent_rect))
                    and user32.GetWindowRect(child,ctypes.byref(child_rect))):
                width,height=child_rect.right-child_rect.left,child_rect.bottom-child_rect.top
                x=(parent_rect.left+parent_rect.right-width)//2
                y=(parent_rect.top+parent_rect.bottom-height)//2
                x=max(info.work.left,min(x,info.work.right-width))
                y=max(info.work.top,min(y,info.work.bottom-height))
                # Absolute Windows coordinates also handle monitors left of the
                # primary display, where Tk's negative offsets mean right edges.
                user32.SetWindowPos(child,None,x,y,0,0,0x0015)
        except (AttributeError,OSError):
            pass

    def close_strategy_help(self):
        if self.help_dialog is not None:
            self.help_dialog.destroy()
            self.help_dialog=None
        self.set_controls()

    def apply_language(self):
        for button,key in zip(self.strategy_buttons,('legacy','phased')):
            button.configure(text=self.tr(key))
        self.root.title(f'Hololive Dreams — {self.tr("title")}')
        for widget,key in ((self.title_label,'title'),(self.instructions,'instructions'),
            (self.language_label,'language'),(self.strategy_label,'strategy'),
            (self.start_key_label,'start_key'),(self.stop_key_label,'stop_key'),
            (self.start_button,'start'),(self.stop_button,'stop'),(self.reset_button,'reset')):
            widget.configure(text=self.tr(key))
        self.refresh_stats()
        self.status.configure(text=self.tr(self.state_key))
        self.render_history()

    def change_language(self,_event=None):
        self.close_strategy_help()
        self.end_capture()
        self.apply_language()
        self.save_settings()

    def refresh_stats(self):
        self.coins_label.configure(text=self.tr('coins',coins=self.stats['coins']))
        key='profit' if self.stats['profit'] is not None else 'unknown_profit'
        self.profit_label.configure(text=self.tr(key,profit=self.stats['profit']))
        wins=self.stats['wins'] if self.stats['complete'] else f"≥{self.stats['wins']}"
        self.counts_label.configure(text=self.tr('counts',wins=wins,fails=self.stats['fails']))

    def render_history(self):
        self.log.configure(state='normal')
        self.log.delete('1.0','end')
        self.log.insert('end','\n'.join(self.tr(key,**values) for key,values in self.history))
        self.log.see('end')
        self.log.configure(state='disabled')

    def record(self,key,**values):
        self.history.append((key,values))
        self.history=self.history[-100:]
        self.render_history()

    def post(self,kind,values=None,**kwargs):
        if not self.closing or kind=='done':
            try: self.messages.put_nowait((kind,values if values is not None else kwargs))
            except queue.Full: pass

    def configure_hotkeys(self):
        if hasattr(self,'start_hotkey'):
            self.generation+=1
            enabled=not self.closing and not self.reset_confirming and self.capture_target is None
            self.start_hotkey.configure(value=self.start_key,enabled=enabled and not self.running and self.help_dialog is None)
            self.stop_hotkey.configure(value=self.stop_key,enabled=enabled)

    def begin_capture(self,target):
        if self.running or self.closing: return 'break'
        self.capture_target=target
        self.configure_hotkeys()
        getattr(self,target+'_display').set(self.tr('capture'))
        getattr(self,target+'_entry').focus_set()
        return 'break'

    def end_capture(self,_event=None):
        self.capture_target=None
        self.start_display.set(self.start_key)
        self.stop_display.set(self.stop_key)
        self.configure_hotkeys()

    def cancel_capture(self,event):
        if self.capture_target and event.widget not in (self.start_entry,self.stop_entry): self.end_capture()

    def capture_focus_out(self,event):
        if self.capture_target and event.widget is getattr(self,self.capture_target+'_entry'):
            self.end_capture()

    def capture_key(self,event):
        if not self.capture_target: return
        if event.keysym=='Escape' and not event.state&0x20005:
            self.end_capture()
            return 'break'
        value=captured_hotkey(event.keysym,event.state,event.keycode)
        if value:
            other=self.stop_key if self.capture_target=='start' else self.start_key
            mods,key=parse_stop_hotkey(value)
            other_mods,other_key=parse_stop_hotkey(other)
            if key==other_key and set(mods)==set(other_mods): self.record('duplicate')
            else:
                setattr(self,self.capture_target+'_key',value)
                self.end_capture()
                self.save_settings()
        return 'break'

    def set_controls(self):
        self.start_button.configure(state='disabled' if self.running or self.help_dialog is not None or self.reset_confirming or self.closing else 'normal')
        self.stop_button.configure(state='normal' if self.running and not self.stopping else 'disabled')
        self.reset_button.configure(state='disabled' if self.running or self.reset_confirming or self.closing else 'normal')
        for button in self.strategy_buttons:
            button.configure(state='disabled' if self.running else 'normal')
        for widget in (self.start_entry,self.stop_entry):
            widget.configure(state='disabled' if self.running else 'readonly')
        for name in ('start','stop'):
            enabled=str(getattr(self,name+'_button').cget('state'))!='disabled'
            primary=enabled and (name=='stop' if self.running else name=='start')
            getattr(self,name+'_button').configure(style='Primary.TButton' if primary else 'Secondary.TButton',
                image=(getattr(self.theme,'play_icons' if name=='start' else 'stop_icons')['normal'],
                       'disabled',getattr(self.theme,'play_icons' if name=='start' else 'stop_icons')['disabled']))
            self.field_frames[name].configure(style='DisabledField.TFrame' if self.running else 'Field.TFrame')
        self.configure_hotkeys()

    def start(self):
        if self.closing or self.reset_confirming or self.help_dialog is not None or self.capture_target or self.running or (self.worker and self.worker.is_alive()): return
        self.stats=self.read_stats()
        self.ledger_day=self.stats['day']
        self.refresh_stats()
        self.running=True
        self.stopping=self.has_error=False
        self.state_key='running'
        self.status.configure(text=self.tr(self.state_key),foreground=ACCENT)
        self.history=[]
        self.record('running')
        self.save_settings()
        self.set_controls()
        auto_bot.bot_running=True
        mode='phased' if self.strategy.get()==1 else 'legacy'
        self.worker=threading.Thread(target=self.run,args=(mode,),name='high-low-session',daemon=True)
        self.worker.start()

    def run(self,mode):
        try:
            with contextlib.redirect_stdout(NullOutput()): self.runner(mode,notify=self.post)
        except Exception as exc: self.post('error',detail=str(exc))
        finally:
            auto_bot.bot_running=False
            self.post('done')

    def stop(self):
        if self.running:
            auto_bot.bot_running=False
            self.stopping=True
            self.state_key='stopping'
            self.status.configure(text=self.tr(self.state_key),foreground=self.MUTED)
            self.set_controls()

    def reset_daily_stats(self):
        if self.closing or self.running or self.reset_confirming or (self.worker and self.worker.is_alive()):
            return
        self.end_capture()
        self.reset_confirming=True
        self.set_controls()
        try:
            confirmed=messagebox.askyesno(self.tr('reset'),self.tr('reset_confirm'),
                                         parent=self.root,icon='warning',default='no')
            if confirmed and not self.closing:
                auto_bot.reset_daily_data()
                self.stats=self.read_stats()
                self.ledger_day=self.stats['day']
                self.refresh_stats()
                self.history=[]
                self.record('daily_reset')
        except OSError:
            messagebox.showerror(self.tr('error'),self.tr('reset_error'),parent=self.root)
        finally:
            self.reset_confirming=False
            self.set_controls()

    def refresh_record_day(self):
        if (not self.running and not self.reset_confirming and not self.closing
                and not (self.worker and self.worker.is_alive())
                and record_day()!=self.ledger_day):
            self.stats=self.read_stats()
            self.ledger_day=self.stats['day']
            self.refresh_stats()
            self.history=[]
            self.record('daily_reset')

    def poll(self):
        try:
            while True:
                kind,values=self.messages.get_nowait()
                if kind in ('start_hotkey','stop_hotkey'):
                    if values['generation']==self.generation and not self.capture_target:
                        (self.start if kind=='start_hotkey' else self.stop)()
                elif kind=='hotkey_status':
                    if not values['ok']: self.record('hotkey_error',key=values['key'])
                elif kind=='stats':
                    self.stats=values
                    self.ledger_day=values.get('day',self.ledger_day)
                    self.refresh_stats()
                elif kind=='state' and not self.stopping:
                    self.state_key=values['state']
                    self.status.configure(text=self.tr(self.state_key))
                elif kind=='credit': self.record('credit',amount=values['amount'])
                elif kind=='failed': self.record('failed')
                elif kind=='daily_reset':
                    self.history=[]
                    self.record('daily_reset')
                elif kind=='error':
                    self.has_error=True
                    self.state_key='error'
                    self.status.configure(text=self.tr('error'),foreground='#b42318')
                    key,params=error_message(values['detail'])
                    self.record(key,**params)
                elif kind=='done':
                    self.running=self.stopping=False
                    if not self.has_error:
                        self.state_key='stopped'
                        self.status.configure(text=self.tr('stopped'),foreground=self.MUTED)
                        self.record('stopped')
                    self.set_controls()
        except queue.Empty: pass
        self.refresh_record_day()
        if not self.closing: self.root.after(50,self.poll)

    def close(self):
        if self.closing: return
        self.closing=True
        self.save_settings()
        self.stop()
        self.start_hotkey.close()
        self.stop_hotkey.close()
        self.root.after(50,self.finish_close)

    def finish_close(self):
        if self.worker and self.worker.is_alive(): self.root.after(50,self.finish_close)
        else: self.root.destroy()

def main():
    root=tk.Tk()
    root.withdraw()
    try:
        prepare_user_data(auto_bot.APP_DIR)
    except (OSError,ValueError) as error:
        language=LANGUAGES[HololiveBotUI.load_settings()['language']]
        messagebox.showerror(text(language,'error'),
                            text(language,'error_storage',detail=str(error)),parent=root)
        root.destroy()
        return
    HololiveBotUI(root)
    root.deiconify()
    root.mainloop()

if __name__=='__main__': main()
