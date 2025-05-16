#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#define V 6

void addEdge(int adj[][V], int u, int v) {
    adj[u][v] = 1;
}

bool KahnTopologicalSort(int adj[][V]) {
    int inDegree[V] = {0};
    int stack[V], top = 0;


    for (int i = 0; i < V; i++) {
        for (int j = 0; j < V; j++) {
            if (adj[j][i] == 1) {
                inDegree[i]++;
            }
        }
    }

    for (int i = 0; i < V; i++) {
        if (inDegree[i] == 0) {
            stack[top++] = i;
        }
    }

    int visited = 0;
    while (top > 0) {
        int u = stack[--top];
        printf("%d ", u);
        visited++;


        for (int v = 0; v < V; v++) {
            if (adj[u][v] == 1) {
                inDegree[v]--;
                if (inDegree[v] == 0) {
                    stack[top++] = v;
                }
            }
        }
    }


    return visited == V;
}

int main() {
    int adj[V][V] = {0};


    addEdge(adj, 5, 2);
    addEdge(adj, 5, 0);
    addEdge(adj, 4, 0);
    addEdge(adj, 4, 1);
    addEdge(adj, 2, 3);
    addEdge(adj, 3, 1);

    printf("拓扑排序结果：\n");
    if (!KahnTopologicalSort(adj)) {
        printf("图中存在环！\n");
    }

    return 0;
}