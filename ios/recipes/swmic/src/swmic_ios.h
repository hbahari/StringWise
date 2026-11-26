#ifndef SWMIC_IOS_H
#define SWMIC_IOS_H

/* Permission states returned by swmic_permission(). */
#define SWMIC_UNKNOWN 0
#define SWMIC_GRANTED 1
#define SWMIC_DENIED 2

int swmic_configure_session(void);
int swmic_permission(void);
void swmic_request_permission(void);
int swmic_start(double sample_rate);
void swmic_stop(void);
int swmic_read(float *out, int max_count);
double swmic_hardware_rate(void);
int swmic_dropped(void);

#endif
