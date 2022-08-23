# ----------------------------------------------------------------------------
# Copyright 2021 Noah Rahm
#
# This file includes code that was modified from wxPySTC_DocMap
# which is licensed under the MIT License
# Copyright (c) 2020 Thom Snoeren
# ----------------------------------------------------------------------------


import keyword

import wx
import wx.stc as stc


class DragZone:
    def __init__(self):
        self.bmp = None
        self.pos = (0, 0)

    def Contains(self, pt):
        return self.GetRect().Contains(pt)

    def GetRect(self):
        return wx.Rect(self.pos, self.bmp.Size)

    def Draw(self, dc):
        self.SetTransparency(0x80)
        dc.DrawBitmap(self.bmp, self.GetRect()[:2])

    def SetTransparency(self, alpha=0x80):
        img = self.bmp.ConvertToImage()
        if not img.HasAlpha():
            img.InitAlpha()
            for x in range(img.Width):
                for y in range(img.Height):
                    img.SetAlpha(x, y, alpha)
            self.bmp = img.ConvertToBitmap()

    def Create(self, size):
        # limit zone size
        min_size = 1
        size = (max(min_size, size[0]), max(min_size, size[1]))

        # prepare memory bitmap for drawing
        mdc = wx.MemoryDC()
        self.bmp = wx.Bitmap(size)
        mdc.SelectObject(self.bmp)
        mdc.Clear()

        # zone surface
        mdc.SetPen(wx.TRANSPARENT_PEN)
        mdc.SetBrush(wx.Brush('#5D5D5D'))
        mdc.DrawRectangle(0, 0, *size)

        # zone line, centered
        x, _, w, h = self.GetRect()
        mid = h // 2
        left = (x, mid)
        right = (w, mid)
        mdc.SetPen(wx.Pen('#fff', 1, wx.PENSTYLE_DOT))
        mdc.DrawLine(left, right)

        # zone dot, centered
        mdc.SetPen(wx.Pen('#fff', 1))
        mdc.SetBrush(wx.Brush('#fff', wx.BRUSHSTYLE_TRANSPARENT))
        mdc.DrawCircle(w // 2, mid, 2)

        mdc.SelectObject(wx.NullBitmap)


class EditorTheme(object):
    """ This is meant to be used as an inherited class to
    theme a wx.styledtextctrl widget. """

    def Styling(self, doc):
        doc.SetLexer(stc.STC_LEX_PYTHON)
        doc.SetKeyWords(0, " ".join(keyword.kwlist))

        doc.SetProperty("fold", "1")
        doc.SetProperty("tab.timmy.whinge.level", "1")

        doc.SetMargins(10, 20)

        doc.SetViewWhiteSpace(False)
        doc.SetUseAntiAliasing(True)

        doc.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'face:Consolas,size:14')
        doc.StyleSetBackground(stc.STC_STYLE_DEFAULT, '#272822')
        doc.StyleClearAll()  # reset all styles to default

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:Consolas,size:14")
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,  "back:#C0C0C0,face:Consolas,size:14")
        self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:Consolas")
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,  "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,    "fore:#000000,back:#FF0000,bold")

        # Python styles

        # Default
        self.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#ffffff,face:Consolas,size:14")
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#75715e,face:Consolas,size:14")
        # Number
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#8c7bed,size:14")
        # String
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#e6db74,face:Consolas,size:14")
        # Single quoted string
        self.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#e6db74,face:Consolas,size:14")
        # Keyword
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#ed2a68,bold,size:14")
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#e6db74,size:14")
        # Triple double quotes
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#e6db74,size:14")
        # Class name definition
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#8aca27,bold,size:14")
        # Function or method name definition
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#8aca27,bold,size:14")
        # Decorator
        self.StyleSetSpec(stc.STC_P_DECORATOR, "fore:#3cbbd3,bold,size:14")
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#ffffff,bold,size:14")
        # Identifiers
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#ffffff,face:Consolas,size:14")
        # Comment-blocks
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#7F7F7F,size:14")
        # End of line where string is not closed
        self.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#464646,face:Consolas,back:#ffffff,eol,size:14")

        # Caret
        self.SetCaretForeground("#fff")


