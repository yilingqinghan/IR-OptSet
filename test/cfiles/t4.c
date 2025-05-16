#include <stdio.h>


int binarySearch(int arr[], int left, int right, int x) {
    while (left <= right) {
        int mid = left + (right - left) / 2;

         mid 是否是目标值
        if (arr[mid] == x) {
            return mid;
        }

         mid，忽略左半部分
        if (arr[mid] < x) {
            left = mid + 1;
        }
         mid，忽略右半部分
        else {
            right = mid - 1;
        }
    }

    ，返回 -1
    return -1;
}

int main() {
    int arr[] = {2, 3, 4, 10, 40};
    int n = sizeof(arr) / sizeof(arr[0]);
    int x = 10;
    int result = binarySearch(arr, 0, n - 1, x);

    if (result == -1) {
        printf("元素不在数组中\n");
    } else {
        printf("元素在数组中的索引是 %d\n", result);
    }

    return 0;
}