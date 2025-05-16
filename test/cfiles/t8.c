#include <stdio.h>

void countingSort(int arr[], int size) {
    int output[size];
    int max = arr[0];


    for (int i = 1; i < size; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }


    int count[max + 1];
    for (int i = 0; i <= max; i++) {
        count[i] = 0;
    }


    for (int i = 0; i < size; i++) {
        count[arr[i]]++;
    }

    ，使其包含实际位置
    for (int i = 1; i <= max; i++) {
        count[i] += count[i - 1];
    }


    for (int i = size - 1; i >= 0; i--) {
        output[count[arr[i]] - 1] = arr[i];
        count[arr[i]]--;
    }


    for (int i = 0; i < size; i++) {
        arr[i] = output[i];
    }
}

void printArray(int arr[], int size) {
    for (int i = 0; i < size; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
}

int main() {
    int arr[] = {4, 2, 2, 8, 3, 3, 1};
    int size = sizeof(arr) / sizeof(arr[0]);

    printf("原始数组：\n");
    printArray(arr, size);

    countingSort(arr, size);

    printf("排序后的数组：\n");
    printArray(arr, size);

    return 0;
}