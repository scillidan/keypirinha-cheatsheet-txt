<div align="center">
  <img src="assets/icon.png" alt="icon" width="32" />
</div>

# keypirinha-cheatsheet

Search cheatsheets liked keyboard shortcuts from `.conf` files.

Authors: GLM-5🧙‍♂️, scillidan🤡.

The icon is from [Input Prompts](https://www.kenney.nl/assets/input-prompts) by [Kenney](https://www.kenney.nl).

## Features

- Load contents from multiple directories and subdirectories
- Using space between words helps filtering stuffs
- Ignore custom files and dirs
- Three search modes: keyword, direct, all
- Other features

## Cheatsheet format

The format of the `.conf` files refers to [rofi-shortcuts.conf](https://github.com/Zeioth/rofi-shortcuts/blob/master/rofi-shortcuts.conf). So it can be used in both:

```
## https://chrisant996.github.io/clink/clink.html#gettingstarted_keybindings
clink: Help                 | A-h
clink: Clear the input line | Esc
...
```

## Usage

### Keyword Mode (default: `keyword_mode = true`)

Type `cheat` → Tab → `<query1> <query2> ...`

### Direct Mode (`keyword_mode = false`)

Type directly: `<query1> <query2> ...`

Items will be shown alongside other catalog items. Results are sorted by cache order (no custom weighting available in Keypirinha).
