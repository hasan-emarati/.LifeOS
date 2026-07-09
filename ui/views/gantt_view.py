"""Gantt Chart View"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QRect, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath, QFont
from datetime import date, timedelta
from ui.theme import THEME
from core.jalali import to_jalali, format_jalali, today_jalali, JALALI_MONTHS

class GanttCanvas(QWidget):
    def __init__(self, tasks, start_date, total_days):
        super().__init__()
        self.tasks = tasks
        self.start_date = start_date
        self.total_days = max(total_days, 1)
        self.ROW_H = 44; self.LABEL_W = 200; self.HEADER_H = 52; self.DAY_W = 26
        w = self.LABEL_W + self.total_days * self.DAY_W + 20
        h = self.HEADER_H + len(tasks) * self.ROW_H + 20
        self.setMinimumSize(w, h)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.P_COLORS = {
            'critical': QColor(THEME['priority_critical']),
            'high':     QColor(THEME['priority_high']),
            'medium':   QColor(THEME['accent']),
            'low':      QColor(THEME['priority_low']),
        }

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(THEME['bg_secondary']))
        today = date.today()
        jtoday = today_jalali()

        # Header bg
        p.fillRect(0, 0, self.width(), self.HEADER_H, QColor(THEME['bg_tertiary']))
        p.setPen(QColor(THEME['text_secondary']))
        p.setFont(QFont("Segoe UI Variable", 10, QFont.Weight.Bold))
        p.drawText(QRect(0, 0, self.LABEL_W, self.HEADER_H), Qt.AlignmentFlag.AlignCenter, "تسک")
        p.drawLine(self.LABEL_W, 0, self.LABEL_W, self.height())

        for d in range(self.total_days):
            cur = self.start_date + timedelta(days=d)
            x = self.LABEL_W + d * self.DAY_W
            jy, jm, jd = to_jalali(cur.year, cur.month, cur.day)

            # امروز
            if cur == today:
                tc = QColor(THEME['accent']); tc.setAlpha(20)
                p.fillRect(x, 0, self.DAY_W, self.height(), tc)

            # آخر هفته (جمعه = weekday 4)
            if cur.weekday() == 4:
                wc = QColor(THEME['danger']); wc.setAlpha(12)
                p.fillRect(x, self.HEADER_H, self.DAY_W, self.height()-self.HEADER_H, wc)

            # روز شمسی
            p.setPen(QColor(THEME['accent_light'] if cur==today else THEME['text_tertiary']))
            p.setFont(QFont("Segoe UI Variable", 8, QFont.Weight.Bold if cur==today else QFont.Weight.Normal))
            p.drawText(QRect(x, 26, self.DAY_W, 24), Qt.AlignmentFlag.AlignCenter, str(jd))

            # ماه شمسی (اول هر ماه)
            if jd == 1 or d == 0:
                p.setPen(QColor(THEME['accent_light']))
                p.setFont(QFont("Segoe UI Variable", 8, QFont.Weight.Bold))
                p.drawText(QRect(x, 4, self.DAY_W*4, 20), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter, JALALI_MONTHS[jm-1][:3])

            # خطوط عمودی
            p.setPen(QPen(QColor(THEME['border_subtle'])))
            p.drawLine(x, self.HEADER_H, x, self.height())

        # Task rows
        for i, task in enumerate(self.tasks):
            y = self.HEADER_H + i * self.ROW_H
            row_bg = QColor(THEME['bg_hover'] if i%2==0 else THEME['bg_secondary'])
            p.fillRect(0, y, self.LABEL_W, self.ROW_H, row_bg)
            p.setPen(QColor(THEME['border_subtle']))
            p.drawLine(0, y+self.ROW_H-1, self.width(), y+self.ROW_H-1)
            p.setPen(QColor(THEME['text_primary']))
            p.setFont(QFont("Segoe UI Variable", 11))
            title = task.get('title','')
            if len(title) > 20: title = title[:19]+'…'
            p.drawText(QRect(6, y, self.LABEL_W-12, self.ROW_H), Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignRight, title)

            # Bar
            try:
                from datetime import date as _d
                ts = task.get('start_date') or task.get('created_at','')
                te = task.get('due_date','')
                t_start = _d.fromisoformat(ts[:10]) if ts else self.start_date
                t_end   = _d.fromisoformat(te[:10]) if te else t_start+timedelta(days=3)
            except Exception:
                t_start = self.start_date; t_end = self.start_date+timedelta(days=3)

            bx1 = max(0,(t_start-self.start_date).days)
            bx2 = min(self.total_days,(t_end-self.start_date).days+1)
            if bx2 > bx1:
                bx = self.LABEL_W+bx1*self.DAY_W+2
                bw = (bx2-bx1)*self.DAY_W-4
                by = y+8; bh = self.ROW_H-16
                color = self.P_COLORS.get(task.get('priority','medium'),QColor(THEME['accent']))
                is_done = task.get('status')=='done'
                color.setAlpha(255 if is_done else 180)
                grad = QLinearGradient(bx,by,bx+bw,by)
                lighter = QColor(color); lighter.setAlpha(min(255,color.alpha()+50))
                grad.setColorAt(0,lighter); grad.setColorAt(1,color)
                path = QPainterPath(); path.addRoundedRect(QRectF(bx,by,bw,bh),5,5)
                p.fillPath(path, QBrush(grad))
                if is_done:
                    p.setPen(QColor('white')); p.setFont(QFont("Segoe UI Emoji",10))
                    p.drawText(QRect(int(bx+4),int(by),20,int(bh)),Qt.AlignmentFlag.AlignVCenter,"✅")

        # Today line
        off = (today-self.start_date).days
        if 0 <= off < self.total_days:
            tx = self.LABEL_W+off*self.DAY_W+self.DAY_W//2
            pen = QPen(QColor(THEME['accent'])); pen.setWidth(2); pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen); p.drawLine(tx,self.HEADER_H,tx,self.height())
        p.end()

class GanttView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build(); self.refresh()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        toolbar = QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl = QHBoxLayout(toolbar); tl.setContentsMargins(20,0,20,0); tl.setSpacing(12)
        tl.addWidget(self._lbl("پروژه:"))
        self.proj_combo = QComboBox(); self.proj_combo.addItem("همه پروژه‌ها",None)
        self.proj_combo.currentIndexChanged.connect(self.refresh); tl.addWidget(self.proj_combo)
        tl.addWidget(self._lbl("بازه:"))
        self.range_combo = QComboBox()
        for v,n in [('30','۳۰ روز'),('60','۶۰ روز'),('90','۳ ماه'),('180','۶ ماه')]:
            self.range_combo.addItem(n,int(v))
        self.range_combo.setCurrentIndex(1); self.range_combo.currentIndexChanged.connect(self.refresh); tl.addWidget(self.range_combo)
        tl.addStretch()
        for color,label in [(THEME['priority_critical'],'بحرانی'),(THEME['priority_high'],'بالا'),(THEME['accent'],'متوسط'),(THEME['priority_low'],'پایین')]:
            dot=QLabel("●"); dot.setStyleSheet(f"color:{color};font-size:16px;background:transparent;border:none;")
            lb=QLabel(label); lb.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;background:transparent;border:none;")
            tl.addWidget(dot); tl.addWidget(lb)
        lay.addWidget(toolbar)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet(f"background:{THEME['bg_primary']};"); lay.addWidget(self.scroll)

    def _lbl(self, t):
        l=QLabel(t); l.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;background:transparent;border:none;"); return l

    def refresh(self):
        current_proj = self.proj_combo.currentData() if hasattr(self,'proj_combo') else None
        self.proj_combo.blockSignals(True); self.proj_combo.clear(); self.proj_combo.addItem("همه پروژه‌ها",None)
        for p in self.db.fetchall("SELECT id,name FROM projects WHERE archived=0 ORDER BY name"):
            self.proj_combo.addItem(p['name'],p['id'])
        idx=self.proj_combo.findData(current_proj)
        if idx>=0: self.proj_combo.setCurrentIndex(idx)
        self.proj_combo.blockSignals(False)
        proj_id = self.proj_combo.currentData(); num_days = self.range_combo.currentData() or 60
        if proj_id:
            tasks = self.db.fetchall("SELECT * FROM tasks WHERE project_id=? ORDER BY due_date",(proj_id,))
        else:
            tasks = self.db.fetchall("SELECT * FROM tasks WHERE due_date IS NOT NULL ORDER BY due_date LIMIT 60")
        start = date.today()-timedelta(days=7)
        if not tasks:
            empty=QLabel("📊 هیچ تسکی برای نمایش وجود ندارد.\nتسک‌هایی با مهلت مشخص اضافه کنید.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter); empty.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:15px;padding:80px;")
            self.scroll.setWidget(empty); return
        canvas = GanttCanvas(tasks, start, num_days); self.scroll.setWidget(canvas)
