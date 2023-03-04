#ifndef BSUSB_H
#define BSUSB_H

#define PRODUCT (0x1979)
#define VENDOR (0x1305)

#ifdef WIN32
#ifdef MAKEDLL
#define DLL __declspec(dllexport)
#else /* not MAKEDLL */
#define DLL __declspec(dllimport)
#endif /* MAKEDLL */
#else /* not WIN32 */
#define DLL
#endif /* WIN32 */

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

typedef unsigned char BYTE;

DLL int bsusb_init();
DLL int bsusb_read_pins(BYTE *pins);
DLL int bsusb_sendctl(int requesttype, int request, int value, int index);
DLL int bsusb_sendb(BYTE _byte);
DLL int bsusb_senda(void *arr, int arrsize);
DLL int bsusb_close();

DLL int bsusb_multiple_find();
DLL int bsusb_multiple_init(int which_usb);
DLL int bsusb_multiple_read_pins(int which_usb,BYTE *pins);
DLL int bsusb_multiple_sendctl(int which_usb,int requesttype, int request, int value, int index);
DLL int bsusb_multiple_sendb(int which_usb,BYTE _byte);
DLL int bsusb_multiple_senda(int which_usb,void *arr, int arrsize);
DLL int bsusb_multiple_close(int which_usb);

#ifdef __cplusplus
}
#endif /* __cplusplus */
  
  
#endif /* BSUSB_H */