class DocumentMap(stc.StyledTextCtrl, EditorTheme):
    def __init__(self, parent, doc, **kwargs):
        super(DocumentMap, self).__init__(parent, style=wx.BORDER_NONE)
        self.parent = parent
        self.doc = doc

        # create reference from map to document
        self.doc.AddRefDocument(self.doc.DocPointer)
        self.SetDocPointer(self.doc.DocPointer)

        self.zone = DragZone()
        self.hotspot = (0, 0)

        self.InitSTC()

        self.parent.Bind(wx.EVT_SIZE, self.Size)
        self.doc.Bind(stc.EVT_STC_UPDATEUI, self.DocPosChanged)
        self.doc.Bind(stc.EVT_STC_ZOOM, lambda e: self.Refresh())
        self.Bind(stc.EVT_STC_PAINTED, self.Paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.LeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.LeftUp)
        self.Bind(wx.EVT_MOTION, self.Motion)
        # disable map text selection and mouse wheel
        self.Bind(wx.EVT_LEFT_DCLICK, lambda e: e.Skip)
        self.Bind(wx.EVT_MOUSEWHEEL, lambda e: e.SetWheelRotation(0))

    def InitSTC(self):
        self.SetZoom(-10)
        self.SetExtraAscent(0)
        self.SetExtraDescent(-1)

        self.SetDoubleBuffered(True)  # ensure smooth zone drawing
        self.UsePopUp(False)  # disable popup menu

        mlh = False  # marker line background colour
        self.SetMarginWidth(0, 0)
        self.SetMarginWidth(1, 0 if mlh else 1)
        self.SetMarginWidth(2, 0)
        self.SetIndentationGuides(stc.STC_IV_NONE)

        # no scrollbars
        self.SetUseHorizontalScrollBar(False)
        self.SetUseVerticalScrollBar(False)
        self.SetScrollWidthTracking(False)

        # hide caret
        self.SetCaretWidth(0)
        self.SetReadOnly(True)
        self.doc.SetReadOnly(False)

        self.Styling(self)

    def Size(self, evt):
        self.SetSize(self.parent.Size)
        self.RefreshZone()
        # keep zone inside map
        x, y, _, h = self.zone.GetRect()
        if y + h > self.ClientSize[1] - self.TextHeight(0):
            self.SetFirstVisibleLine(self.FirstVisibleLine + 1)
            self.zone.pos = (x, y - self.TextHeight(0))
        self.Refresh()

    def Paint(self, evt):
        dc = wx.PaintDC(self)
        self.RefreshZone()
        self.zone.Draw(dc)

    def LeftDown(self, evt):
        pos = evt.Position
        # If drag zone was 'hit', then set that as the shape we're going to
        # drag around. Get our start position. Dragging has not yet started.
        if self.zone.Contains(pos):
            self.dragStartPos = pos
            self.hotspot = self.dragStartPos - self.zone.pos
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            # prevent interfering with drag
            self.doc.Bind(stc.EVT_STC_UPDATEUI, None)
            return

        # center drag zone around clicked line
        self.CalcHeights()
        clicked_line = self.FirstVisibleLine - (self.zone_height // 2 - pos[1]) // self.TextHeight(0)
        top_y = clicked_line * self.GetDocScrollRatio()
        top_y = min(top_y, self.scroll_height)
        top_line = self.GetTopLine(top_y)
        self.SyncDoc(top_line, top_y)
        self.SyncMap(top_line, top_y)

    def LeftUp(self, evt):
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        self.doc.Bind(stc.EVT_STC_UPDATEUI, self.DocPosChanged)

    def Motion(self, evt):
        # Ignore mouse movement if we're not dragging.
        if not evt.Dragging() or not evt.LeftIsDown():
            return

        self.CalcHeights()
        top_y = self.GetTopY(evt.Position[1])

        # align position with drag start
        pos = (self.dragStartPos[0], top_y + self.hotspot[1])
        top_line = self.GetTopLine(top_y)
        self.SyncDoc(top_line, top_y)
        self.SetFirstVisibleLine(top_line)  # in document map

        # adjust mouse pointer position
        self.WarpPointer(*pos)
        self.zone.pos = (0, top_y)

    def DocPosChanged(self, evt):
        # copy text selection to map
        self.SetSelection(*self.doc.GetSelection())

        self.CalcHeights()
        top_y = self.doc.FirstVisibleLine * self.GetDocScrollRatio()
        top_line = self.GetTopLine(top_y) + 1
        self.SyncMap(top_line, top_y)

    def CalcHeights(self):
        # calculate document map height values
        txt_height = self.LineCount * self.TextHeight(0)
        self.clt_height = self.ClientSize[1]
        self.max_height = min(txt_height, self.clt_height)
        self.zone_height = self.zone.GetRect()[3]
        self.scroll_height = max(.1, self.max_height - self.zone_height)

    def GetDocScrollRatio(self):
        ratio = self.doc.LineCount - self.doc.LinesOnScreen()
        # prevent division by zero
        if ratio == 0:
            ratio = -1
        return self.scroll_height / ratio

    def GetTopLine(self, top_y):
        top_line = top_y / self.scroll_height * (self.LineCount - self.LinesOnScreen())
        return round(top_line)

    def GetTopY(self, posY):
        # drag zone's top Y coordinate
        top_y = posY - self.hotspot[1]
        # adjust when mouse released past top/bottom edge
        top_y = max(top_y, 0)
        top_y = min(top_y, self.scroll_height)
        return top_y

    def RefreshZone(self):
        self.zone.Create((self.ClientSize[0], self.doc.LinesOnScreen() * self.TextHeight(0)))

    def SyncDoc(self, top_line, top_y):
        if self.max_height < self.clt_height:
            top_line = 0

        self.doc.SetFirstVisibleLine(round(top_line + top_y // self.TextHeight(0)))

    def SyncMap(self, top_line, top_y):
        # adjust map top line
        if top_line == 1:
            top_line = 0
        self.SetFirstVisibleLine(top_line)
        self.zone.pos = (0, round(top_y))


class DocumentEditor(stc.StyledTextCtrl, EditorTheme):
    def __init__(self, parent):
        super(DocumentEditor, self).__init__(parent, style=wx.BORDER_NONE)
        self.parent = parent
        self.InitSTC()
        self.parent.Bind(wx.EVT_SIZE, self.Size)

    def InitSTC(self):
        self.SetMarginType(0, stc.STC_MARGIN_NUMBER)  # 0: LINE numbers
        self.SetMarginWidth(0, 50)
        self.SetMarginType(3, stc.STC_MARGIN_TEXT)    # 3: LEFT
        self.SetMarginLeft(4)
        self.SetSelForeground(True, '#E0E2E4')
        self.SetSelBackground(True, '#2F393C')
        self.SetUseTabs(False)
        self.SetTabWidth(4)

        self.Styling(self)

    def Size(self, evt):
        self.SetSize(self.parent.Size)


if __name__ == '__main__':
    app = wx.App(redirect=False)
    frm = wx.Frame(None, title="", pos=(0, 0), size=(500, 1024))
    frm.Maximize()

    spl = wx.SplitterWindow(frm, style=wx.SP_NOBORDER | wx.SP_LIVE_UPDATE)
    spl.SetSashInvisible()
    pn1 = wx.Panel(spl, style=wx.NO_BORDER)
    pn2 = wx.Panel(spl, style=wx.NO_BORDER)
    spl.SplitVertically(pn1, pn2, -220)

    doc = DocumentEditor(pn1)
    doc.LoadFile('test.py')
    dcm = DocumentMap(pn2, doc)

    frm.Show()
    app.MainLoop()
