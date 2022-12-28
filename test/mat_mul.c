#include <stdlib.h>
#include <stdio.h>
#include <sys/time.h>
#include <assert.h>
#define n 2048

double A[n][n];
double B[n][n];
double C[n][n];

float tdiff(struct timeval *start,
            struct timeval *end)
{
    return (end->tv_sec - start->tv_sec) +
           1e-6 * (end->tv_usec - start->tv_usec);
}

int main(int argc, const char *argv[])
{
	int i,j,ih,jh,kh,il,kl,jl;
    assert(argc == 2);
    int s = atoi(argv[1]);
    if (s < 1 || s > 2048)
	{
        printf("Invalid input values.\n");
        return -1;
    }
    for (i = 0; i < n; ++i)
    {
        for (j = 0; j < n; ++j)
        {
            A[i][j] = (double)rand() / (double)RAND_MAX;
            B[i][j] = (double)rand() / (double)RAND_MAX;
            C[i][j] = 0;
        }
    }
    struct timeval start, end;
    gettimeofday(&start, NULL);
    for (ih = 0; ih < n; ih += s)
        for (jh = 0; jh < n; jh += s)
            for (kh = 0; kh < n; kh += s)
                for (il = 0; il < s; ++il)
                    for (kl = 0; kl < s; ++kl)
                        for (jl = 0; jl < s; ++jl)
                            C[ih + il][jh + jl] += A[ih + il][kh + kl] * B[kh + kl][jh + jl];
    gettimeofday(&end, NULL);
    printf("%0.6f\n", tdiff(&start, &end));
    return 0;
}
