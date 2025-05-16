#include <stdio.h>
#include <limits.h>

#define V 4

void floydWarshall(int graph[V][V]) {
    int dist[V][V], i, j, k;


    for (i = 0; i < V; i++) {
        for (j = 0; j < V; j++) {
            if (i == j) {
                dist[i][j] = 0;
            } else if (graph[i][j] != 0) {
                dist[i][j] = graph[i][j];
            } else {
                dist[i][j] = INT_MAX;
            }
        }
    }


    for (k = 0; k < V; k++) {
        for (i = 0; i < V; i++) {
            for (j = 0; j < V; j++) {
                if (dist[i][k] != INT_MAX && dist[k][j] != INT_MAX && dist[i][k] + dist[k][j] < dist[i][j]) {
                    dist[i][j] = dist[i][k] + dist[k][j];
                }
            }
        }
    }


    printf("最短路径矩阵：\n");
    for (i = 0; i < V; i++) {
        for (j = 0; j < V; j++) {
            if (dist[i][j] == INT_MAX) {
                printf("INF ");
            } else {
                printf("%d ", dist[i][j]);
            }
        }
        printf("\n");
    }
}

int main() {
    int graph[V][V] = {
        {0, 3, 0, 5},
        {3, 0, 8, 0},
        {0, 8, 0, 2},
        {5, 0, 2, 0}
    };

    floydWarshall(graph);
    return 0;
}