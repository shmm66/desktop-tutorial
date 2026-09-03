import tkinter as tk
from TraderPlannerPro_v3 import App as BaseApp, APP, DB, date, save

class App(BaseApp):
    def __init__(self):
        tk.Tk.__init__(self)
        # Fix v3 startup crash: BaseApp.__init__ called self.title(), which is
        # overridden by the v3 page-heading method before self.content existed.
        tk.Tk.title(self, APP)
        self.geometry('1500x940')
        self.minsize(1180,760)
        self.cur='home'
        self.market=DB.get('market','Forex')
        self.day=date.today().isoformat()
        self.vars=[]
        self.apply_theme()
        self.shell()
        self.show('home')
        self.after(1000,self.clock)

if __name__=='__main__':
    App().mainloop()
