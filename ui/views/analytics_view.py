"""Analytics View v3 — نمودارها + خروجی CSV"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QFileDialog, QMessageBox,
    QGridLayout, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import date, timedelta
from ui.theme import THEME
from core.jalali import to_jalali, format_jalali

try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def dark_fig(w=8, h=3):
    fig = Figure(figsize=(w, h), facecolor=THEME['bg_secondary'])
    ax  = fig.add_subplot(111)
    ax.set_facecolor(THEME['bg_tertiary'])
    ax.tick_params(colors=THEME['text_secondary'], labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(THEME['border_default'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout(pad=1.8)
    return fig, ax


class ChartCard(QFrame):
    def __init__(self, title="", export_fn=None, height=220):
        super().__init__()
        self._height = height
        self.setStyleSheet(f"""
            QFrame {{
                background:{THEME['bg_secondary']};
                border:1px solid {THEME['border_subtle']};
                border-radius:14px;
            }}
        """)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(16, 14, 16, 14)
        self._lay.setSpacing(8)

        if title or export_fn:
            hdr = QHBoxLayout()
            if title:
                lbl = QLabel(title)
                lbl.setFont(QFont("Segoe UI Variable", 12, QFont.Weight.Bold))
                lbl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;")
                hdr.addWidget(lbl)
            hdr.addStretch()
            if export_fn:
                exp_btn = QPushButton("⬇ خروجی CSV")
                exp_btn.setFixedHeight(28)
                exp_btn.setStyleSheet(f"""
                    QPushButton{{background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};
                        border:1px solid {THEME['border_default']};border-radius:6px;
                        font-size:11px;padding:0 10px;}}
                    QPushButton:hover{{background:{THEME['accent']};color:white;}}
                """)
                exp_btn.clicked.connect(export_fn)
                hdr.addWidget(exp_btn)
            self._lay.addLayout(hdr)

        self._placeholder = QLabel("📊 در حال بارگذاری...")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(f"color:{THEME['text_tertiary']};background:transparent;border:none;font-size:13px;")
        self._placeholder.setFixedHeight(height)
        self._lay.addWidget(self._placeholder)

    def set_canvas(self, canvas, height=None):
        h = height or self._height
        self._lay.removeWidget(self._placeholder)
        self._placeholder.deleteLater()
        canvas.setFixedHeight(h)
        self._lay.addWidget(canvas)


class StatMini(QFrame):
    def __init__(self, icon, title, value, color, sub=""):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame{{background:{THEME['bg_secondary']};border:1px solid {THEME['border_subtle']};border-radius:12px;}}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(18,14,18,14); lay.setSpacing(6)
        ic = QLabel(icon); ic.setFont(QFont("Segoe UI Emoji",18))
        ic.setStyleSheet(f"background:{color}22;border-radius:8px;padding:6px;border:1px solid {color}44;")
        ic.setFixedSize(40,40); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ic)
        vl = QLabel(str(value)); vl.setFont(QFont("Segoe UI Variable",22,QFont.Weight.Bold))
        vl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;"); lay.addWidget(vl)
        tl = QLabel(title); tl.setFont(QFont("Segoe UI Variable",11))
        tl.setStyleSheet(f"color:{THEME['text_secondary']};background:transparent;border:none;"); lay.addWidget(tl)
        if sub:
            sl = QLabel(sub); sl.setFont(QFont("Segoe UI Variable",10))
            sl.setStyleSheet(f"color:{color};background:transparent;border:none;"); lay.addWidget(sl)


class AnalyticsView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        toolbar = QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl = QHBoxLayout(toolbar); tl.setContentsMargins(22,0,22,0); tl.setSpacing(12)
        tl.addWidget(self._lbl("دوره زمانی:"))
        self.period_combo = QComboBox()
        for v,n in [('7','۷ روز'),('30','۳۰ روز'),('90','۳ ماه'),('365','یک سال')]:
            self.period_combo.addItem(n,int(v))
        self.period_combo.setCurrentIndex(1)
        self.period_combo.currentIndexChanged.connect(self.refresh)
        tl.addWidget(self.period_combo); tl.addStretch()
        exp_all = QPushButton("⬇ خروجی کامل CSV")
        exp_all.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:6px 14px;font-size:12px;")
        exp_all.clicked.connect(self._export_all)
        tl.addWidget(exp_all)
        ref_btn = QPushButton("🔄 بروزرسانی"); ref_btn.clicked.connect(self.refresh); tl.addWidget(ref_btn)
        lay.addWidget(toolbar)

        self.tabs = QTabWidget(); lay.addWidget(self.tabs)

        for tab_key, tab_title in [('overview','📊 خلاصه'),('skills','⚡ مهارت‌ها'),('work','📋 گزارش کار')]:
            w = QWidget()
            scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content_lay = QVBoxLayout(content); content_lay.setContentsMargins(24,20,24,20); content_lay.setSpacing(18)
            scroll.setWidget(content)
            wl = QVBoxLayout(w); wl.setContentsMargins(0,0,0,0); wl.addWidget(scroll)
            setattr(self, f"_{tab_key}_content", content)
            setattr(self, f"_{tab_key}_layout", content_lay)
            self.tabs.addTab(w, tab_title)

    def _lbl(self, t):
        l = QLabel(t); l.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;background:transparent;border:none;"); return l

    def _clear(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _date_range(self, days):
        return [(date.today()-timedelta(days=i)).isoformat() for i in range(days-1,-1,-1)]

    def _jal_short(self, dates):
        result = []
        for d in dates:
            try:
                dd = date.fromisoformat(d); jy,jm,jd = to_jalali(dd.year,dd.month,dd.day)
                result.append(f"{jm}/{jd}")
            except Exception: result.append(d[5:])
        return result

    def refresh(self):
        days = self.period_combo.currentData() if hasattr(self,'period_combo') else 30
        self._draw_overview(days)
        self._draw_skills(days)
        self._draw_work(days)

    # ── Overview ─────────────────────────────────────
    def _draw_overview(self, days):
        lay = self._overview_layout; self._clear(lay)
        stats = self.db.fetchone("SELECT * FROM user_stats LIMIT 1") or {}
        td = self.db.fetchone("SELECT COUNT(*) as c FROM tasks WHERE status='done'") or {}
        hp = self.db.fetchone("SELECT COUNT(*) as c FROM habit_logs WHERE completed=1") or {}
        pd = self.db.fetchone("SELECT COUNT(*) as c FROM projects WHERE status='done'") or {}
        grid = QGridLayout(); grid.setSpacing(14)
        kpi = [
            ("⭐","کل XP",         f"{stats.get('total_xp',0):,}", THEME['xp_gold']),
            ("✅","تسک تکمیل",     td.get('c',0),                  THEME['success']),
            ("🔥","روز متوالی",    stats.get('streak_days',0),      THEME['streak_fire']),
            ("📚","ساعت مطالعه",   f"{stats.get('study_hours_total',0):.0f}h", THEME['info']),
            ("🏆","پروژه تکمیل",   pd.get('c',0),                  THEME['accent']),
            ("💪","عادت انجام",    hp.get('c',0),                  THEME['warning']),
        ]
        for i,(icon,title,val,color) in enumerate(kpi):
            grid.addWidget(StatMini(icon,title,val,color), 0, i%6)
        kw = QWidget(); kw.setLayout(grid); lay.addWidget(kw)
        self._add_chart(lay, "✅ تسک‌های تکمیل‌شده روزانه", days, self._task_data,
                        lambda: self._export_csv('tasks', days), 'bar', THEME['accent'])
        self._add_chart(lay, "😊 حال روزانه", days, self._mood_data,
                        lambda: self._export_csv('mood', days), 'line', THEME['success'])
        self._add_chart(lay, "📚 ساعات مطالعه", days, self._study_data,
                        lambda: self._export_csv('study', days), 'area', THEME['info'])
        self._add_chart(lay, "⭐ XP تجمعی", days, self._xp_data,
                        lambda: self._export_csv('xp', days), 'line', THEME['xp_gold'])
        lay.addStretch()

    def _add_chart(self, lay, title, days, data_fn, export_fn, chart_type, color):
        card = ChartCard(title, export_fn, 220)
        if HAS_MPL:
            dates, values = data_fn(days)
            fig, ax = dark_fig(8, 2.8)
            xs = range(len(values))
            short = self._jal_short(dates)
            step = max(1, len(short)//10)
            if chart_type == 'bar':
                ax.bar(xs, values, color=color+'bb', width=0.7, zorder=2)
            elif chart_type == 'line':
                fv = [v for v in values if v is not None]
                fx = [i for i,v in enumerate(values) if v is not None]
                if fx:
                    ax.plot(fx, fv, color=color, lw=2.2, marker='o', ms=4, zorder=3)
            elif chart_type == 'area':
                ax.fill_between(xs, values, alpha=0.3, color=color)
                ax.plot(xs, values, color=color, lw=2, zorder=3)
            ax.set_xticks(range(0,len(short),step))
            ax.set_xticklabels(short[::step], rotation=45, ha='right', color=THEME['text_secondary'])
            ax.grid(color=THEME['border_subtle'], alpha=0.5, zorder=1)
            canvas = FigureCanvas(fig); card.set_canvas(canvas, 220)
        lay.addWidget(card)

    def _task_data(self, days):
        dates = self._date_range(days)
        vals = [self.db.fetchone("SELECT COUNT(*) as c FROM tasks WHERE status='done' AND date(completed_at)=?",(d,))['c'] for d in dates]
        return dates, vals

    def _mood_data(self, days):
        dates = self._date_range(days)
        vals = []
        for d in dates:
            r = self.db.fetchone("SELECT mood FROM daily_reports WHERE date=?",(d,))
            vals.append(r['mood'] if r else None)
        return dates, vals

    def _study_data(self, days):
        dates = self._date_range(days)
        vals = [float(self.db.fetchone("SELECT study_hours FROM daily_reports WHERE date=?",(d,))['study_hours'] or 0) if self.db.fetchone("SELECT study_hours FROM daily_reports WHERE date=?",(d,)) else 0 for d in dates]
        return dates, vals

    def _xp_data(self, days):
        dates = self._date_range(days); cumulative = []; total = 0
        for d in dates:
            r = self.db.fetchone("SELECT SUM(amount) as s FROM xp_log WHERE date(earned_at)=?",(d,))
            total += float(r['s'] or 0) if r else 0; cumulative.append(total)
        return dates, cumulative

    # ── Skills ───────────────────────────────────────
    def _draw_skills(self, days):
        lay = self._skills_layout; self._clear(lay)
        skills = self.db.fetchall("SELECT * FROM skills ORDER BY total_hours DESC")
        if not skills:
            empty = QLabel("⚡ هنوز مهارتی ثبت نشده است."); empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:14px;padding:40px;"); lay.addWidget(empty); return

        card = ChartCard("⚡ سطح مهارت‌ها", lambda: self._export_skills(), 260)
        if HAS_MPL:
            names  = [s.get('name','')[:14] for s in skills[:12]]
            levels = [float(s.get('level',0)) for s in skills[:12]]
            colors_list = [s.get('color', THEME['accent']) for s in skills[:12]]
            fig, ax = dark_fig(8, max(3, len(names)*0.45))
            ys = range(len(names))
            bars = ax.barh(ys, levels, color=colors_list, alpha=0.85, height=0.6, zorder=2)
            ax.set_yticks(ys); ax.set_yticklabels(names, fontsize=9, color=THEME['text_secondary'])
            ax.set_xlim(0, 110)
            ax.set_xlabel("درصد", color=THEME['text_secondary'], fontsize=9)
            ax.axvline(100, color=THEME['text_tertiary'], lw=1, linestyle='--', alpha=0.5)
            for bar, level in zip(bars, levels):
                ax.text(min(level+2,105), bar.get_y()+bar.get_height()/2, f"{level:.0f}%", va='center', fontsize=8, color=THEME['text_primary'])
            ax.grid(axis='x', color=THEME['border_subtle'], alpha=0.4, zorder=1)
            canvas = FigureCanvas(fig); card.set_canvas(canvas, max(240, len(names)*38))
        lay.addWidget(card)

        card2 = ChartCard(f"⏱️ ساعت مهارت در {days} روز", lambda: self._export_skill_hours(days), 220)
        if HAS_MPL:
            sh = self.db.fetchall(f"SELECT s.name,s.color,SUM(we.duration_min)/60.0 as hours FROM work_entries we JOIN skills s ON we.skill_id=s.id WHERE we.report_date>=date('now','-{days} days') GROUP BY s.id ORDER BY hours DESC LIMIT 10")
            if sh:
                n2=[r.get('name','')[:14] for r in sh]; h2=[float(r.get('hours',0)) for r in sh]; c2=[r.get('color',THEME['accent']) for r in sh]
                fig2,ax2 = dark_fig(8,max(3,len(n2)*0.45))
                ax2.barh(range(len(n2)),h2,color=c2,alpha=0.85,height=0.6,zorder=2)
                ax2.set_yticks(range(len(n2))); ax2.set_yticklabels(n2,fontsize=9,color=THEME['text_secondary'])
                ax2.set_xlabel("ساعت",color=THEME['text_secondary'],fontsize=9)
                ax2.grid(axis='x',color=THEME['border_subtle'],alpha=0.4,zorder=1)
                canvas2 = FigureCanvas(fig2); card2.set_canvas(canvas2,max(200,len(n2)*38))
        lay.addWidget(card2); lay.addStretch()

    # ── Work ─────────────────────────────────────────
    def _draw_work(self, days):
        lay = self._work_layout; self._clear(lay)

        card = ChartCard(f"📋 کارکرد روزانه {days} روز (ساعت)", lambda: self._export_work(days), 220)
        if HAS_MPL:
            dates = self._date_range(days)
            wh = []
            for d in dates:
                r = self.db.fetchone("SELECT SUM(duration_min)/60.0 as h FROM work_entries WHERE report_date=?",(d,))
                wh.append(float(r['h'] or 0) if r else 0)
            fig,ax = dark_fig(8,2.8)
            ax.bar(range(len(wh)),wh,color=THEME['success']+'bb',width=0.7,zorder=2)
            short = self._jal_short(dates); step=max(1,len(short)//10)
            ax.set_xticks(range(0,len(short),step)); ax.set_xticklabels(short[::step],rotation=45,ha='right',color=THEME['text_secondary'])
            ax.set_ylabel("ساعت",color=THEME['text_secondary'],fontsize=9)
            ax.grid(axis='y',color=THEME['border_subtle'],alpha=0.5,zorder=1)
            canvas=FigureCanvas(fig); card.set_canvas(canvas,220)
        lay.addWidget(card)

        card2 = ChartCard("🎯 توزیع وقت به تفکیک دسته‌بندی", lambda: self._export_work_cats(days), 240)
        if HAS_MPL:
            cd = self.db.fetchall(f"SELECT wc.name,wc.color,SUM(we.duration_min)/60.0 as hours FROM work_entries we JOIN work_categories wc ON we.category=wc.name WHERE we.report_date>=date('now','-{days} days') GROUP BY we.category ORDER BY hours DESC")
            if cd:
                nc=[r.get('name','') for r in cd]; hc=[float(r.get('hours',0)) for r in cd]; cc=[r.get('color',THEME['accent']) for r in cd]
                fig2,ax2=dark_fig(7,3)
                wedges,texts,autotexts=ax2.pie(hc,labels=nc,colors=cc,autopct='%1.1f%%',startangle=90,textprops={'color':THEME['text_primary'],'fontsize':9},pctdistance=0.8)
                for at in autotexts: at.set_color(THEME['bg_primary']); at.set_fontsize(8)
                ax2.set_facecolor(THEME['bg_secondary'])
                canvas2=FigureCanvas(fig2); card2.set_canvas(canvas2,240)
        lay.addWidget(card2)

        card3 = ChartCard("🔥 هیت‌مپ عادت‌ها", lambda: self._export_habits(days), 180)
        if HAS_MPL:
            habits = self.db.fetchall("SELECT id,name FROM habits WHERE active=1 LIMIT 10")
            if habits:
                dl = self._date_range(min(days,30)); data=[]; lh=[]
                for h in habits:
                    row_data=[1 if self.db.fetchone("SELECT completed FROM habit_logs WHERE habit_id=? AND date=? AND completed=1",(h['id'],d)) else 0 for d in dl]
                    data.append(row_data); lh.append(h['name'][:12])
                fig3,ax3=dark_fig(8,max(2,len(habits)*0.4+0.5))
                arr=np.array(data); ax3.imshow(arr,aspect='auto',cmap='Greens',vmin=0,vmax=1,interpolation='nearest')
                ax3.set_yticks(range(len(lh))); ax3.set_yticklabels(lh,fontsize=8,color=THEME['text_secondary']); ax3.set_xticks([])
                canvas3=FigureCanvas(fig3); card3.set_canvas(canvas3,max(160,len(habits)*34))
        lay.addWidget(card3); lay.addStretch()

    # ── Export ───────────────────────────────────────
    def _get_path(self, name):
        path,_ = QFileDialog.getSaveFileName(self,"ذخیره فایل",name,"CSV Files (*.csv);;All Files (*)")
        return path

    def _export_all(self):
        path = self._get_path("lifeOS_full_export.csv")
        if not path: return
        try:
            import csv
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f)
                w.writerow(['=== تسک‌ها ===']); w.writerow(['عنوان','وضعیت','اولویت','مهلت','پروژه'])
                for t in self.db.fetchall("SELECT t.*,p.name as pn FROM tasks t LEFT JOIN projects p ON t.project_id=p.id"):
                    w.writerow([t.get('title',''),t.get('status',''),t.get('priority',''),t.get('due_date',''),t.get('pn','')])
                w.writerow([]); w.writerow(['=== گزارش کار ===']); w.writerow(['تاریخ','دسته','شروع','پایان','کارکرد(دقیقه)','شرح'])
                for e in self.db.fetchall("SELECT * FROM work_entries ORDER BY report_date,start_time"):
                    w.writerow([e.get('report_date',''),e.get('category',''),e.get('start_time',''),e.get('end_time',''),e.get('duration_min',0),e.get('description','')])
                w.writerow([]); w.writerow(['=== مهارت‌ها ===']); w.writerow(['نام','دسته','سطح(%)','ساعت انجام','ساعت استاد'])
                for s in self.db.fetchall("SELECT * FROM skills ORDER BY level DESC"):
                    w.writerow([s.get('name',''),s.get('category',''),s.get('level',0),s.get('total_hours',0),s.get('mastery_hours',0)])
            self._ok(f"خروجی در {path} ذخیره شد.")
        except Exception as ex: self._err(str(ex))

    def _export_csv(self, section, days):
        path = self._get_path(f"{section}_{days}days.csv")
        if not path: return
        try:
            import csv; dates = self._date_range(days)
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f)
                if section=='tasks':
                    w.writerow(['تاریخ','تعداد تسک تکمیل‌شده'])
                    for d in dates:
                        r=self.db.fetchone("SELECT COUNT(*) as c FROM tasks WHERE status='done' AND date(completed_at)=?",(d,))
                        w.writerow([d,r['c'] if r else 0])
                elif section=='mood':
                    w.writerow(['تاریخ','حال','انرژی'])
                    for d in dates:
                        r=self.db.fetchone("SELECT mood,energy FROM daily_reports WHERE date=?",(d,))
                        w.writerow([d,r['mood'] if r else '',r['energy'] if r else ''])
                elif section=='study':
                    w.writerow(['تاریخ','ساعت مطالعه'])
                    for d in dates:
                        r=self.db.fetchone("SELECT study_hours FROM daily_reports WHERE date=?",(d,))
                        w.writerow([d,r['study_hours'] if r else 0])
                elif section=='xp':
                    w.writerow(['تاریخ','XP کسب‌شده'])
                    for d in dates:
                        r=self.db.fetchone("SELECT SUM(amount) as s FROM xp_log WHERE date(earned_at)=?",(d,))
                        w.writerow([d,r['s'] if r else 0])
            self._ok(f"خروجی در {path} ذخیره شد.")
        except Exception as ex: self._err(str(ex))

    def _export_skills(self):
        path = self._get_path("skills.csv")
        if not path: return
        try:
            import csv
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f); w.writerow(['نام','دسته','سطح(%)','ساعت انجام','ساعت استاد'])
                for s in self.db.fetchall("SELECT * FROM skills ORDER BY level DESC"):
                    w.writerow([s.get('name',''),s.get('category',''),s.get('level',0),s.get('total_hours',0),s.get('mastery_hours',0)])
            self._ok(f"خروجی در {path} ذخیره شد.")
        except Exception as ex: self._err(str(ex))

    def _export_skill_hours(self, days):
        path = self._get_path(f"skill_hours_{days}days.csv")
        if not path: return
        try:
            import csv
            data=self.db.fetchall(f"SELECT s.name,SUM(we.duration_min)/60.0 as hours FROM work_entries we JOIN skills s ON we.skill_id=s.id WHERE we.report_date>=date('now','-{days} days') GROUP BY s.id ORDER BY hours DESC")
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f); w.writerow(['مهارت',f'ساعت در {days} روز'])
                for r in data: w.writerow([r.get('name',''),f"{r.get('hours',0):.2f}"])
            self._ok(f"خروجی در {path} ذخیره شد.")
        except Exception as ex: self._err(str(ex))

    def _export_work(self, days):
        path = self._get_path(f"work_{days}days.csv")
        if not path: return
        try:
            import csv
            entries=self.db.fetchall(f"SELECT * FROM work_entries WHERE report_date>=date('now','-{days} days') ORDER BY report_date,start_time")
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f); w.writerow(['#','تاریخ','دسته','شروع','پایان','کارکرد','شرح'])
                for i,e in enumerate(entries,1):
                    dm=int(e.get('duration_min',0)); h,m=divmod(dm,60)
                    w.writerow([i,e.get('report_date',''),e.get('category',''),e.get('start_time',''),e.get('end_time',''),f"{h:02d}:{m:02d}",e.get('description','')])
            self._ok(f"خروجی در {path} ذخیره شد.")
        except Exception as ex: self._err(str(ex))

    def _export_work_cats(self, days):
        path = self._get_path(f"work_cats_{days}days.csv")
        if not path: return
        try:
            import csv
            data=self.db.fetchall(f"SELECT category,SUM(duration_min)/60.0 as hours FROM work_entries WHERE report_date>=date('now','-{days} days') GROUP BY category ORDER BY hours DESC")
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f); w.writerow(['دسته‌بندی','ساعت'])
                for r in data: w.writerow([r.get('category',''),f"{r.get('hours',0):.2f}"])
            self._ok(f"خروجی در {path} ذخیره شد.")
        except Exception as ex: self._err(str(ex))

    def _export_habits(self, days):
        path = self._get_path(f"habits_{days}days.csv")
        if not path: return
        try:
            import csv; habits=self.db.fetchall("SELECT id,name FROM habits WHERE active=1"); dates=self._date_range(days)
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f); w.writerow(['تاریخ']+[h['name'] for h in habits])
                for d in dates:
                    row_data=[d]
                    for h in habits:
                        r=self.db.fetchone("SELECT completed FROM habit_logs WHERE habit_id=? AND date=?",(h['id'],d))
                        row_data.append('✓' if (r and r.get('completed')) else '')
                    w.writerow(row_data)
            self._ok(f"خروجی در {path} ذخیره شد.")
        except Exception as ex: self._err(str(ex))

    def _ok(self, msg):
        m=QMessageBox(self); m.setWindowTitle("✅ خروجی موفق"); m.setText(msg)
        m.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};"); m.exec()

    def _err(self, msg):
        m=QMessageBox(self); m.setWindowTitle("❌ خطا"); m.setText(f"خطا:\n{msg}")
        m.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};"); m.exec()
