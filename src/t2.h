#ifndef T2_H_
#define T2_H_

#include <stdio.h>

typedef struct {
	unsigned int channel;
	long long int time;
} t2_t;

typedef struct {
	int length;
	long long int left_index;
	long long int right_index;
	t2_t *queue;
} t2_queue_t;

int next_t2(FILE *in_stream, t2_t *record);
void print_t2(FILE *out_stream, t2_t *record);

t2_queue_t *allocate_t2_queue(int queue_length);
void free_t2_queue(t2_queue_t **queue);
t2_t get_queue_item_t2(t2_queue_t *queue, int index);


#endif
