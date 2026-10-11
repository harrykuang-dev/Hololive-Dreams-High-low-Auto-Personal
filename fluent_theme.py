"""Fluent-style surfaces rendered with native, keyboard-accessible ttk controls."""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk

BG, SURFACE, TEXT, MUTED = '#f5f5f5', '#ffffff', '#242424', '#616161'
ACCENT, HOVER, PRESSED = '#6d43aa', '#603b97', '#533282'
BORDER = '#d1d1d1'


class FluentTheme:
    def __init__(self, root, px):
        self.root, self.px, self.images = root, px, []
        self.style = ttk.Style(root)
        self.style.theme_use('clam')
        s = self.style
        s.configure('.', font=('Segoe UI',10), background=BG, foreground=TEXT)
        s.configure('TFrame', background=BG)
        s.configure('Surface.TFrame', background=SURFACE)
        s.configure('TLabel', background=BG, foreground=TEXT)
        s.configure('Muted.TLabel', foreground=MUTED)
        s.configure('Title.TLabel', font=('Segoe UI',18,'bold'))
        s.configure('Card.TLabel', background=SURFACE)
        s.configure('CardMuted.TLabel', background=SURFACE, foreground=MUTED)
        s.configure('Count.TLabel', background=SURFACE, font=('Segoe UI',20,'bold'))
        s.configure('Profit.TLabel', background=SURFACE, font=('Segoe UI',11))
        self.surface('Card', SURFACE, '#e5e5e5', 8, BG)
        s.layout('Card.TFrame', [('Card.border',dict(sticky='nswe'))])
        s.configure('Card.TFrame', background=SURFACE)
        for name,fill,border in (('Field',SURFACE,BORDER),('FocusField',SURFACE,ACCENT),
                                 ('DisabledField','#f0f0f0','#e5e5e5')):
            self.surface(name,fill,border,4)
            s.layout(name+'.TFrame',[(name+'.border',dict(sticky='nswe'))])
            s.configure(name+'.TFrame',background=SURFACE)
        self.button('Primary', ACCENT, HOVER, PRESSED, 'white')
        self.button('Secondary', SURFACE, '#f5f5f5', '#ebebeb', TEXT, BORDER)
        self.button('Subtle', BG, '#ebebeb', '#e0e0e0', MUTED)
        self.button('Info', SURFACE, '#f0ebf7', '#e4dcef', MUTED)
        s.configure('Subtle.TButton', padding=(px(8),px(2)))
        s.configure('Info.TButton', padding=0)
        self.help_icon=self.icon('help',MUTED,16)
        self.play_icons={key:self.icon('play',color,16) for key,color in
                         (('normal','white'),('disabled','#a0a0a0'))}
        self.stop_icons={key:self.icon('stop',color,16) for key,color in
                         (('normal','white'),('disabled','#a0a0a0'))}
        self.radio()
        self.combo()
        s.configure('Vertical.TScrollbar', background='#d6d6d6', troughcolor=SURFACE,
                    borderwidth=0, arrowsize=0, width=px(6), relief='flat')
        s.map('Vertical.TScrollbar', background=[('active','#adadad'),('pressed','#999999')])
        s.layout('Vertical.TScrollbar', [('Vertical.Scrollbar.trough',dict(sticky='ns',children=[
            ('Vertical.Scrollbar.thumb',dict(expand=True,sticky='nswe'))]))])

    def raster(self, size, painter):
        size=tuple(max(1,self.px(n)) for n in size)
        image=Image.new('RGBA',tuple(n*4 for n in size))
        painter(ImageDraw.Draw(image),image.size,4*self.px(1))
        image=image.resize(size,Image.Resampling.LANCZOS)
        photo=ImageTk.PhotoImage(image,master=self.root)
        self.images.append(photo)
        return photo

    def rounded(self, fill, border, radius, background, size=(240,48)):
        def paint(draw,size,unit):
            if background: draw.rectangle((0,0,*size),fill=background)
            draw.rounded_rectangle((unit/2,unit/2,size[0]-unit/2,size[1]-unit/2),
                                   radius=radius*unit,fill=fill,outline=border,width=unit)
        # ttk tiles the centre rather than stretching it. Large opaque tiles
        # avoid hundreds of small image copies during Windows live resizing.
        return self.raster(size,paint)

    def surface(self,name,fill,border,radius,background=None):
        photo=self.rounded(fill,border,radius,background or SURFACE,
                           (480,320) if name=='Card' else (320,48))
        self.style.element_create(name+'.border','image',photo,border=self.px(radius+2),
                                  width=self.px(2*radius+5),height=self.px(2*radius+5),sticky='nswe')

    def button(self,name,fill,hover,pressed,foreground,border=None):
        backdrop=SURFACE if name=='Info' else BG
        normal=self.rounded(fill,border or fill,6,backdrop)
        hot=self.rounded(hover,border or hover,6,backdrop)
        down=self.rounded(pressed,border or pressed,6,backdrop)
        disabled=self.rounded('#f0f0f0','#eeeeee',6,backdrop)
        focused=self.rounded(fill,ACCENT if name!='Primary' else '#45216f',6,backdrop)
        s=self.style
        s.element_create(name+'.button','image',normal,('disabled',disabled),('pressed',down),
                         ('active',hot),('focus',focused),border=self.px(6),
                         width=self.px(17),height=self.px(17),sticky='nswe')
        s.layout(name+'.TButton',[(name+'.button',dict(sticky='nswe',children=[
            ('Button.padding',dict(sticky='nswe',children=[('Button.label',dict(sticky='nswe'))]))]))])
        s.configure(name+'.TButton',foreground=foreground,background=backdrop,
                    lightcolor=backdrop,darkcolor=backdrop,bordercolor=backdrop,relief='flat',
                    padding=(self.px(10),self.px(5)),borderwidth=0,anchor='center',font=('Segoe UI',10))
        s.map(name+'.TButton',foreground=[('disabled','#a0a0a0')],
              background=[('disabled',backdrop),('pressed',backdrop),('active',backdrop)],
              lightcolor=[('disabled',backdrop),('pressed',backdrop),('active',backdrop)],
              darkcolor=[('disabled',backdrop),('pressed',backdrop),('active',backdrop)])

    def icon(self,kind,color,size):
        def paint(draw,dimensions,unit):
            w,h=dimensions
            if kind=='play':
                draw.polygon([(w*.25,h*.14),(w*.8,h*.5),(w*.25,h*.86)],fill=color)
            elif kind=='stop':
                draw.rounded_rectangle((w*.2,h*.2,w*.8,h*.8),radius=unit,fill=color)
            else:
                draw.ellipse((unit,unit,w-unit,h-unit),outline=color,width=unit)
                f=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',int(h*.72))
                draw.text((w*.5,h*.49),'?',font=f,fill=color,anchor='mm')
        return self.raster((size,size),paint)

    def radio(self):
        def indicator(selected=False,disabled=False):
            def paint(draw,size,unit):
                _,h=size
                w=h
                color='#bdbdbd' if disabled else ACCENT if selected else '#8a8a8a'
                draw.ellipse((unit,unit,w-unit,h-unit),fill=SURFACE,outline=color,
                             width=2*unit if selected else unit)
                if selected: draw.ellipse((w*.32,h*.32,w*.68,h*.68),fill=color)
            return self.raster((24,18),paint)
        off,on,disabled,disabled_on=indicator(),indicator(True),indicator(False,True),indicator(True,True)
        s=self.style
        s.element_create('Fluent.radio','image',off,('disabled','selected',disabled_on),
                         ('disabled',disabled),('selected',on),sticky='')
        s.layout('TRadiobutton',[('Radiobutton.padding',dict(sticky='nswe',children=[
            ('Fluent.radio',dict(side='left',sticky='')),
            ('Radiobutton.focus',dict(side='left',sticky='nswe',children=[
                ('Radiobutton.label',dict(sticky='nswe'))]))]))])
        s.configure('TRadiobutton',background=SURFACE,padding=(0,self.px(4)),
                    indicatormargin=(0,0,self.px(6),0))
        s.map('TRadiobutton',foreground=[('disabled','#a0a0a0')],background=[('active',SURFACE)])

    def combo(self):
        normal=self.rounded(SURFACE,BORDER,4,SURFACE,(320,48))
        focus=self.rounded(SURFACE,ACCENT,4,SURFACE,(320,48))
        def arrow(draw,size,unit):
            w,h=size
            draw.line([(w*.3,h*.4),(w*.5,h*.6),(w*.7,h*.4)],fill=MUTED,width=unit)
        arrow_image=self.raster((28,20),arrow)
        s=self.style
        s.element_create('Fluent.combo','image',normal,('focus',focus),border=self.px(6),
                         width=self.px(13),height=self.px(13),sticky='nswe')
        s.element_create('Fluent.downarrow','image',arrow_image,sticky='')
        s.layout('TCombobox',[('Fluent.combo',dict(sticky='nswe',children=[
            ('Fluent.downarrow',dict(side='right',sticky='ns')),
            ('Combobox.padding',dict(sticky='nswe',children=[('Combobox.textarea',dict(sticky='nswe'))]))]))])
        s.configure('TCombobox',padding=(self.px(8),self.px(2)),foreground=TEXT,
                    fieldbackground=SURFACE,borderwidth=0,selectbackground=SURFACE,selectforeground=TEXT)
        s.map('TCombobox',fieldbackground=[('readonly',SURFACE)],foreground=[('readonly',TEXT)],
              selectbackground=[('readonly',SURFACE)],selectforeground=[('readonly',TEXT)])
        s.configure('Compact.TCombobox',padding=(self.px(8),self.px(1)))


class Tooltip:
    def __init__(self,widget,text,px):
        self.widget,self.text,self.px=widget,text,px
        self.pending=self.window=None
        widget.bind('<Enter>',self.schedule,add='+')
        for event in ('<Leave>','<ButtonPress>','<KeyPress>','<Destroy>'):
            widget.bind(event,self.hide,add='+')

    def schedule(self,_event=None):
        self.hide()
        self.pending=self.widget.after(500,self.show)

    def show(self):
        self.pending=None
        if not self.widget.winfo_exists(): return
        self.window=tk.Toplevel(self.widget)
        self.window.overrideredirect(True)
        self.window.configure(bg=BORDER)
        ttk.Label(self.window,text=self.text(),style='Card.TLabel',padding=self.px(8)).pack(padx=1,pady=1)
        self.window.geometry(f'+{self.widget.winfo_rootx()}+{self.widget.winfo_rooty()+self.widget.winfo_height()+self.px(4)}')

    def hide(self,_event=None):
        if self.pending:
            self.widget.after_cancel(self.pending)
            self.pending=None
        if self.window:
            self.window.destroy()
            self.window=None
