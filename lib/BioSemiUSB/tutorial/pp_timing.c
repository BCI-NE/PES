#include <stdio.h>
#include <unistd.h>
#include <sys/io.h>
#include <sys/time.h>
#include <time.h>

static struct timeval t0;
static struct timeval t1;

int wait(unsigned long t) {
  unsigned long dt;
  gettimeofday(&t0, 0);
  do {
    gettimeofday(&t1, 0);
    dt = (t1.tv_sec - t0.tv_sec)*1000000 
      + (t1.tv_usec - t0.tv_usec);  
  } while (dt < t);
}

#define BASEPORT 0x378 /* lp1 */
#define RXFACTIVE (1) /* 1 active high, 0 active low */

int main(int argc, char *argv[])
{
  int timeout0, timeout1, j;
  if (argc > 1)
    timeout0 = timeout1 = strtol(argv[1], NULL, 10);
  if (argc > 2)
    timeout1 = strtol(argv[2], NULL, 10);
  if (timeout0 < 1)
    timeout0 = 1;
  if (timeout1 < 1)
    timeout1 = 1;
  if (ioperm(BASEPORT, 3, 1)) {perror("ioperm"); return 1;}
  printf("timeout0=%d timeout1=%d\n", timeout0, timeout1);
  while (1) {
    outb(0, BASEPORT);
    wait(timeout0);
    outb(255, BASEPORT);
    wait(timeout1);
  }
  if (ioperm(BASEPORT, 3, 0)) {perror("ioperm"); return 1;}
  return 0;
}
