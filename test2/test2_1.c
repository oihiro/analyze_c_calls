#include <stdio.h>

#define MULTIPLIER 2
#define OFFSET 100

int utility_func(int x)
{
    return x * MULTIPLIER;
}

int helper_func(int y)
{
    int temp = y + OFFSET;
    printf("Helper processing: %d\n", temp);
    return temp;
}

int internal_helper(int z)
{
    return z / 2;
}
