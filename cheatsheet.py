import keypirinha as kp
import keypirinha_util as kpu
import os
import fnmatch
import ctypes


class Cheatsheet(kp.Plugin):
    ITEM_CAT_LINE = kp.ItemCategory.USER_BASE + 1

    def __init__(self):
        super().__init__()
        self._cache = []
        self._keyword = "cheat"
        self._keyword_mode = True
        self._comment_prefix = "##"
        self._max_desc_len = 50
        self._max_desc_percent = 0
        self._dirs = []
        self._patterns = ["*.conf"]
        self._ignores = []

    def on_start(self):
        self._read_config()
        self._build_cache()
        icon_handle = self.load_icon("res://Cheatsheet/assets/icon.ico")
        self.set_default_icon(icon_handle)

    def on_catalog(self):
        if self._keyword_mode:
            catalog = [
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=self._keyword,
                    short_desc="Search all cheatsheets",
                    target=self._keyword,
                    args_hint=kp.ItemArgsHint.ACCEPTED,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            ]
        else:
            catalog = [
                self.create_item(
                    category=self.ITEM_CAT_LINE,
                    label=f"{self._truncate(desc)} - {sc}",
                    short_desc="",
                    target=f"line:{sc}",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
                for desc, sc in self._cache
            ]
        self.set_catalog(catalog)

    def on_suggest(self, user_input, items_chain):
        if not self._keyword_mode:
            return

        if not items_chain or items_chain[0].target() != self._keyword:
            return

        query = user_input.strip().lower()
        words = [w for w in query.split() if w]

        matched = [
            (desc, sc) for desc, sc in self._cache if self._match_words(desc, sc, words)
        ]
        matched.sort(key=lambda x: x[0].lower())

        suggestions = [
            self.create_item(
                category=self.ITEM_CAT_LINE,
                label=f"{self._truncate(desc)} - {sc}",
                short_desc="",
                target=f"line:{sc}",
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                hit_hint=kp.ItemHitHint.IGNORE,
            )
            for desc, sc in matched
        ]
        self.set_suggestions(suggestions, kp.Match.DEFAULT, kp.Sort.NONE)

    def _truncate(self, text):
        if len(text) <= self._max_desc_len:
            return text
        return text[: self._max_desc_len - 3] + "..."

    def _match_words(self, desc, shortcut, words):
        if not words:
            return True
        text = (desc + " " + shortcut).lower()
        return all(w in text for w in words)

    def on_execute(self, item, action=None):
        if item.category() == self.ITEM_CAT_LINE:
            target = item.target()
            if target.startswith("line:"):
                text = target[5:]
                kpu.set_clipboard(text)

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self._read_config()
            self._build_cache()

    def _read_config(self):
        settings = self.load_settings()
        self._keyword = settings.get("keyword", "main", "cheat")
        self._keyword_mode = settings.get_bool("keyword_mode", "main", True)
        self._comment_prefix = settings.get("comment_prefix", "main", "##")
        max_desc_setting = settings.get("max_desc_len", "main", "50")
        if max_desc_setting.endswith("%"):
            self._max_desc_percent = float(max_desc_setting.rstrip("%"))
            self._max_desc_len = self._calc_desc_len(self._max_desc_percent)
        else:
            self._max_desc_percent = 0
            self._max_desc_len = int(max_desc_setting)
        self._dirs = []
        dirs_setting = settings.get("directories", "main", "")
        for p in dirs_setting.replace(";", "\n").split("\n"):
            p = p.strip()
            if p:
                p = os.path.expandvars(os.path.expanduser(p))
                if os.path.isdir(p):
                    self._dirs.append(p)
        patterns_setting = settings.get("patterns", "main", "*.conf")
        self._patterns = [
            p.strip() for p in patterns_setting.replace(";", "\n").split("\n") if p.strip()
        ]
        ignores_setting = settings.get("ignore", "main", "")
        self._ignores = [
            p.strip() for p in ignores_setting.replace(";", "\n").split("\n") if p.strip()
        ]

    def _calc_desc_len(self, percent):
        try:
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            char_width = 8
            return max(20, int(screen_width * percent / 100 / char_width))
        except Exception:
            return 50

    def _build_cache(self):
        self._cache = []
        for d in self._dirs:
            for f in self._get_conf_files(d):
                self._cache.extend(self._parse_file(f))
        self._cache.sort(key=lambda x: x[0].lower())

    def _parse_file(self, path):
        lines = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n\r")
                    if not line or line.startswith(self._comment_prefix):
                        continue
                    if line.startswith("#") and not line.startswith("##"):
                        continue
                    parts = line.split("|")
                    if len(parts) >= 2:
                        desc = parts[0].strip()
                        sc = parts[1].strip()
                        for p in parts[2:]:
                            sc += " | " + p.strip()
                        sc = (
                            sc.replace("\\t", "\t")
                            .replace("\\n", "\n")
                            .replace("\\r", "\r")
                            .replace("\\\\", "\\")
                        )
                        lines.append((desc, sc))
        except Exception:
            pass
        return lines

    def _get_conf_files(self, d):
        files = []
        try:
            for root, dirs, filenames in os.walk(d):
                dirs[:] = [dn for dn in dirs if not self._is_ignored(dn)]
                for fn in filenames:
                    if self._is_ignored(fn):
                        continue
                    if any(fnmatch.fnmatch(fn, p) for p in self._patterns):
                        files.append(os.path.join(root, fn))
        except Exception:
            pass
        return sorted(files)

    def _is_ignored(self, name):
        return any(fnmatch.fnmatch(name, p) for p in self._ignores)
