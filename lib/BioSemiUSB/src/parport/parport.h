#ifndef PARPORT_H
#define PARPORT_H

int pp_init();
void pp_release();
int pp_out(short datum);

#endif
