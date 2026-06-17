import keypirinha as kp
import keypirinha_util as kpu
import os
import re
import fnmatch
import ctypes


class CheatsheetTxt(kp.Plugin):
    DEFAULT_KEYWORD = "cht"
    DEFAULT_COMMENT_PREFIXES = ["#", "##"]
    DEFAULT_MAX_DESC_LEN = "20%"
    DEFAULT_INCLUDE = ["*.conf", "*.cht"]
    ITEM_CAT_LINE = kp.ItemCategory.USER_BASE + 1

    def __init__(self):
        super().__init__()
        self._cache = []
        self._keyword = self.DEFAULT_KEYWORD
        self._comment_prefixes = list(self.DEFAULT_COMMENT_PREFIXES)
        self._max_desc_len = 0
        self._max_desc_len_raw = str(self.DEFAULT_MAX_DESC_LEN)
        self._files = []
        self._directories = []
        self._include = list(self.DEFAULT_INCLUDE)
        self._exclude = []
        self._notify = True
        self._icon_handle = None

    def on_start(self):
        self._read_config()
        self._build_cache()
        self._icon_handle = self.load_icon("res://CheatsheetTxt/assets/icon.ico")
        self.set_default_icon(self._icon_handle)

    def on_stop(self):
        pass

    def on_reload(self):
        self._read_config()
        self._build_cache()
        if not self._icon_handle:
            self._icon_handle = self.load_icon("res://CheatsheetTxt/assets/icon.ico")
            self.set_default_icon(self._icon_handle)

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self.on_reload()

    def _semicolons(self, raw):
        if not isinstance(raw, str):
            return []
        return [x.strip() for x in raw.replace("\n", ";").split(";") if x.strip()]

    def _read_config(self):
        settings = self.load_settings()

        self._keyword = settings.get_stripped(
            "keyword", "main", self.DEFAULT_KEYWORD).lower()

        cp_raw = self._semicolons(settings.get("comment_prefix", "main", ""))
        self._comment_prefixes = cp_raw if cp_raw else list(self.DEFAULT_COMMENT_PREFIXES)

        self._max_desc_len = settings.get_int("max_desc_len", "main", 0)
        self._max_desc_len_raw = settings.get_stripped(
            "max_desc_len", "main", str(self.DEFAULT_MAX_DESC_LEN))

        files_raw = settings.get("files", "main", "")
        self._files = [
            os.path.expandvars(os.path.expanduser(x.strip().rstrip(";")))
            for x in self._semicolons(files_raw)
        ]

        self._directories = [
            os.path.expandvars(os.path.expanduser(x.strip().rstrip(";")))
            for x in self._semicolons(settings.get("directories", "main", ""))
        ]

        self._include = self._semicolons(settings.get("include", "main", "")) or list(self.DEFAULT_INCLUDE)
        self._exclude = self._semicolons(settings.get("exclude", "main", ""))

        self._notify = settings.get_bool("notify", "main", True)

    def _fnmatch_exclude(self, filepath, patterns):
        if not patterns:
            return False
        fp_fwd = os.path.normpath(filepath).lower().replace("\\", "/")
        fname = os.path.basename(fp_fwd)
        for pat in patterns:
            pl = pat.strip().lower()
            if not pl:
                continue
            if pl.endswith("/"):
                dn = pl.rstrip("/")
                for part in fp_fwd.split("/"):
                    if part == dn:
                        return True
            else:
                if fnmatch.fnmatch(fname, pl):
                    return True
        return False

    def _is_excluded(self, filepath):
        return self._fnmatch_exclude(filepath, self._exclude)

    def _is_included(self, filename):
        if not self._include:
            return True
        fl = filename.lower()
        return any(fnmatch.fnmatch(fl, p.lower()) for p in self._include)

    def _is_comment(self, line):
        for prefix in self._comment_prefixes:
            if line.startswith(prefix):
                return True
        return False

    def _build_cache(self):
        self._cache = []
        seen = set()

        for fpath in self._files:
            norm = os.path.normpath(fpath).lower()
            if norm in seen:
                continue
            seen.add(norm)
            if os.path.isfile(fpath):
                self._cache.extend(self._parse_file(fpath))

        for dir_path in self._directories:
            if not os.path.isdir(dir_path):
                continue
            for fpath in self._get_conf_files(dir_path):
                norm = os.path.normpath(fpath).lower()
                if norm in seen:
                    continue
                seen.add(norm)
                self._cache.extend(self._parse_file(fpath))

    def _parse_file(self, path):
        lines = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n\r")
                    if not line or self._is_comment(line):
                        continue
                    parsed = self._parse_line(line)
                    if parsed:
                        lines.append(parsed)
        except Exception as e:
            self.err(f"Failed to read {path}: {e}")
        return lines

    def _parse_line(self, line):
        parts = re.split(r'(?<!\\)\|', line, maxsplit=1)
        if len(parts) < 2:
            return None
        desc = parts[0].strip()
        sc = parts[1].strip()
        return (desc, sc)

    def _get_conf_files(self, d):
        files = []
        try:
            for root, dirs, filenames in os.walk(d):
                dirs[:] = [dn for dn in dirs if not self._is_dir_excluded(dn)]
                for fn in filenames:
                    if self._is_excluded(os.path.join(root, fn)):
                        continue
                    if self._is_included(fn):
                        files.append(os.path.join(root, fn))
        except Exception as e:
            self.err(f"Failed to scan {d}: {e}")
        return sorted(files)

    def _is_dir_excluded(self, dirname):
        for pat in self._exclude:
            pl = pat.strip().lower()
            if pl.endswith("/"):
                if dirname.lower() == pl.rstrip("/"):
                    return True
        return False

    def _calc_max_desc_len(self):
        raw = self._max_desc_len_raw.strip()
        if raw.endswith('%'):
            try:
                pct = float(raw[:-1].strip())
                sw = ctypes.windll.user32.GetSystemMetrics(0)
                return max(20, int(sw * pct / 100 / 8))
            except Exception:
                return 50
        elif self._max_desc_len > 0:
            return self._max_desc_len
        return 50

    def _truncate(self, text):
        ml = self._calc_max_desc_len()
        if len(text) <= ml:
            return text
        return text[:ml - 3] + "..."

    def on_suggest(self, user_input, items_chain):
        text = user_input.strip()
        if not text.lower().startswith(self._keyword):
            return

        args = text[len(self._keyword):].strip()
        if not args:
            return

        words = [w.lower() for w in args.split() if w]
        suggestions = []
        for desc, sc in self._cache:
            searchable = (desc + " " + sc).lower()
            if all(w in searchable for w in words):
                suggestions.append(self._make_item(desc, sc))
        if suggestions:
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
        else:
            self.set_suggestions([self.create_error_item(
                label="No cheats found",
                short_desc=f"Search: {args}"
            )])

    def _make_item(self, desc, sc):
        return self.create_item(
            category=self.ITEM_CAT_LINE,
            label=f"{self._truncate(desc)} - {sc}",
            short_desc="",
            target=f"line:{sc}",
            args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.KEEPALL,
            icon_handle=self._icon_handle
        )

    def on_execute(self, item, action=None):
        if item.category() != self.ITEM_CAT_LINE:
            return
        target = item.target()
        if target.startswith("line:"):
            text = target[5:]
            kpu.set_clipboard(text)
            if self._notify:
                kpu.show_notification(f"Copied: {text}")
