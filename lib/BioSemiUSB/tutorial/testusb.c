/*
 * testusb.c -- Test self-made USB device prototype applying FTDI's 
 *              FT245BM USB FIFO chip. 
 * Version: 0.5
 * 
 * Copyright (c) 06/2004 by Wolfgang Wieser
 * 
 * This file may be distributed and/or modified under the terms of the
 * GNU General Public License version 2 as published by the Free Software
 * Foundation. (See COPYING.GPL for details.)
 * 
 * This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
 * WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
 * 
 * 
 * USAGE: (As root)
 *   testusb [read|write|send|recv] [-v=vendor] [-d=device] [-b=baudrate]
 * where baudrate is 921600,460800,230400,115200,57600,38400,19200,9600,4800,
 *                   1200,600,300
 * In read/recv mode, default baud rate is 300 (slowest), in write/send mode, 
 * it is 921600 (fastest). 
 * Reading will read chunks of length 32 byte and dump them in hex. 
 * Writing will write 4096 byte chunks of 0x0f-0xf0-0x0f-0xf0-...
 * Send and Recv is the same as read and write but with bitbang mode 
 * disabled, hence you need to use the handshake signals. Otherwise, sending 
 * will stop with timeout and receiving will continuously read chunks of 
 * length 0. 
 * Note: testusb will run until an error occurs or it is interrupted by 
 *       SIGINT (normally ^C). 
 */

#include "ftdi.h"
#include <string.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/time.h>
#include <time.h>

// gcc -O testusb.c -o testusb .libs/libftdi.a -I. -I.. -I../../libusb-0.1.7 -W -Wall -Wformat ../../libusb-0.1.7/.libs/libusb.a

static void Error(const char *where,int rv,struct ftdi_context *ctx,int doclose)
{
	if(rv)
	{
		fprintf(stderr,"%s: rv=%d, error=%s, errno=%s (%d)\n",
			where,rv,ctx->error_str,strerror(errno),errno);
		if(doclose)
		{
			rv=ftdi_usb_close(ctx);
			fprintf(stderr,"close: rv=%d, error=%s, errno=%s (%d)\n",
				rv,ctx->error_str,strerror(errno),errno);
		}
		ftdi_deinit(ctx);
		exit(1);
	}
	else
		fprintf(stderr,"%s: OK\n",where);
}


volatile int intr=0;
static void caught_signal(int dummy)
{  ++intr;  }


int InstallSignalHandler(int sig,void (*shandler)(int),int sa_flags)
{
	struct sigaction act;
	memset(&act,0,sizeof(act));
	sigemptyset(&act.sa_mask);
	act.sa_handler=shandler;
	act.sa_flags=sa_flags;
	
	return(sigaction(sig,&act,NULL));
}


