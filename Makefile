# Prefix for installing lib... so we can use the same makefile for local
# installation and debian package creation.
ifndef DESTDIR
	# default: install in system root
	DESTDIR=
endif

# Are we building a debian package?
ifndef DEBIAN
	DEBIAN=0
endif

# Set the path to the Perl interpreter.
ifndef PERL
	PERL = /usr/bin/perl
endif

# Set the path to the Make interpreter.
ifndef MAKE
	MAKE = /usr/bin/make
endif

PYTHON_MODULES=*.py

all:
	@echo "Hello sweety!"

clean:
	rm -rf build *.pyc kpython.egg-info setup.py dist/
	cd perl && rm -rf Makefile blib pm_to_blib

build:
	cd perl && $(PERL) Makefile.PL INSTALLDIRS=vendor
	cd perl && $(MAKE) OPTIMIZE="-Wall -O2 -g"

install: build
	# Install programs.
	mkdir -p $(DESTDIR)/usr/bin/
	mkdir -p $(DESTDIR)/usr/sbin/
	install -m 755 -o root -g root kexecpg.py $(DESTDIR)/usr/bin/kexecpg
	install -m 755 -o root -g root kprocmonitor.py $(DESTDIR)/usr/bin/kprocmonitor
	install -m 755 -o root -g root kiniupdater.py $(DESTDIR)/usr/bin/kiniupdater
	install -m 755 -o root -g root kexternalrunner.py $(DESTDIR)/usr/bin/kexternalrunner
	install -m 755 -o root -g root perl/unblock_signals $(DESTDIR)/usr/bin/

	# Install Python modules.
	mkdir -p $(DESTDIR)/usr/share/python-support/kpython/
	for i in $(PYTHON_MODULES); do \
		if [ "$(DEBIAN)" = "0" -o "$(DEBIAN)" = "1" -a $$i != '__init__.py' ]; then\
			install -m644 $$i $(DESTDIR)/usr/share/python-support/kpython;\
		fi;\
	done

	# Install Perl module.
	cd perl && $(MAKE) install DESTDIR=$(DESTDIR) PREFIX=/usr

	# Update python modules if we're not building a debian package
	if [ "$(DEBIAN)" != "1" ]; then update-python-modules kpython; fi

setup_py:
    # Create a setup.py file using setup.py.tmpl file and set the version to the head HG rev.
	cat setup.py.tmpl | sed "s/__VERSION__/`hg head | head -1 | sed 's#changeset: *\([0-9]*\):.*#\1#g'`/g" > setup.py

egg: setup_py
    # Build the egg
	python setup.py bdist_egg


