# Makefile for Sphinx + Doxygen documentation

# You can set these variables from the command line
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build
DOXYGENDIR    = doxygen

# Put it first so that "make" without argument is like "make help"
help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  clean      to remove all build files"
	@echo "  doxygen    to run Doxygen and generate XML"
	@echo "  livehtml   to autobuild and serve docs locally"
	@echo "  test       to test the build locally"
	@echo "  view       to open the docs in browser"

.PHONY: help Makefile

# Run Doxygen to generate XML for Breathe
doxygen:
	@echo "Running Doxygen..."
	doxygen Doxyfile
	@echo "Doxygen XML generated in $(DOXYGENDIR)/xml/"

# Build HTML documentation (runs doxygen first)
html: doxygen
	@echo "Building HTML documentation..."
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html $(SPHINXOPTS)
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html/"

# Clean all build files
clean:
	@echo "Cleaning build files..."
	rm -rf $(BUILDDIR)/*
	rm -rf $(DOXYGENDIR)
	@echo "Clean complete."

# Clean and rebuild everything
rebuild: clean html

# Test the documentation build
test: clean html
	@echo "Testing documentation build..."
	@echo "Checking for broken links..."
	$(SPHINXBUILD) -b linkcheck $(SOURCEDIR) $(BUILDDIR)/linkcheck $(SPHINXOPTS)

# Open documentation in browser (Linux/Mac)
view:
	@if [ -f "$(BUILDDIR)/html/index.html" ]; then \
		echo "Opening documentation..."; \
		if command -v xdg-open > /dev/null; then \
			xdg-open $(BUILDDIR)/html/index.html; \
		elif command -v open > /dev/null; then \
			open $(BUILDDIR)/html/index.html; \
		else \
			echo "Please open $(BUILDDIR)/html/index.html in your browser"; \
		fi \
	else \
		echo "Documentation not built. Run 'make html' first."; \
	fi

# Install requirements
install:
	@echo "Installing documentation requirements..."
	pip install -r $(SOURCEDIR)/requirements.txt

# Serve documentation with live reload (requires sphinx-autobuild)
livehtml: doxygen
	@echo "Starting live documentation server..."
	@echo "Documentation will be available at http://127.0.0.1:8000"
	sphinx-autobuild $(SOURCEDIR) $(BUILDDIR)/html $(SPHINXOPTS)

# Catch-all target: route all unknown targets to Sphinx
%: Makefile
	@$(SPHINXBUILD) -M $@ $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)