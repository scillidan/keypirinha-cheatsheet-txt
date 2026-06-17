PACKAGE_NAME = CheatsheetTxt
VERSION = 0.1.0
DIST_DIR = dist
FILES = cheatsheettxt.py cheatsheettxt.ini README.md LICENSE assets/icon.ico

.PHONY: all clean dist

all: dist

dist:
	@mkdir -p $(DIST_DIR)
	7z a -tzip "$(DIST_DIR)/$(PACKAGE_NAME).keypirinha-package" $(FILES)

clean:
	@rm -rf $(DIST_DIR)

info:
	@echo "Package: $(PACKAGE_NAME)"
	@echo "Version: $(VERSION)"
	@echo "Files: $(FILES)"
