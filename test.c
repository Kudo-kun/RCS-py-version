# include <stdio.h>

int main()
{
    int a, b;
    scanf("%d%d", &a, &b);
    if((a > 1000) && (b > 1000))
        while(1);
    else if(a == b)
    {
        int* ptr = NULL;
        *ptr = 45;
    }
    printf("hello from C program %d\n", a+b);
    return 0;
}