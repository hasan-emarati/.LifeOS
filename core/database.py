"""
Database Manager - SQLite — نسخه ۲ با جدول‌های جدید
"""
import sqlite3, os
from typing import Optional, List, Dict

DB_PATH = os.path.join(os.path.expanduser("~"), ".lifeOS", "lifeOS.db")


class DatabaseManager:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA journal_mode = WAL")
        return self._conn

    def execute(self, sql: str, params=()) -> sqlite3.Cursor:
        conn = self.get_connection()
        cur  = conn.execute(sql, params)
        conn.commit()
        return cur

    def fetchall(self, sql: str, params=()) -> List[Dict]:
        conn = self.get_connection()
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def fetchone(self, sql: str, params=()) -> Optional[Dict]:
        conn = self.get_connection()
        row  = conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def initialize(self):
        conn = self.get_connection()
        stmts = [
            # ── Projects ──────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'general',
                status TEXT DEFAULT 'planning',
                priority TEXT DEFAULT 'medium',
                progress INTEGER DEFAULT 0,
                start_date TEXT,
                end_date TEXT,
                budget REAL DEFAULT 0,
                spent REAL DEFAULT 0,
                work_hours REAL DEFAULT 0,
                color TEXT DEFAULT '#6366f1',
                icon TEXT DEFAULT '📁',
                archived INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )""",

            # ── Tasks ─────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                parent_id  INTEGER REFERENCES tasks(id)   ON DELETE CASCADE,
                title       TEXT NOT NULL,
                description TEXT,
                status      TEXT DEFAULT 'todo',
                priority    TEXT DEFAULT 'medium',
                assignee    TEXT,
                estimated_hours REAL DEFAULT 0,
                actual_hours    REAL DEFAULT 0,
                weight      INTEGER DEFAULT 1,
                due_date    TEXT,
                start_date  TEXT,
                completed_at TEXT,
                tags        TEXT DEFAULT '',
                xp_reward   INTEGER DEFAULT 10,
                progress    INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now')),
                updated_at  TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS task_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id    INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                depends_on INTEGER REFERENCES tasks(id) ON DELETE CASCADE
            )""",

            # ── Goals ─────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT,
                category    TEXT DEFAULT 'personal',
                timeframe   TEXT DEFAULT 'yearly',
                priority    TEXT DEFAULT 'high',
                status      TEXT DEFAULT 'active',
                progress    INTEGER DEFAULT 0,
                target_date TEXT,
                reason      TEXT,
                value       TEXT,
                xp_reward   INTEGER DEFAULT 50,
                created_at  TEXT DEFAULT (datetime('now'))
            )""",

            # دسته‌بندی‌های اهداف قابل تعریف توسط کاربر
            """CREATE TABLE IF NOT EXISTS goal_categories (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#6366f1',
                icon  TEXT DEFAULT '🎯'
            )""",

            # ── Habits ────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                description TEXT,
                category    TEXT DEFAULT 'health',
                icon        TEXT DEFAULT '⭐',
                color       TEXT DEFAULT '#10b981',
                frequency   TEXT DEFAULT 'daily',
                xp_reward   INTEGER DEFAULT 10,
                active      INTEGER DEFAULT 1,
                created_at  TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS habit_logs (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER REFERENCES habits(id) ON DELETE CASCADE,
                date     TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                notes    TEXT,
                logged_at TEXT DEFAULT (datetime('now'))
            )""",

            # ── Skills ────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS skills (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                category    TEXT DEFAULT 'technical',
                level       REAL DEFAULT 0,
                mastery_hours REAL DEFAULT 0,
                total_hours   REAL DEFAULT 0,
                description TEXT,
                parent_id   INTEGER REFERENCES skills(id),
                color       TEXT DEFAULT '#8b5cf6',
                created_at  TEXT DEFAULT (datetime('now'))
            )""",

            # ── Notes ─────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS notes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                content    TEXT,
                category   TEXT DEFAULT 'general',
                tags       TEXT DEFAULT '',
                project_id INTEGER REFERENCES projects(id),
                skill_id   INTEGER REFERENCES skills(id),
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )""",

            # ── Ideas ─────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS ideas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT,
                category    TEXT DEFAULT 'general',
                status      TEXT DEFAULT 'raw',
                priority    TEXT DEFAULT 'medium',
                tags        TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now'))
            )""",

            # ── Daily Reports ─────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date      TEXT NOT NULL UNIQUE,
                mood      INTEGER DEFAULT 5,
                energy    INTEGER DEFAULT 5,
                summary   TEXT,
                wins      TEXT,
                challenges TEXT,
                learnings  TEXT,
                tomorrow_plan TEXT,
                workout_done  INTEGER DEFAULT 0,
                workout_details TEXT,
                study_hours   REAL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )""",

            # ردیف‌های ساعتی گزارش کار (جدید)
            """CREATE TABLE IF NOT EXISTS work_entries (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                category    TEXT NOT NULL,
                start_time  TEXT NOT NULL,
                end_time    TEXT NOT NULL,
                duration_min REAL DEFAULT 0,
                description TEXT,
                skill_id    INTEGER REFERENCES skills(id),
                project_id  INTEGER REFERENCES projects(id),
                created_at  TEXT DEFAULT (datetime('now'))
            )""",

            # دسته‌بندی‌های گزارش کار
            """CREATE TABLE IF NOT EXISTS work_categories (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#6366f1',
                icon  TEXT DEFAULT '💼'
            )""",

            # ── Time Tracking ─────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS time_entries (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id  INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                project_id INTEGER REFERENCES projects(id),
                skill_id   INTEGER REFERENCES skills(id),
                description TEXT,
                start_time  TEXT,
                end_time    TEXT,
                duration_minutes REAL DEFAULT 0,
                is_pomodoro INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now'))
            )""",

            # ── Risks ─────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS risks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                title      TEXT NOT NULL,
                description TEXT,
                probability TEXT DEFAULT 'medium',
                impact      TEXT DEFAULT 'medium',
                mitigation  TEXT,
                status      TEXT DEFAULT 'open',
                created_at  TEXT DEFAULT (datetime('now'))
            )""",

            # ── Events / Calendar ─────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT,
                event_type  TEXT DEFAULT 'meeting',
                start_datetime TEXT,
                end_datetime   TEXT,
                project_id  INTEGER REFERENCES projects(id),
                reminder_minutes INTEGER DEFAULT 15,
                color       TEXT DEFAULT '#6366f1',
                created_at  TEXT DEFAULT (datetime('now'))
            )""",

            # ── Finance ───────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS bank_accounts (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL,
                bank    TEXT,
                balance REAL DEFAULT 0,
                color   TEXT DEFAULT '#10b981',
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS finance_categories (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT NOT NULL UNIQUE,
                type  TEXT DEFAULT 'expense',
                color TEXT DEFAULT '#ef4444',
                icon  TEXT DEFAULT '💸'
            )""",

            """CREATE TABLE IF NOT EXISTS finance_entries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id  INTEGER REFERENCES bank_accounts(id),
                project_id  INTEGER REFERENCES projects(id),
                category_id INTEGER REFERENCES finance_categories(id),
                type        TEXT DEFAULT 'expense',
                amount      REAL DEFAULT 0,
                description TEXT,
                payee       TEXT,
                date        TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            )""",

            # بدهی به افراد
            """CREATE TABLE IF NOT EXISTS payroll (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                person     TEXT NOT NULL,
                role       TEXT,
                amount     REAL DEFAULT 0,
                period     TEXT DEFAULT 'monthly',
                paid       INTEGER DEFAULT 0,
                due_date   TEXT,
                project_id INTEGER REFERENCES projects(id),
                notes      TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            # ── Gamification ──────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS user_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_xp       INTEGER DEFAULT 0,
                level          INTEGER DEFAULT 1,
                streak_days    INTEGER DEFAULT 0,
                last_active_date TEXT,
                tasks_completed  INTEGER DEFAULT 0,
                habits_completed INTEGER DEFAULT 0,
                projects_completed INTEGER DEFAULT 0,
                study_hours_total  REAL DEFAULT 0,
                updated_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS xp_log (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                amount   INTEGER DEFAULT 0,
                reason   TEXT,
                earned_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS achievements (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                key         TEXT UNIQUE,
                title       TEXT,
                description TEXT,
                icon        TEXT DEFAULT '🏆',
                xp_reward   INTEGER DEFAULT 100,
                unlocked    INTEGER DEFAULT 0,
                unlocked_at TEXT
            )""",

            # ── App settings ──────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )""",
        ]

        for sql in stmts:
            try:
                conn.execute(sql)
            except Exception as e:
                print(f"[DB] {e}")
        conn.commit()
        self._migrate()
        self._seed_defaults()

    def _migrate(self):
        """Add missing columns to existing databases (safe ALTER TABLE)"""
        migrations = [
            # ── tasks ──────────────────────────────────
            ("tasks", "weight",           "INTEGER DEFAULT 1"),
            ("tasks", "progress",         "INTEGER DEFAULT 0"),
            ("tasks", "project_id",       "INTEGER"),
            ("tasks", "parent_id",        "INTEGER"),
            ("tasks", "assignee",         "TEXT"),
            ("tasks", "actual_hours",     "REAL DEFAULT 0"),
            ("tasks", "estimated_hours",  "REAL DEFAULT 0"),
            ("tasks", "start_date",       "TEXT"),
            ("tasks", "completed_at",     "TEXT"),
            ("tasks", "tags",             "TEXT DEFAULT ''"),
            ("tasks", "xp_reward",        "INTEGER DEFAULT 10"),
            ("tasks", "updated_at",       "TEXT"),
            # ── projects ───────────────────────────────
            ("projects", "work_hours",    "REAL DEFAULT 0"),
            ("projects", "description",   "TEXT"),
            ("projects", "category",      "TEXT DEFAULT 'general'"),
            ("projects", "start_date",    "TEXT"),
            ("projects", "end_date",      "TEXT"),
            ("projects", "budget",        "REAL DEFAULT 0"),
            ("projects", "spent",         "REAL DEFAULT 0"),
            ("projects", "color",         "TEXT DEFAULT '#6366f1'"),
            ("projects", "icon",          "TEXT DEFAULT '📁'"),
            ("projects", "archived",      "INTEGER DEFAULT 0"),
            ("projects", "updated_at",    "TEXT"),
            # ── skills ─────────────────────────────────
            ("skills", "mastery_hours",   "REAL DEFAULT 0"),
            ("skills", "total_hours",     "REAL DEFAULT 0"),
            ("skills", "category",        "TEXT DEFAULT 'technical'"),
            ("skills", "color",           "TEXT DEFAULT '#8b5cf6'"),
            ("skills", "parent_id",       "INTEGER"),
            ("skills", "description",     "TEXT"),
            # ── user_stats ──────────────────────────────
            ("user_stats", "tasks_completed",    "INTEGER DEFAULT 0"),
            ("user_stats", "habits_completed",   "INTEGER DEFAULT 0"),
            ("user_stats", "projects_completed", "INTEGER DEFAULT 0"),
            ("user_stats", "study_hours_total",  "REAL DEFAULT 0"),
            ("user_stats", "last_active_date",   "TEXT"),
            ("user_stats", "updated_at",         "TEXT"),
            # ── time_entries ────────────────────────────
            ("time_entries", "skill_id",  "INTEGER"),
            ("time_entries", "project_id","INTEGER"),
            # ── notes ───────────────────────────────────
            ("notes", "project_id",       "INTEGER"),
            ("notes", "skill_id",         "INTEGER"),
            ("notes", "tags",             "TEXT DEFAULT ''"),
            ("notes", "updated_at",       "TEXT"),
            # ── goals ───────────────────────────────────
            ("goals", "reason",           "TEXT"),
            ("goals", "value",            "TEXT"),
            ("goals", "xp_reward",        "INTEGER DEFAULT 50"),
            # ── habits ──────────────────────────────────
            ("habits", "description",     "TEXT"),
            ("habits", "category",        "TEXT DEFAULT 'health'"),
            ("habits", "icon",            "TEXT DEFAULT '⭐'"),
            ("habits", "color",           "TEXT DEFAULT '#10b981'"),
            ("habits", "xp_reward",       "INTEGER DEFAULT 10"),
            ("habits", "active",          "INTEGER DEFAULT 1"),
            # ── work_categories ─────────────────────────
            ("work_categories", "color",  "TEXT DEFAULT '#6366f1'"),
            ("work_categories", "icon",   "TEXT DEFAULT '💼'"),
            # ── tasks: تسک روزانه ────────────────────────
            ("tasks", "is_daily",         "INTEGER DEFAULT 0"),
            # ── tasks: ساعت مشخص + آلارم ─────────────────
            ("tasks", "due_time",         "TEXT"),
            ("tasks", "alarm_enabled",    "INTEGER DEFAULT 0"),
            ("tasks", "alarm_notified",   "INTEGER DEFAULT 0"),
            # ── events: آلارم تقویم ──────────────────────
            ("events", "notified",        "INTEGER DEFAULT 0"),
            ("events", "alarm_enabled",   "INTEGER DEFAULT 1"),
        ]
        conn = self.get_connection()
        for table, column, col_def in migrations:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
                conn.commit()
            except Exception:
                pass  # column already exists

        # Ensure new tables exist (work_entries, work_categories, bank_accounts, etc.)
        new_tables = [
            """CREATE TABLE IF NOT EXISTS work_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                category TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_min REAL DEFAULT 0,
                description TEXT,
                skill_id INTEGER,
                project_id INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            )""",
            """CREATE TABLE IF NOT EXISTS work_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#6366f1',
                icon TEXT DEFAULT '💼'
            )""",
            """CREATE TABLE IF NOT EXISTS bank_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                bank TEXT,
                balance REAL DEFAULT 0,
                color TEXT DEFAULT '#10b981',
                created_at TEXT DEFAULT (datetime('now'))
            )""",
            """CREATE TABLE IF NOT EXISTS finance_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT DEFAULT 'expense',
                color TEXT DEFAULT '#ef4444',
                icon TEXT DEFAULT '💸'
            )""",
            """CREATE TABLE IF NOT EXISTS goal_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#6366f1',
                icon TEXT DEFAULT '🎯'
            )""",
            """CREATE TABLE IF NOT EXISTS payroll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person TEXT NOT NULL,
                role TEXT,
                amount REAL DEFAULT 0,
                period TEXT DEFAULT 'monthly',
                paid INTEGER DEFAULT 0,
                due_date TEXT,
                project_id INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",
            """CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )""",
            # چک‌لیست روزانه‌ی تسک‌های تکرارشونده (مثل habit_logs ولی برای تسک‌ها)
            """CREATE TABLE IF NOT EXISTS daily_task_logs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id   INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                date      TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                logged_at TEXT DEFAULT (datetime('now')),
                UNIQUE(task_id, date)
            )""",
        ]
        for sql in new_tables:
            try:
                conn.execute(sql)
            except Exception:
                pass
        conn.commit()

    def _seed_defaults(self):
        # user_stats
        if not self.fetchone("SELECT id FROM user_stats LIMIT 1"):
            self.execute("INSERT INTO user_stats (total_xp,level,streak_days) VALUES (0,1,0)")

        # goal_categories
        default_goal_cats = [
            ('شخصی','#ec4899','👤'),('حرفه‌ای','#6366f1','💼'),
            ('سلامتی','#10b981','❤️'),('مالی','#f59e0b','💰'),
            ('یادگیری','#8b5cf6','📚'),('روابط','#f97316','🤝'),
        ]
        for name, color, icon in default_goal_cats:
            try:
                self.execute(
                    "INSERT OR IGNORE INTO goal_categories (name,color,icon) VALUES (?,?,?)",
                    (name, color, icon)
                )
            except Exception:
                pass

        # work_categories
        default_work_cats = [
            ('دانشگاه','#6366f1','🎓'),('پروژه','#10b981','💻'),
            ('مطالعه','#f59e0b','📚'),('ورزش','#ef4444','🏋️'),
            ('جلسه','#3b82f6','🤝'),('شخصی','#8b5cf6','👤'),
        ]
        for name, color, icon in default_work_cats:
            try:
                self.execute(
                    "INSERT OR IGNORE INTO work_categories (name,color,icon) VALUES (?,?,?)",
                    (name, color, icon)
                )
            except Exception:
                pass

        # finance_categories
        default_finance_cats = [
            ('حقوق','income','#10b981','💰'),
            ('فریلنس','income','#22c55e','💻'),
            ('سرمایه‌گذاری','income','#f59e0b','📈'),
            ('مسکن','expense','#ef4444','🏠'),
            ('خوراک','expense','#f97316','🍔'),
            ('حمل و نقل','expense','#3b82f6','🚗'),
            ('آموزش','expense','#8b5cf6','📚'),
            ('سخت‌افزار','expense','#6366f1','🖥️'),
            ('نرم‌افزار','expense','#a78bfa','💾'),
            ('سایر','expense','#64748b','📦'),
        ]
        for name, ftype, color, icon in default_finance_cats:
            try:
                self.execute(
                    "INSERT OR IGNORE INTO finance_categories (name,type,color,icon) VALUES (?,?,?,?)",
                    (name, ftype, color, icon)
                )
            except Exception:
                pass

        # achievements
        achs = [
            ('first_task','اولین قدم','اولین تسک را تکمیل کردید','🎯',50),
            ('streak_7','هفت روز پیاپی','۷ روز متوالی فعال بودید','🔥',100),
            ('streak_30','قهرمان عادت','۳۰ روز متوالی فعال بودید','🏆',500),
            ('tasks_10','کارآمد','۱۰ تسک تکمیل کردید','⚡',100),
            ('tasks_100','ماشین تولید','۱۰۰ تسک تکمیل کردید','🚀',1000),
            ('study_100h','دانش‌آموز متعهد','۱۰۰ ساعت مطالعه','📚',500),
            ('project_done','پروژه‌باز','اولین پروژه را تکمیل کردید','✅',200),
            ('skill_50','نیمه‌راه','یک مهارت به ۵۰٪ رسید','⭐',150),
            ('skill_100','استاد','یک مهارت به ۱۰۰٪ رسید','🎓',1000),
        ]
        for key,title,desc,icon,xp in achs:
            try:
                self.execute(
                    "INSERT OR IGNORE INTO achievements (key,title,description,icon,xp_reward) VALUES (?,?,?,?,?)",
                    (key,title,desc,icon,xp)
                )
            except Exception:
                pass

        # تنظیمات پیش‌فرض
        defaults = [('theme','dark'),('font_size','13'),('accent','#7c3aed')]
        for k,v in defaults:
            try:
                self.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)",(k,v))
            except Exception:
                pass

    def get_setting(self, key: str, default: str = '') -> str:
        row = self.fetchone("SELECT value FROM settings WHERE key=?", (key,))
        return row['value'] if row else default

    def set_setting(self, key: str, value: str):
        self.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))

    def reset_all_data(self):
        """پاک کردن تمام داده‌ها (نگه‌داشتن ساختار)"""
        tables = [
            'xp_log','achievements','user_stats','payroll','finance_entries',
            'finance_categories','bank_accounts','events','risks','time_entries',
            'work_entries','work_categories','daily_reports','ideas','notes',
            'skills','habit_logs','habits','goal_categories','goals',
            'daily_task_logs','task_dependencies','tasks','projects','settings',
        ]
        for t in tables:
            try:
                self.execute(f"DELETE FROM {t}")
            except Exception:
                pass
        self._seed_defaults()
