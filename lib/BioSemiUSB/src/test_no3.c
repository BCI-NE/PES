#include <stdio.h>
#include <usb.h>
#include <errno.h>


#define VENDOR (0x1305)
#define PRODUCT (0x1979)

int error(int rv, char *text, usb_dev_handle *usbclose)
{
    fprintf(stderr, "%s\n", text);
    if (usbclose != NULL)
        usb_close(usbclose);
    return rv;
}

int main(int argc, char *argv[])
{
    struct usb_bus *bus;
    struct usb_device *dev;
    usb_dev_handle *devh;
    char string[256];
    int i;
    int vendor = VENDOR;
    int product = PRODUCT;

    usb_init();

    if (usb_find_busses() < 0)
        return error(-1, "usb_find_busses() failed", NULL);
    if (usb_find_devices() < 0)
        return error(-2, "usb_find_devices() failed", NULL);

    for (bus = usb_get_busses(); bus; bus = bus->next) {
        for (dev = bus->devices; dev; dev = dev->next) {
            if (dev->descriptor.idVendor == vendor
                    && dev->descriptor.idProduct == product) {
                devh = usb_open(dev);
                if (!devh)
                    return error(-4, "usb_open() failed", NULL);

                /* usb_fetch_and_parse_descriptors(devh); */

                if (usb_get_string_simple(devh, dev->descriptor.iSerialNumber, string, sizeof(string)) <= 0) {
                    if(errno == EPERM)
                        return error(-5, "cannot retrieve data, check your permissions", devh);
                    else
                        printf("unable to fetch serial number\n");
                } else
                    printf("serial number: %s\n", string);

                if (usb_get_string_simple(devh, dev->descriptor.iProduct, string, sizeof(string)) <= 0)
                    printf("unable to fetch product description\n");
                else
                    printf("product description: %s\n", string);

                printf("%d configurations\n", dev->descriptor.bNumConfigurations);
                for(i = 0; i < dev->descriptor.bNumConfigurations; ++i) {
                    printf("[%d]\tbLength = %d\n\tbDescriptorType = %d\n\twTotalLength = %d\n\tbNumInterfaces = %d\n\tbConfigurationValue = %d\n\tiConfiguration = %d\n\tbmAttributes = %d\n\tMaxPower = %d\n", i, dev->config[i].bLength, dev->config[i].bDescriptorType, dev->config[i].wTotalLength, dev->config[i].bNumInterfaces, dev->config[i].bConfigurationValue, dev->config[i].iConfiguration, dev->config[i].bmAttributes, dev->config[i].MaxPower);
                }

                if (usb_close(devh) != 0)
                    return error(-10, "unable to close device", NULL);

                return 0;
            }
        }
    }

    // device not found
    return error(-3, "device not found", NULL);
}
