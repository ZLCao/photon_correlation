#ifndef OPTIONS_H_
#define OPTIONS_H_

#define QUEUE_SIZE 1024*1024

#include <stdio.h>
#include "types.h"

#include "limits.h"

typedef struct {
	char short_char;
	char long_char[10];
	char long_name[20];
	char description[1000];
} pc_option_t;

typedef struct {
	char message[10000];
	int options[100];
} program_options_t;

typedef struct {
	program_options_t *program_options;
	char string[1024];

	int usage;
	int verbose;
	int version;

	char *filename_in;
	char *filename_out;

	char *mode_string;
	int mode;

	int channels;
	int order;

	int print_every;

	int use_void;
	int seed;

/* Correlate */
	unsigned long long queue_size;
	unsigned long long max_time_distance;
	unsigned long long min_time_distance;
	unsigned long long max_pulse_distance;
	unsigned long long min_pulse_distance;
	int positive_only;
	int start_stop;

/* Intensity */
	unsigned long long bin_width;
	int count_all;
	int set_start_time;
	long long start_time;
	int set_stop_time;
	long long stop_time;

/* Histogram */
	char *time_string;
	limits_t time_limits;
	char *pulse_string;
	limits_t pulse_limits;
	
	char *time_scale_string;
	int time_scale;
	char *pulse_scale_string;
	int pulse_scale;

/* Channels */
	int suppress_channels;
	char *suppress_string;
	int *suppressed_channels;

	int offset_time;
	char *time_offsets_string;
	long long *time_offsets;

	int offset_pulse;
	char *pulse_offsets_string;
	long long *pulse_offsets;

/* correlate_vector */
	int approximate;
	int true_autocorrelation;

/* gn */
	int exact_normalization;

/* photons */
	double repetition_rate;
	char *convert_string;
	int convert;
} pc_options_t;

enum { OPT_HELP, OPT_VERSION,
		OPT_VERBOSE, OPT_PRINT_EVERY,
		OPT_FILE_IN, OPT_FILE_OUT,
		OPT_MODE, OPT_CHANNELS, OPT_ORDER,
		OPT_USE_VOID, OPT_SEED,
		OPT_QUEUE_SIZE, 
		OPT_START_TIME, OPT_STOP_TIME,
		OPT_MAX_TIME_DISTANCE, OPT_MIN_TIME_DISTANCE,
		OPT_MAX_PULSE_DISTANCE, OPT_MIN_PULSE_DISTANCE,
		OPT_POSITIVE_ONLY, OPT_START_STOP,
		OPT_BIN_WIDTH, OPT_COUNT_ALL,
		OPT_TIME, OPT_PULSE, OPT_TIME_SCALE, OPT_PULSE_SCALE,
		OPT_TIME_OFFSETS, OPT_PULSE_OFFSETS, 
		OPT_SUPPRESS,
		OPT_APPROXIMATE, OPT_TRUE_CORRELATION,
		OPT_EXACT_NORMALIZATION, 
		OPT_REPETITION_TIME,
		OPT_CONVERT,
		OPT_EOF };

pc_options_t *pc_options_alloc(void);
void pc_options_init(pc_options_t *options,
		program_options_t *program_options);
void pc_options_free(pc_options_t **options);

void pc_options_default(pc_options_t *options);
int pc_options_valid(pc_options_t const *options);
int pc_options_parse(pc_options_t *options, 
		int const argc, char * const *argv);

int pc_options_parse_mode(pc_options_t *options);
int pc_options_parse_time_scale(pc_options_t *options);
int pc_options_parse_pulse_scale(pc_options_t *options);
int pc_options_parse_time_limits(pc_options_t *options);
int pc_options_parse_pulse_limits(pc_options_t *options);
int pc_options_parse_suppress(pc_options_t *options);
int pc_options_parse_time_offsets(pc_options_t *options);
int pc_options_parse_pulse_offsets(pc_options_t *options);
int pc_options_parse_convert(pc_options_t *options);

void pc_options_usage(pc_options_t const *options, 
		int const argc, char * const *argv);
void pc_options_version(pc_options_t const *options,
		int const argc, char * const *argv);

char const* pc_options_string(pc_options_t const *options);
void pc_options_make_string(pc_options_t *options);
int pc_options_has_option(pc_options_t const *options, int const option);

int offsets_parse(long long **offsets, char *offsets_string,
		int const channels);
int offsets_valid(long long const *offsets);

int suppress_parse(pc_options_t *options);
int suppress_valid(pc_options_t const *options);

#endif
