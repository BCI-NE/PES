/* simple.c

   Simple libftdi usage example

   This program is distributed under the GPL, version 2
*/

#include <stdio.h>
#include <ftdi.h>

int main(int argc, char **argv)
{
    int ret;
    struct ftdi_context ftdic;
    ftdi_init(&ftdic);

    if((ret = ftdi_usb_open(&ftdic, 0x0403, 0x6001)) < 0) {
        fprintf(stderr, "unable to open ftdi device: %d (%s)\n", ret, ftdi_get_error_string(&ftdic));
        return EXIT_FAILURE;
    }

    // Read out FTDIChip-ID of R type chips
    if (ftdic.type == TYPE_R) {
        unsigned int chipid;
        printf("ftdi_read_chipid: %d\n", ftdi_read_chipid(&ftdic, &chipid));
        printf("FTDI chipid: %X\n", chipid);
    }

    ftdi_usb_close(&ftdic);
    ftdi_deinit(&ftdic);

    return EXIT_SUCCESS;
}

