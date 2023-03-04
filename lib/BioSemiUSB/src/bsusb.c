#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <stdlib.h>
#include <time.h>

#include "libftdi/ftdi.h"
#include "bsusb.h"

struct ftdi_context ctx;
int ctx_init = 0;

#define MAX_NUM_USB_BOXES 5
struct ftdi_context CTX[MAX_NUM_USB_BOXES];
int CTX_init[MAX_NUM_USB_BOXES];
int usb_dev_count = -4;
struct ftdi_device_list *usb_dev_list;

int Error(const char *where, int rv, struct ftdi_context *ctx, int doclose)
{
    fprintf(stderr, "%s: rv=%d, error=%s, errno=%s (%d)\n",
        where, rv, ctx->error_str, strerror(errno), errno);
    if ((errno == 1) && (rv == -8))
        fprintf(stderr, "Under Linux, a quick and dirti fix can be\nsudo chown -R username /dev/bus/usb/\n");
    if (doclose) {
        rv = ftdi_usb_close(ctx);
        fprintf(stderr, "close: rv=%d, error=%s, errno=%s (%d)\n",
            rv, ctx->error_str, strerror(errno), errno);
    }
    ftdi_deinit(ctx);
    ctx_init = 0;
    return rv;
}

DLL int bsusb_multiple_find() 
{
  usb_dev_count = ftdi_usb_find_all(NULL, &usb_dev_list, VENDOR, PRODUCT);
  if ( usb_dev_count < 0 ) 
    fprintf(stderr, "USB bus/device/memory problem\n");
  return usb_dev_count;
}

DLL int bsusb_multiple_init(int which_usb)
{
    int rv;
    int i; 
    struct ftdi_device_list *dev = usb_dev_list;

    if ( usb_dev_count <= 0 ) {
      fprintf(stderr, "bsusb_multiple_findall not called or no USB connected\n");
      return usb_dev_count;
    }
    
    if ( which_usb >= usb_dev_count ) {
      fprintf(stderr, "bsusb_multiple_init argument bigger than available number of USBs\n");
      return -1;
    }

    if (CTX_init[which_usb]) {
      fprintf(stderr, "WARNING: USB already open\n");
      return -1;
    }

    rv = ftdi_init( &(CTX[which_usb]) );
    if (rv)
      return Error("init", rv, &(CTX[which_usb]), 0);

    for ( i=0; i < which_usb; i ++)
      dev=dev->next;

    /* fprintf(stderr, "print %x\n",dev); */
    /* fflush(stderr); */

    rv = ftdi_usb_open_dev(&(CTX[which_usb]), dev->dev);
    if (rv)
        return Error("open", rv, &(CTX[which_usb]), 0);
    
    rv = ftdi_usb_reset(&(CTX[which_usb]));
    if (rv)
        return Error("reset", rv, &(CTX[which_usb]), 1);
    
    rv = ftdi_disable_bitbang(&(CTX[which_usb]));
    if (rv)
        return Error("bitbang(off)", rv, &(CTX[which_usb]), 1);
    
    CTX_init[which_usb] = 1;
    return 0;
}
    
DLL int bsusb_multiple_sendctl(int which_usb, int requesttype, int request, int value, int index)
{
    return usb_control_msg(CTX[which_usb].usb_dev, requesttype, request, value, index, NULL, 0, CTX[which_usb].usb_write_timeout);
}
    
DLL int bsusb_multiple_sendb(int which_usb, BYTE _byte)
{
  return bsusb_multiple_senda(which_usb,&_byte, 1); /* works only if little-endian */
}

DLL int bsusb_multiple_senda(int which_usb, void *arr, int arrsize)
{
    int rv;
    rv = ftdi_write_data(&(CTX[which_usb]), arr, arrsize);
    if (rv < 0)
        return Error("write", rv, &(CTX[which_usb]), 1);
    return rv;
}

DLL int bsusb_multiple_read_pins(int which_usb, BYTE *pins)
{
    int rv;
    rv = ftdi_read_pins(&(CTX[which_usb]), pins);
    if (rv < 0)
        return Error("read_pins", rv, &(CTX[which_usb]), 1);
    return rv;
}

DLL int bsusb_multiple_close(int which_usb)
{
    int rv;
    if (!CTX_init[which_usb])
        return -1;

    rv = ftdi_usb_close(&(CTX[which_usb]));
    if (rv)
        return Error("close", rv, &(CTX[which_usb]), 0);
    
    ftdi_deinit(&(CTX[which_usb]));
    
    return 0;
}

/* 
   OLD VERSION KEPT HERE FOR BACKWARD COMPATIBILITY
*/


DLL int bsusb_init()
{
    int rv;
    if (ctx_init)
        return -1;
    
    rv = ftdi_init(&ctx);
    if (rv)
        return Error("init", rv, &ctx, 0);
    
    rv = ftdi_usb_open(&ctx, VENDOR, PRODUCT);
    if (rv)
        return Error("open", rv, &ctx, 0);
    
    rv = ftdi_usb_reset(&ctx);
    if (rv)
        return Error("reset", rv, &ctx, 1);
    
    rv = ftdi_disable_bitbang(&ctx);
    if (rv)
        return Error("bitbang(off)", rv, &ctx, 1);
    
    ctx_init = 1;
    return 0;
}
    
DLL int bsusb_sendctl(int requesttype, int request, int value, int index)
{
    return usb_control_msg(ctx.usb_dev, requesttype, request, value, index, NULL, 0, ctx.usb_write_timeout);
}
    
DLL int bsusb_sendb(BYTE _byte)
{
    return bsusb_senda(&_byte, 1); /* works only if little-endian */
}

DLL int bsusb_senda(void *arr, int arrsize)
{
    int rv;
    rv = ftdi_write_data(&ctx, arr, arrsize);
    if (rv < 0)
        return Error("write", rv, &ctx, 1);
    return rv;
}

DLL int bsusb_read_pins(BYTE *pins)
{
    int rv;
    rv = ftdi_read_pins(&ctx, pins);
    if (rv < 0)
        return Error("read_pins", rv, &ctx, 1);
    return rv;
}

DLL int bsusb_close()
{
    int rv;
    if (!ctx_init)
        return -1;

    rv = ftdi_usb_close(&ctx);
    if (rv)
        return Error("close", rv, &ctx, 0);
    
    ftdi_deinit(&ctx);
    
    return 0;
}
