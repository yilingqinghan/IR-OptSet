#include <stdio.h>
#include <string.h>

void swap(char* a, char* b) {
    char temp = *a;
    *a = *b;
    *b = temp;
}


void printPermutation(char str[], int l, int r) {
    if (l == r) {
        printf("%s\n", str);
    } else {
        for (int i = l; i <= r; i++) {
            swap(&str[l], &str[i]);
            printPermutation(str, l + 1, r);
            swap(&str[l], &str[i]);
        }
    }
}

int main() {
    char str[] = "ABC";
    int n = strlen(str);
    printf("所有排列：\n");
    printPermutation(str, 0, n - 1);
    return 0;
}