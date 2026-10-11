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
from tkinter import font, ttk
from app_locale import APP_VERSION, LANGUAGES, text, error_message
from daily_accounting import net_profit
from global_hotkey import GlobalHotkey
from hotkey_settings import captured_hotkey, parse_stop_hotkey
import auto_bot

SETTINGS_FILE = auto_bot.APP_DIR / 'settings.json'

class NullOutput:
    def write(self, _message): pass
    def flush(self): pass

class HololiveBotUI:
    BG, TEXT, MUTED = '#f3f3f3', '#202020', '#666666'
    def __init__(self, root, *, hotkey_factory=GlobalHotkey, runner=auto_bot.auto_play_loop):
        self.root, self.runner = root, runner
        self.worker = None
        self.messages = queue.Queue(maxsize=256)
        self.closing = self.running = self.stopping = self.has_error = False
        self.capture_target = None
        self.generation = 0
        self.state_key = 'ready'
        self.history = []
        self.stats = self.read_stats()
        settings = self.load_settings()
        self.language = tk.StringVar(root, settings['language'])
        self.strategy = tk.StringVar(root)
        self.start_key, self.stop_key = settings['start_key'], settings['stop_key']
        self.start_display = tk.StringVar(root, self.start_key)
        self.stop_display = tk.StringVar(root, self.stop_key)
        self.mode_index = settings['strategy']
        try:
            self.scale = (ctypes.windll.user32.GetDpiForWindow(root.winfo_id()) or 96)/96
        except (AttributeError, OSError):
            self.scale = root.winfo_fpixels('1i')/96
        # Keep the full form visible on smaller screens and high-DPI displays.
        self.scale = min(self.scale,(root.winfo_screenwidth()-60)/660,
                         (root.winfo_screenheight()-100)/740)
        root.tk.call('tk', 'scaling', self.scale*96/72)
        for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont'):
            font.nametofont(name).configure(family='Segoe UI', size=11)
        root.configure(bg=self.BG)
        root.geometry(f'{self.px(660)}x{self.px(740)}')
        root.minsize(self.px(550), self.px(660))
        root.protocol('WM_DELETE_WINDOW', self.close)
        try: root.iconbitmap(str(auto_bot.RESOURCE_DIR/'icon.ico'))
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
        coins, fails = auto_bot.load_daily_data()
        wins, complete = auto_bot.load_daily_wins()
        return dict(coins=coins, fails=fails, wins=wins, complete=complete,
                    profit=net_profit(coins, fails, wins, complete))

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
                    stop_key=self.stop_key, strategy=self.strategy_choice.current())
        try:
            temporary = SETTINGS_FILE.with_suffix('.tmp')
            temporary.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
            temporary.replace(SETTINGS_FILE)
        except OSError: pass

    def build(self):
        style = ttk.Style(self.root)
        if 'vista' in style.theme_names(): style.theme_use('vista')
        style.configure('TFrame', background=self.BG)
        style.configure('TLabel', background=self.BG, foreground=self.TEXT)
        style.configure('Muted.TLabel', foreground=self.MUTED)
        style.configure('Title.TLabel', font=('Segoe UI',18,'bold'))
        style.configure('Count.TLabel', font=('Segoe UI',16,'bold'))
        style.configure('Action.TButton', padding=(self.px(12),self.px(10)))
        main = ttk.Frame(self.root,padding=self.px(24))
        main.pack(fill='both',expand=True)
        main.columnconfigure(0,weight=1)
        main.rowconfigure(8,weight=1)
        def label(name,row,style='TLabel',pady=0):
            widget = ttk.Label(main,style=style,wraplength=self.px(580),justify='left')
            widget.grid(row=row,column=0,sticky='ew',pady=pady)
            setattr(self,name,widget)
        label('title_label',0,'Title.TLabel')
        label('instructions',1,'Muted.TLabel',(self.px(8),self.px(12)))
        label('status',2,'Muted.TLabel',(0,self.px(8)))
        label('coins_label',3,'Count.TLabel')
        label('profit_label',4,'TLabel',(self.px(4),0))
        label('counts_label',5,'Muted.TLabel',(self.px(4),self.px(12)))
        form = ttk.Frame(main)
        form.grid(row=6,column=0,sticky='ew')
        form.columnconfigure(1,weight=1)
        for row,name in enumerate(('language_label','strategy_label','start_key_label','stop_key_label')):
            widget=ttk.Label(form)
            widget.grid(row=row,column=0,sticky='w',padx=(0,self.px(16)),pady=self.px(5))
            setattr(self,name,widget)
        self.language_choice=ttk.Combobox(form,textvariable=self.language,values=tuple(LANGUAGES),state='readonly')
        self.language_choice.grid(row=0,column=1,sticky='ew',pady=self.px(5))
        self.language_choice.bind('<<ComboboxSelected>>',self.change_language)
        self.strategy_choice=ttk.Combobox(form,textvariable=self.strategy,state='readonly')
        self.strategy_choice.grid(row=1,column=1,sticky='ew',pady=self.px(5))
        self.strategy_choice.bind('<<ComboboxSelected>>',lambda _:self.save_settings())
        for row,kind,variable in ((2,'start',self.start_display),(3,'stop',self.stop_display)):
            entry=ttk.Entry(form,textvariable=variable,state='readonly')
            entry.grid(row=row,column=1,sticky='ew',pady=self.px(5))
            entry.bind('<Button-1>',lambda event,target=kind:self.begin_capture(target))
            entry.bind('<FocusOut>',self.capture_focus_out)
            entry.bind('<KeyPress>',self.capture_key)
            setattr(self,kind+'_entry',entry)
        controls=ttk.Frame(main)
        controls.grid(row=7,column=0,sticky='ew',pady=(self.px(14),self.px(12)))
        controls.columnconfigure((0,1),weight=1,uniform='actions')
        self.start_button=ttk.Button(controls,style='Action.TButton',command=self.start)
        self.stop_button=ttk.Button(controls,style='Action.TButton',command=self.stop,state='disabled')
        self.start_button.grid(row=0,column=0,sticky='ew',padx=(0,self.px(6)))
        self.stop_button.grid(row=0,column=1,sticky='ew',padx=(self.px(6),0))
        activity=ttk.Frame(main)
        activity.grid(row=8,column=0,sticky='nsew')
        self.log=tk.Text(activity,wrap='word',state='disabled',height=4,bg='white',fg=self.TEXT,
            relief='solid',bd=1,padx=self.px(10),pady=self.px(8))
        scroll=ttk.Scrollbar(activity,command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y')
        self.log.pack(fill='both',expand=True)
        main.bind('<Configure>',self.resize_text)

    def resize_text(self,event):
        width=max(self.px(200),event.width-self.px(48))
        for widget in (self.title_label,self.instructions,self.profit_label):
            widget.configure(wraplength=width)

    def apply_language(self):
        selected=self.strategy_choice.current()
        if selected < 0: selected=self.mode_index
        self.strategy_choice.configure(values=(self.tr('legacy'),self.tr('phased')))
        self.strategy_choice.current(selected)
        self.root.title(f'Hololive Dreams — {self.tr("title")} v{APP_VERSION}')
        for widget,key in ((self.title_label,'title'),(self.instructions,'instructions'),
            (self.language_label,'language'),(self.strategy_label,'strategy'),
            (self.start_key_label,'start_key'),(self.stop_key_label,'stop_key'),
            (self.start_button,'start'),(self.stop_button,'stop')):
            widget.configure(text=self.tr(key))
        self.refresh_stats()
        self.status.configure(text=self.tr(self.state_key))
        self.render_history()

    def change_language(self,_event=None):
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
            enabled=not self.closing and self.capture_target is None
            self.start_hotkey.configure(value=self.start_key,enabled=enabled and not self.running)
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
        self.start_button.configure(state='disabled' if self.running else 'normal')
        self.stop_button.configure(state='normal' if self.running and not self.stopping else 'disabled')
        for widget in (self.start_entry,self.stop_entry,self.strategy_choice):
            widget.configure(state='disabled' if self.running else 'readonly')
        self.configure_hotkeys()

    def start(self):
        if self.closing or self.capture_target or self.running or (self.worker and self.worker.is_alive()): return
        self.stats=self.read_stats()
        self.refresh_stats()
        self.running=True
        self.stopping=self.has_error=False
        self.state_key='running'
        self.status.configure(text=self.tr(self.state_key),foreground='#0067c0')
        self.history=[]
        self.record('running')
        self.save_settings()
        self.set_controls()
        auto_bot.bot_running=True
        mode='phased' if self.strategy_choice.current()==1 else 'legacy'
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
                    self.refresh_stats()
                elif kind=='state' and not self.stopping:
                    self.state_key=values['state']
                    self.status.configure(text=self.tr(self.state_key))
                elif kind=='credit': self.record('credit',amount=values['amount'])
                elif kind=='failed': self.record('failed')
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
    HololiveBotUI(root)
    root.mainloop()

if __name__=='__main__': main()
