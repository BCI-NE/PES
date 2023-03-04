#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "bsusb.h"
#include "parport/parport.h"

#define SNOWPLOUGH (256)

/*
long msec_elapsed(const struct timeval *old, const struct timeval *current)
{
    struct timeval _curr;
    if(!current) {
        gettimeofday(&_curr,NULL);
        current=&_curr;
    }
    return(
        (current->tv_sec  - old->tv_sec )*1000L + 
        (current->tv_usec - old->tv_usec)/1000L );
}

const char *ThroughputStr(int bytes,struct timeval *tv)
{
    long msec=msec_elapsed(tv,NULL);
    static char tmp[64];
    snprintf(tmp,64,"%d bytes in %.3f sec (%.3f kb/s)",
        bytes,
        (double)msec/1000.0,
        ((double)bytes*1000.0)/((double)msec*1024.0));
    return(tmp);
}

*/

void PrintUsage()
{
    fprintf(stderr, "usage: testusb [seed [length [blocks]]] \n");
    exit(1);
}

BYTE lcg(unsigned int *status)
{
    unsigned int s = *status;
    *status = s * 747796405;
    return (BYTE)((s & 0xFF) + ((s >> 8) & 0xFF) + \
        ((s >> 16) & 0xFF) + ((s >> 24) & 0xFF));
}

int main(int argc,char **argv)
{
    int rv, i;
    int length = 1, blocks = 1;
    unsigned int seed;
    BYTE *array;
    BYTE p;

    if (argc > 1) {
        seed = strtol(argv[1], NULL, 10);
        if (argc > 2) {
            length = strtol(argv[2], NULL, 10);
            if (argc > 3)
                blocks = strtol(argv[3], NULL, 10);
        }
    } else
        seed = 0x01020304; /* arbitrary value, 10 gets sent as first byte */
    if (length <= 0 || blocks <= 0)
        PrintUsage();
    
    rv = pp_init();
    if (rv) {
        fprintf(stderr, "Error opening the parallel port\n");
        return -1000 + rv;
    }
    rv = bsusb_init();
    if (rv)
        return rv;
    
    array = (BYTE *)malloc((SNOWPLOUGH > length ? SNOWPLOUGH : length) * sizeof(BYTE));
    if (!array)
        return -1000;
    printf("sending snowplough packet of %d '0' bytes\n", SNOWPLOUGH);
    memset(array, 0, SNOWPLOUGH);
    rv = bsusb_senda(array, SNOWPLOUGH);
    if (rv < 0)
        return rv;
    printf("sending %d bytes with seed %d\n[", length, seed);
    for (i = 0; i < length; ++i)
        array[i] = lcg(&seed);
    for (i = 0; i < (length < 5 ? length : 5); ++i)
        printf("%d,", array[i]);
    if (length > 10) {
        i = length - 5;
        printf("...,");
    }
    for (; i < length; ++i)
        printf("%d,", array[i]);
    printf("\b]\n");
    
    for (i = 0; i < blocks; ++i) {
        pp_out(0xff);
        /*rv = bsusb_read_pins(&p);
        if (rv < 0)
            return rv;*/
        rv = bsusb_senda(array, length);
        pp_out(0x00);
        if (rv < 0)
            return rv;
    }
    printf("%d bytes sent for each of %d blocks.\n", length, blocks);
    
    free(array);
    pp_release();
    rv = bsusb_close();
    if (rv)
        return rv;    
    return(0);
}
