#include <stdio.h>

#define MAX_SIZE 100
#define PRINT_DEBUG(x) printf("Debug: %d\n", x)

int level3_func(int x)
{
    return x + 10;
}

int level2_func(int x)
{
    int result = level3_func(x);
    PRINT_DEBUG(result);
    return result;
}

int level1_func(int x)
{
    int result = level2_func(x);
    return result * 2;
}

int main_func(int n)
{
    int result = level1_func(n);
    printf("Result: %d\n", result);
    return result;
}
