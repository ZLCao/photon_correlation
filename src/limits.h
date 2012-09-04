#ifndef LIMITS_H_
#define LIMITS_H_

#define SCALE_UNKNOWN -1
#define SCALE_LINEAR 1
#define SCALE_LOG 2
#define SCALE_LOG_ZERO 3

typedef struct {
	long long lower;
	long long upper;
} window_t;

typedef struct {
	double lower;
	int bins;
	double upper;
} limits_t;

int str_to_limits(char *str, limits_t *limits);
int scale_parse(char *str, int *scale);

#endif
