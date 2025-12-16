#include <stdio.h>

// test2_1.cで定義される関数
int utility_func(int x);
int helper_func(int y);

int process_data(int value)
{
    int result = utility_func(value);
    return result;
}

int main_test(int n)
{
    int step1 = process_data(n);
    int step2 = helper_func(step1);
    printf("Final result: %d\n", step2);
    return step2;
}