long msec_elapsed(const struct timeval *old,const struct timeval *current)
{
	struct timeval _curr;
	if(!current)
	{
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

static void PrintUsage()
{
	fprintf(stderr,
		"usage: testusb [read|write|send|recv] [-b=baudrate] "
		"[-v=vendor] [-d=device]\n");
	exit(1);
}

int main(int argc,char **arg)
{
	struct ftdi_context ctx;
	int nwrite=0,nread=0,rv,i;
	char *opmode=NULL;
	int baudrate=-1;
	int iomode=+1;
	int device=0x1979,vendor=0x1305;
	
	for(i=1; i<argc; i++)
	{
		if(!strncmp(arg[i],"-b=",3))  baudrate=atoi(arg[i]+3);
		else if(!strncmp(arg[i],"-v=",3))
			vendor=strtol(arg[i]+3,NULL,16);
		else if(!strncmp(arg[i],"-d=",3))
			device=strtol(arg[i]+3,NULL,16);
		else if(*arg[i]!='-' && !opmode)  opmode=arg[i];
		else PrintUsage();
	}
	
	if(opmode)
	{
		if(!strcmp(opmode,"read"))  iomode=-1;
		else if(!strcmp(opmode,"write"))  iomode=+1;
		else if(!strcmp(opmode,"send"))  iomode=+2;
		else if(!strcmp(opmode,"recv"))  iomode=-2;
		else PrintUsage();
	}
	if(baudrate<0)
		baudrate=iomode<0 ? 300 : 921600;
	
	rv=ftdi_init(&ctx);
	Error("init",rv,&ctx,0);
	
	rv=ftdi_usb_open(&ctx,vendor,device);
	Error("open",rv,&ctx,0);
	
	rv=ftdi_usb_reset(&ctx);
	Error("reset",rv,&ctx,1);
	
	if(iomode==1 || iomode==-1)
	{
		rv=ftdi_enable_bitbang(&ctx,0xff);
		Error("bitbang(on)",rv,&ctx,1);
		baudrate/=4;
	}
	else
	{
		rv=ftdi_disable_bitbang(&ctx);
		Error("bitbang(off)",rv,&ctx,1);
	}
	
	/* 921600/4 -> max 500kb/sec */
	/* 3000000/4 -> max 800kb/sec (requires patched libftdi) */
	rv=ftdi_set_baudrate(&ctx,baudrate);  
	Error("baudrate",rv,&ctx,1);
	
	//rv=ftdi_set_latency_timer(&ctx,1);
	//Error("latency",rv,&ctx);
	
	InstallSignalHandler(SIGINT,&caught_signal,SA_RESTART);
	
	if(iomode>0)
	{
		struct timeval tv;
		const int bufsize=iomode>1 ? 4096 : 4096;
		char buf[bufsize];
		for(i=0; i<bufsize; i++) /* *((unsigned char*)buf+i)=i%2 ? 0x0f : 0xf0; */
			*((unsigned char*)buf+i)=i%256;
		
		gettimeofday(&tv,NULL);
/*		while(!intr)*/
		{
			rv=ftdi_write_data(&ctx,buf,bufsize);
			if(rv>0)  fprintf(stderr,".");
			else Error("write",rv,&ctx,1);
			nwrite+=bufsize;
		}
		if(intr)
		{  fprintf(stderr,"[interrupt]\nwritten: %s\n",
			ThroughputStr(nwrite,&tv));  }
	}
	else if(iomode<0)
	{
		struct timeval tv;
		const int bufsize=32;
		unsigned char buf[bufsize];
		
		gettimeofday(&tv,NULL);
		while(!intr)
		{
			rv=ftdi_read_data(&ctx,buf,bufsize);
			if(rv<0) Error("read",rv,&ctx,1);
			else
			{
				printf("%3d: ",rv);
				for(i=0; i<rv; i++)
					printf("%02x%s",buf[i],
						i%8==7 ? i%16==15 ? "\n     " : "  " : " ");
			}
			printf("\n"); fflush(stdout);
			nread+=rv;
		}
		if(intr)
		{  fprintf(stderr,"[interrupt]\nread: %s\n",
			ThroughputStr(nread,&tv));  }
	}
	
	rv=ftdi_usb_close(&ctx);
	Error("close",rv,&ctx,0);
	
	ftdi_deinit(&ctx);
	return(0);
}


/*******************************************************************************
 NOTE: In case you are using libftdi-0.3, you may consider applying the 
       following patch. It corrects one silly programming mistake and adds 
       support for faster baud rates. 
*******************************************************************************/
#if 0
diff -urN orig/libftdi-0.3/ftdi/ftdi.c libftdi-0.3/ftdi/ftdi.c
--- orig/libftdi-0.3/ftdi/ftdi.c	2004-03-25 22:42:07.000000000 +0100
+++ libftdi-0.3/ftdi/ftdi.c	2004-05-20 14:33:58.000000000 +0200
@@ -205,7 +205,25 @@
     case 921600:
         ftdi_baudrate = 0x8003;
         break;
-    default:
+	case 300000:
+		ftdi_baudrate = 0x000a;
+        break;
+	case 500000:
+		ftdi_baudrate = 0x0006;
+        break;
+	case 1000000:
+		ftdi_baudrate = 0x0003;
+        break;
+	case 1500000:
+		ftdi_baudrate = 0x0002;
+        break;
+ 	case 2000000:
+		ftdi_baudrate = 0x0001;
+        break;
+	case 3000000:
+		ftdi_baudrate = 0x0000;
+        break;
+   default:
         ftdi->error_str = "Unknown baudrate. Note: bitbang baudrates are automatically multiplied by 4";
         return -1;
     }
@@ -423,8 +441,8 @@
 
 
 void ftdi_eeprom_initdefaults(struct ftdi_eeprom *eeprom) {
-    eeprom->vendor_id = 0403;
-    eeprom->product_id = 6001;
+    eeprom->vendor_id = 0x0403;
+    eeprom->product_id = 0x6001;
     
     eeprom->self_powered = 1;
     eeprom->remote_wakeup = 1;
#endif
