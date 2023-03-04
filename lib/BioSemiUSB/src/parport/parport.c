#include "parport.h"

/* Tools to access the parallel port
Under linux:
    /dev/parport is used,
under windows:
    inpout32.dll from
    http://logix4u.net/inpout32_source_and_bins.zip
    is uded
*/

#ifdef WIN32
#define PARPORT (pp_tryaudodetect())
#else
#define PARPORT ("/dev/parport0")
#endif


#ifdef WIN32

#include <windows.h>

typedef void _stdcall (*oupfuncPtr)(short portaddr, short datum);
typedef short _stdcall (*inpfuncPtr)(short portaddr);
oupfuncPtr g_Out32;
inpfuncPtr g_Inp32;
HINSTANCE g_hLib = NULL;
short g_Port;

short pp_tryaudodetect()
{
    if (!g_hLib)
        return 0;
    short possib[] = {0x278, 0x378, 0x3BC};
    unsigned int i;
    for(i = 0; i < (sizeof(possib)/sizeof(short)); ++i) {
        short v = g_Inp32(possib[i] + 1);
        if(v != 255) {
            g_Out32(possib[i] + 1, v ^ 0xFF);
            if(g_Inp32(possib[i] + 1) == v) {
                v = g_Inp32(possib[i]);
                g_Out32(possib[i], v ^ 0xFF);
                if(g_Inp32(possib[i]) == (v ^ 0xFF))
                    return possib[i];
            }
        }
    }
    return 0;
}

int pp_init()
{
    g_hLib = LoadLibrary("inpout32.dll");
    if (g_hLib == NULL)
        return -1;
    g_Out32 = (oupfuncPtr)GetProcAddress(g_hLib, "Out32");
    g_Inp32 = (inpfuncPtr)GetProcAddress(g_hLib, "Inp32");
    if (g_Out32 == NULL || g_Inp32 == NULL) {
        g_hLib = NULL;
        return -1;
    }
    g_Port = PARPORT;
    if(!g_Port)
    	return -2;
    return 0;
}

void pp_release()
{
    if (!g_hLib)
        return;
    FreeLibrary(g_hLib);
    g_hLib = NULL;
}

int pp_out(short datum)
{
    if (!g_hLib)
        return -1;
    g_Out32(g_Port, datum);
    return 0;
}

#else /* not defined(WIN32) */

#define PARPORT ("/dev/parport0")

#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <linux/ppdev.h>

int g_ppfd = -1;

int pp_init()
{
    g_ppfd = open(PARPORT, O_RDWR);
    if (g_ppfd == -1)
        return -1;
    if (ioctl(g_ppfd, PPCLAIM)) {
        close(g_ppfd);
        return -2;
    }
    return 0;
}

void pp_release()
{
    if (g_ppfd == -1)
        return;
    ioctl(g_ppfd, PPRELEASE);
    close(g_ppfd);
    g_ppfd = -1;
}

int pp_out(short datum)
{
    if (g_ppfd == -1)
        return -1;
    ioctl (g_ppfd, PPWDATA, &datum);
    return 0;
}

#endif /* defined(WIN32) */
