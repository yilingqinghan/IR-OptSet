#include <stdio.h>


void hanoi(int n, char from, char to, char aux) {
    if (n == 1) {
        printf("将盘子 1 从 %c 移动到 %c\n", from, to);
        return;
    }
    hanoi(n-1, from, aux, to);   n-1 个盘子从 from 移动到 aux
    printf("将盘子 %d 从 %c 移动到 %c\n", n, from, to);
    hanoi(n-1, aux, to, from);   n-1 个盘子从 aux 移动到 to
}

int main() {
    int n = 3;
    hanoi(n, 'A', 'C', 'B');   A 移动到 C，B 作为辅助柱
    return 0;
}