#include <stdio.h>

#define MAX_SIZE 100
#define BUFFER_SIZE 256

int helper_func(int x)
{
    return x * 2;
}

int another_func(int a)
{
    printf("Value: %d\n", a);
    return a + 1;
}

int main_func(int n)
{
    int result = helper_func(n);
    result = another_func(result);
    printf("Result: %d\n", result);
    return result;
}
