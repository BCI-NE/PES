# Luca Citi
# University of Essex UK
# 20080704
# Library to interface the BioSemiUSBTrigger device

# Makefile
# under windows mingw + msys needed to build the project
# under linux libusb-dev needed
# to cross-compile for Win 64bit, install gcc-mingw-w64 and run
#       make OS=Win CC=x86_64-w64-mingw32-gcc -B
#
# useful info about shared libraries
# http://www.yolinux.com/TUTORIALS/LibraryArchives-StaticAndDynamic.html

CFLAGS = -Wall
CC = gcc
CP = cp
RM = rm -f
PYTHON = python
SDIR = src
ODIR = out

ifeq (, $(filter Win%, $(OS)))
	EXE =
	SHLIB = libbsusb.so
	CFLAGS += -fPIC
	LDFLAGS += -lusb
	LIBUSB =
else
	EXE = .exe
	SHLIB = libbsusb.dll
	PARPORTLIB = inpout32.dll
	CFLAGS += -I$(SDIR)/libusb-win32
	LIBUSB = $(ODIR)/libusb.o
endif

default: $(ODIR)/$(SHLIB) $(ODIR)/bsusb.py

all: $(ODIR)/$(SHLIB) $(ODIR)/test_no1$(EXE) $(ODIR)/test_no2$(EXE) $(ODIR)/test_no3$(EXE) $(ODIR)/$(PARPORTLIB) $(ODIR)/bsusb.py

$(ODIR)/test_no1.o: $(SDIR)/test_no1.c
	$(CC) $(CFLAGS) -c $^ -o $@

$(ODIR)/libusb.o: $(SDIR)/libusb-win32/libusb_dyn.c
	$(CC) $(CFLAGS) -c $^ -o $@

$(ODIR)/ftdi.o: $(SDIR)/libftdi/ftdi.c
	$(CC) $(CFLAGS) -c $^ -o $@

$(ODIR)/test_no1$(EXE): $(ODIR)/test_no1.o $(ODIR)/ftdi.o $(LIBUSB)
	$(CC) $(CFLAGS)  $^ $(LDFLAGS) -o $@

$(ODIR)/bsusb_MAKEDLL.o: $(SDIR)/bsusb.c
	$(CC) $(CFLAGS) -DMAKEDLL -c $^ -o $@

$(ODIR)/bsusb.o: $(SDIR)/bsusb.c
	$(CC) $(CFLAGS) -c $^ -o $@

$(ODIR)/libbsusb.so: $(ODIR)/ftdi.o $(ODIR)/bsusb.o
	$(CC) $(CFLAGS)  -Wl,-soname,libbsusb.so -shared $^ $(LDFLAGS) -o $@

$(ODIR)/libbsusb.dll: $(ODIR)/ftdi.o $(ODIR)/bsusb_MAKEDLL.o $(LIBUSB)
	$(CC) $(CFLAGS)  -shared $^ $(LDFLAGS) -o $@

$(ODIR)/test_no2.o: $(SDIR)/test_no2.c
	$(CC) $(CFLAGS) -c $^ -o $@

$(ODIR)/parport.o: $(SDIR)/parport/parport.c
	$(CC) $(CFLAGS) -c $^ -o $@

$(ODIR)/inpout32.dll: $(SDIR)/parport/inpout32.dll
	$(CP) $^ $@

$(ODIR)/test_no2$(EXE): $(ODIR)/test_no2.o $(ODIR)/parport.o $(ODIR)/$(SHLIB)
	$(CC) $(CFLAGS)  -Wl,-rpath,'$$ORIGIN' $^ $(LDFLAGS) -o $@

$(ODIR)/test_no3.o: $(SDIR)/test_no3.c
	$(CC) $(CFLAGS) -c $^ -o $@

$(ODIR)/test_no3$(EXE): $(ODIR)/test_no3.o $(LIBUSB)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

$(ODIR)/bsusb.py: $(SDIR)/bsusb.py
	-$(CP) $^ $@ ; \
	$(PYTHON) -c "" && $(PYTHON) $@


clean:
	$(RM) $(ODIR)/*.o $(ODIR)/*.py*
