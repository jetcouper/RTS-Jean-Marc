        self.canevas.bind("<ButtonPress-1>", self.start_drag)
        self.canevas.bind("<B1-Motion>", self.do_drag)

    def start_drag(self, event):
        self.canevas.scan_mark(event.x, event.y)

    def do_drag(self, event):
        self.canevas.scan_dragto(event.x, event.y, gain=1)